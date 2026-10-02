#!/usr/bin/env Rscript
suppressPackageStartupMessages({library(dplyr);library(readr);library(jsonlite)})
args <- commandArgs(trailingOnly=TRUE);stopifnot(length(args)==3,args[[3]] %in% c('training','early','expanded'))
project <- normalizePath(args[[1]]);root <- normalizePath(args[[2]]);mode <- args[[3]]
out <- file.path(root,'data/august-baseline');config <- read_json(file.path(out,'design.json'),simplifyVector=TRUE)
if(mode!='training') stopifnot(file.exists(file.path(out,'threshold-fit.json')))
provenance <- read_json(file.path(out,'data-provenance.json'),simplifyVector=TRUE)
stopifnot(provenance$design_sha256==digest::digest(file=file.path(out,'design.json'),algo='sha256'),
          provenance$model_data_sha256==digest::digest(file=file.path(out,'model-data.csv.gz'),algo='sha256'))
setwd(project);source('R/latent_curve_gam.R')
data <- read_csv(file.path(out,'model-data.csv.gz'),show_col_types=FALSE) %>%
  filter(season_start_year %in% config$model_fit_seasons[[mode]]) %>%
  group_by(season) %>% mutate(max_week=if_else(any(mmwr_week==53L),53L,52L)) %>% ungroup() %>%
  mutate(state=factor(state),season=factor(season),
         season_pos=week_to_season_index(mmwr_week,start_week=32L,max_week=max_week),
         ili_cases=pmax(round(ilitotal),0),non_ili_cases=pmax(round(total_patients-ilitotal),0),
         has_observed_denominator=is.finite(total_patients)&total_patients>0&is.finite(ilitotal)&ilitotal>=0&ilitotal<=total_patients,
         total_patients_model=if_else(has_observed_denominator,pmax(round(total_patients),1),0),
         ili_prop=if_else(has_observed_denominator,pmin(pmax(ili_cases/total_patients_model,0),1),NA_real_),
         model_ili_prop=coalesce(ili_prop,0))
if(mode=='training') stopifnot(all(data$season_start_year<=2018))
states <- sort(unique(as.character(data$state)))
models <- parallel::mclapply(states,function(state_name) {
  model <- fit_statewise_latent_gams(filter(data,state==state_name),family='quasibinomial',global_k=14L,season_k=12L,gamma=1)[[1]]
  stopifnot(isTRUE(model$fit$converged),model$fit$outer.info$conv=='full convergence',
            all(is.finite(coef(model$fit))),min(eigen(model$fit$Vp,symmetric=TRUE,only.values=TRUE)$values)>0)
  message(mode,': fitted ',state_name)
  model
},mc.cores=4,mc.preschedule=FALSE)
names(models) <- states
stopifnot(length(models)==51,!any(vapply(models,inherits,logical(1),'try-error')))
dir.create(file.path(out,'cache'),showWarnings=FALSE)
path <- file.path(out,'cache',paste0(mode,'.rds'));saveRDS(models,path)
write_json(list(mode=mode,design_sha256=provenance$design_sha256,model_data_sha256=provenance$model_data_sha256,
                model_sha256=digest::digest(file=path,algo='sha256'),fitting_seasons=sort(unique(as.character(data$season))),
                all_51_converged=TRUE,all_covariances_positive_definite=TRUE,
                fit_script_sha256=digest::digest(file=file.path(root,'scripts/fit_august_baseline.R'),algo='sha256'),
                R_version=R.version.string,mgcv_version=as.character(packageVersion('mgcv'))),
           file.path(out,paste0(mode,'-model-manifest.json')),auto_unbox=TRUE,pretty=TRUE)
message('Saved ',mode,' August-inclusive models.')
