#!/usr/bin/env Rscript
# Fit the additional 2022/23 benchmark only in the slide workspace.
suppressPackageStartupMessages({library(dplyr); library(readr); library(jsonlite)})
args <- commandArgs(trailingOnly=TRUE)
stopifnot(length(args)==2)
project <- normalizePath(args[[1]]); out <- normalizePath(args[[2]])
setwd(project)
source('R/latent_curve_gam.R')
early_source <- file.path(out,'ilinet-state-2022-23.csv')
raw <- read_csv(early_source,show_col_types=FALSE)
population <- read_csv('data/processed/state_population.csv',show_col_types=FALSE)
sum_reported <- function(x) if(all(is.na(x))) NA_real_ else sum(x,na.rm=TRUE)
early <- raw %>%
  mutate(season_start_year=if_else(week>=36L,year,year-1L),
         state=if_else(region=='New York City','New York',region)) %>%
  filter(season_start_year==2022,week>=36|week<=22,state %in% population$state) %>%
  group_by(state,mmwr_year=year,mmwr_week=week,week_start) %>%
  summarise(ilitotal=sum_reported(ilitotal),total_patients=sum_reported(total_patients),
            num_providers=sum_reported(num_of_providers),.groups='drop') %>%
  mutate(season='2022/23',season_start_year=2022L,age_group='all')
stopifnot(nrow(early)==51*39, !any(xor(is.na(early$ilitotal),is.na(early$total_patients))),
          all(early$ilitotal>=0 & early$ilitotal<=early$total_patients,na.rm=TRUE))
early <- early %>% mutate(ilitotal=if_else(total_patients>0,ilitotal,NA_real_),
                          total_patients=if_else(total_patients>0,total_patients,NA_real_))
pre <- read_csv('data/processed/ilinet_state_all_age_primary_seasons.csv',show_col_types=FALSE) %>%
  filter(season_start_year<=2018)
data <- prepare_all_age_gam_data(bind_rows(pre,early))
cache <- file.path(out,'cache')
dir.create(cache,showWarnings=FALSE)
models <- list()
for(state_name in sort(unique(as.character(data$state)))) {
  model <- fit_statewise_latent_gams(filter(data,state==state_name),
             family='quasibinomial',global_k=14L,season_k=12L,gamma=1)
  stopifnot(isTRUE(model[[1]]$fit$converged), all(is.finite(coef(model[[1]]$fit))))
  models[[state_name]] <- model[[1]]
  message('2022 benchmark: fitted ',length(models),'/51 states (',state_name,')')
}
p <- file.path(cache,'gam-pre-plus-2022.rds');saveRDS(models,p)
sources <- c(early_source,'data/processed/ilinet_state_all_age_primary_seasons.csv',
             'R/latent_curve_gam.R','R/calendar.R')
manifest <- list(model_path=p,model_sha256=digest::digest(file=p,algo='sha256'),
                 source_files=lapply(sources,function(p)list(path=p,sha256=digest::digest(file=p,algo='sha256'))),
                 fitting_seasons=sort(unique(as.character(data$season))),
                 early_missing_rows=sum(is.na(early$total_patients)),
                 model='Statewise quasibinomial GAM, global k14, season k12, gamma1, REML',
                 outer_convergence=as.list(table(vapply(models,function(m)m$fit$outer.info$conv,character(1)))),
                 warning_note='The original global plus seasonal smooth formula produces mgcv repeated-1d-smooth warnings; verify convergence and covariance.',
                 R_version=R.version.string,mgcv_version=as.character(packageVersion('mgcv')))
write_json(manifest,file.path(out,'early-model-manifest.json'),pretty=TRUE,auto_unbox=TRUE)
message('Saved separate 2022 benchmark; manuscript files untouched.')
