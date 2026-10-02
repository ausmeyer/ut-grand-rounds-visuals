#!/usr/bin/env Rscript
# Replay selected components of the frozen national 2022/23 draw ensemble.
suppressPackageStartupMessages({library(dplyr);library(jsonlite)})
args <- commandArgs(trailingOnly=TRUE)
stopifnot(length(args)==2)
project <- normalizePath(args[[1]]); root <- normalizePath(args[[2]])
out <- file.path(root,'data/slide-31')
config <- read_json(file.path(out,'design.json'),simplifyVector=TRUE)
for(p in names(config$source_pins)) stopifnot(digest::digest(file=file.path(root,p),algo='sha256')==config$source_pins[[p]])
base <- file.path(root,'data/slide-30/threshold-example')
manifest <- read_json(file.path(base,'early-model-manifest.json'),simplifyVector=TRUE)
stopifnot(digest::digest(file=manifest$model_path,algo='sha256')==manifest$model_sha256)
models <- readRDS(manifest$model_path)
prior <- fromJSON(gzfile(file.path(base,'early-draws.json.gz')))
seeds <- read_json(file.path(base,'extended-evaluation.json'),simplifyVector=TRUE)$early_seeds
n <- prior$n_draws; ids <- prior$scenarios$draw
stopifnot(n==config$evaluation_n_per_location, identical(ids,seq_len(n)))
setwd(project)
source('R/latent_curve_gam.R');source('R/decision_engine.R')
ve <- as_tibble(prior$scenarios$parameters) %>% mutate(draw=ids,age_group='all')
results <- list()
for(state_name in config$states) {
  k <- match(state_name,names(models)); obj <- models[[k]]
  grid <- make_prediction_grid(obj$data)
  model_matrix <- predict(obj$fit,newdata=grid,type='lpmatrix')
  rows <- which(as.character(grid$season)==config$season)
  weeks <- grid$mmwr_week[rows]
  stopifnot(length(weeks)==39L, all(weeks==c(36:52,1:22)))
  set.seed(seeds$posterior+k)
  coefficients <- MASS::mvrnorm(n,coef(obj$fit),obj$fit$Vp)
  posterior <- plogis(coefficients %*% t(model_matrix[rows,,drop=FALSE]))
  x <- outer(prior$scenarios$timing_shift_weeks,seq_along(weeks),function(shift,t)t-shift)
  x <- pmin(pmax(x,1),length(weeks));lo <- floor(x);hi <- pmin(lo+1L,length(weeks))
  r <- rep(ids,times=length(weeks))
  shifted <- matrix(posterior[cbind(r,as.vector(lo))]*as.vector(1-(x-lo))+
                    posterior[cbind(r,as.vector(hi))]*as.vector(x-lo),nrow=n)
  burden <- tibble(draw=rep(ids,each=length(weeks)),state=state_name,age_group='all',
                   season=config$season,week=rep(weeks,times=n),max_week=52L,
                   burden=as.vector(t(shifted)))
  utility <- evaluate_candidate_utilities(burden,ve,prior$candidate_weeks) %>%
    mutate(candidate_index=match(vaccination_week,prior$candidate_weeks)) %>%
    arrange(draw,candidate_index)
  results[[state_name]] <- list(name=state_name,posterior_seed=seeds$posterior+k,
                               weeks=weeks,max_week=52L,burden=shifted,
                               utility=matrix(utility$utility,nrow=n,byrow=TRUE))
  message('Extracted ',state_name,': ',n,' paired curves and ',n*length(prior$candidate_weeks),' utilities')
}
export <- list(design_sha256=digest::digest(file=file.path(out,'design.json'),algo='sha256'),
               model_sha256=manifest$model_sha256,n_draws=n,draw_ids=ids,
               candidate_weeks=prior$candidate_weeks,states=results,
               source_code=lapply(c('R/latent_curve_gam.R','R/decision_engine.R','R/protection_models.R','R/calendar.R'),
                 function(p)list(path=p,sha256=digest::digest(file=p,algo='sha256'))))
con <- gzfile(file.path(out,'states-draws.json.gz'),'wt')
writeLines(toJSON(export,auto_unbox=TRUE,digits=16),con);close(con)
