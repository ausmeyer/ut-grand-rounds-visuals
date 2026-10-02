#!/usr/bin/env Rscript
# Replay the saved season/VE pairs against the separate August-inclusive fits.
suppressPackageStartupMessages({library(dplyr);library(jsonlite);library(readr)})
args <- commandArgs(trailingOnly=TRUE)
stopifnot(length(args)==3,args[[3]] %in% c('training','early','expanded'))
project <- normalizePath(args[[1]]);root <- normalizePath(args[[2]]);mode <- args[[3]]
out <- file.path(root,'data/august-baseline')
sha <- function(path) digest::digest(file=path,algo='sha256')
config <- read_json(file.path(out,'design.json'),simplifyVector=TRUE)
if(mode!='training') stopifnot(file.exists(file.path(out,'threshold-fit.json')))
manifest <- read_json(file.path(out,paste0(mode,'-model-manifest.json')),simplifyVector=TRUE)
model_path <- file.path(out,'cache',paste0(mode,'.rds'))
stopifnot(manifest$design_sha256==sha(file.path(out,'design.json')),manifest$model_sha256==sha(model_path))
pin <- config$paired_inputs[[mode]];prior_path <- file.path(root,pin$path)
stopifnot(sha(prior_path)==pin$sha256)
prior <- fromJSON(gzfile(prior_path));pairs <- prior$scenarios;n <- config$n_draws
stopifnot(prior$n_draws==n,identical(pairs$draw,seq_len(n)),
          all(as.integer(substr(pairs$parameters$ve_source_season,1,4))<=2018))
models <- readRDS(model_path)
population <- read_csv(file.path(out,'state-population.csv'),show_col_types=FALSE)
weights <- population$population[match(names(models),population$state)]
stopifnot(length(models)==51,all(is.finite(weights)),all(weights>0))
weights <- weights/sum(weights)
setwd(project);source('R/latent_curve_gam.R');source('R/decision_engine.R')
seasons <- sort(unique(pairs$season))
stopifnot(identical(as.integer(substr(seasons,1,4)),as.integer(config[[paste0(mode,'_seasons')]])))
groups <- setNames(lapply(seasons,function(s)which(pairs$season==s)),seasons)
national <- season_weeks <- states <- list()
for(k in seq_along(models)) {
  obj <- models[[k]];grid <- make_prediction_grid(obj$data)
  if(mode=='training') stopifnot(all(as.integer(substr(as.character(grid$season),1,4))<=2018))
  design <- predict(obj$fit,newdata=grid,type='lpmatrix')
  set.seed(config$seeds[[mode]]$posterior+k)
  coefficients <- MASS::mvrnorm(n,coef(obj$fit),obj$fit$Vp)
  for(s in seasons) {
    ids <- groups[[s]];rows <- which(as.character(grid$season)==s);weeks <- as.integer(grid$mmwr_week[rows])
    max_week <- if(53L %in% weeks)53L else 52L
    stopifnot(identical(weeks,c(32L:max_week,1L:22L)))
    if(k==1L) {season_weeks[[s]] <- weeks;national[[s]] <- matrix(0,length(ids),length(weeks))}
    stopifnot(identical(weeks,season_weeks[[s]]))
    posterior <- plogis(coefficients[ids,,drop=FALSE] %*% t(design[rows,,drop=FALSE]))
    x <- outer(pairs$timing_shift_weeks[ids],seq_along(weeks),function(shift,t)t-shift)
    x <- pmin(pmax(x,1),length(weeks));lo <- floor(x);hi <- pmin(lo+1L,length(weeks))
    r <- rep(seq_along(ids),times=length(weeks))
    shifted <- matrix(posterior[cbind(r,as.vector(lo))]*as.vector(1-(x-lo))+
                      posterior[cbind(r,as.vector(hi))]*as.vector(x-lo),nrow=length(ids))
    national[[s]] <- national[[s]]+shifted*weights[[k]]
    if(mode=='early' && names(models)[[k]] %in% config$states) {
      stopifnot(identical(ids,seq_len(n)))
      states[[names(models)[[k]]]] <- list(name=names(models)[[k]],posterior_seed=config$seeds[[mode]]$posterior+k,
                                         weeks=weeks,max_week=max_week,burden=shifted)
    }
  }
  if(k%%10L==0L || k==51L) message(mode,': sampled ',k,'/51 August-inclusive fits')
}
ve <- as_tibble(pairs$parameters) %>% mutate(draw=pairs$draw,age_group='all')
burden_table <- function(matrix,weeks,ids,state,season) {
  tibble(draw=rep(ids,each=length(weeks)),state=state,age_group='all',season=season,
         week=rep(weeks,times=length(ids)),max_week=if(53L %in% weeks)53L else 52L,
         burden=as.vector(t(matrix)))
}
utilities <- function(burden) {
  values <- evaluate_candidate_utilities(burden,ve,config$candidate_weeks) %>%
    mutate(candidate_index=match(vaccination_week,config$candidate_weeks)) %>% arrange(draw,candidate_index)
  stopifnot(nrow(values)==n*length(config$candidate_weeks))
  matrix(values$utility,nrow=n,byrow=TRUE)
}
national_burden <- bind_rows(lapply(seasons,function(s)burden_table(national[[s]],season_weeks[[s]],groups[[s]],'US',s)))
national_utility <- utilities(national_burden)
examples <- vector('list',n)
for(s in seasons) for(j in seq_along(groups[[s]])) {
  id <- groups[[s]][[j]];weeks <- season_weeks[[s]]
  examples[[id]] <- list(draw=id,season=s,weeks=weeks,max_week=if(53L %in% weeks)53L else 52L,
                         burden=national[[s]][j,],timing_shift_weeks=pairs$timing_shift_weeks[[id]],
                         parameters=as.list(pairs$parameters[id,]),utility=national_utility[id,])
}
export <- list(mode=mode,n_draws=n,candidate_weeks=config$candidate_weeks,
               season_counts=as.list(table(pairs$season)),scenarios=examples,
               design_sha256=sha(file.path(out,'design.json')),model_sha256=manifest$model_sha256,
               model_manifest_sha256=sha(file.path(out,paste0(mode,'-model-manifest.json'))),
               prior_pairs_sha256=pin$sha256,
               extraction_script_sha256=sha(file.path(root,'scripts/extract_august_baseline.R')))
if(mode!='training') export$threshold_fit_sha256 <- sha(file.path(out,'threshold-fit.json'))
save_json <- function(value,name) {
  con <- gzfile(file.path(out,name),'wt');writeLines(toJSON(value,auto_unbox=TRUE,digits=16),con);close(con)
}
save_json(export,paste0(mode,'-draws.json.gz'))
if(mode=='early') {
  states <- states[config$states]
  for(name in names(states)) {
    state <- states[[name]]
    states[[name]]$utility <- utilities(burden_table(state$burden,state$weeks,seq_len(n),name,seasons[[1]]))
  }
  save_json(list(design_sha256=export$design_sha256,model_sha256=export$model_sha256,
                 national_draws_sha256=sha(file.path(out,'early-draws.json.gz')),
                 threshold_fit_sha256=export$threshold_fit_sha256,n_draws=n,draw_ids=seq_len(n),
                 candidate_weeks=config$candidate_weeks,states=states),'states-draws.json.gz')
}
message('Saved ',n,' ',mode,' pairs; prior VE parameters, season assignments, and timing shifts preserved.')
