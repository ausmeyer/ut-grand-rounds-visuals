#!/usr/bin/env Rscript
suppressPackageStartupMessages({library(dplyr);library(readr);library(jsonlite)})
args <- commandArgs(trailingOnly=TRUE);stopifnot(length(args)==2)
project <- normalizePath(args[[1]]); root <- normalizePath(args[[2]])
out <- file.path(root,'data/august-baseline')
config <- read_json(file.path(out,'design.json'),simplifyVector=TRUE)
setwd(project);source('R/fluview_download.R')
raw_path <- 'data/raw/ilinet_state_raw.csv'
early_path <- file.path(root,'data/slide-30/threshold-example/ilinet-state-2022-23.csv')
aug_path <- file.path(out,'ilinet-august-2022.csv')
if(!file.exists(aug_path)) {
  august <- fluview_download_ilinet(region='state',years=2021) %>% filter(year==2022,week %in% config$baseline_weeks)
  stopifnot(all(config$baseline_weeks %in% august$week))
  write_csv(august,aug_path,na='NA')
}
raw <- read_csv(raw_path,show_col_types=FALSE) %>%
  filter(!(year==2022 & week>=32 | year==2023 & week<=22))
raw <- bind_rows(raw,read_csv(early_path,show_col_types=FALSE),read_csv(aug_path,show_col_types=FALSE))
population_path <- 'data/processed/state_population.csv'
population <- read_csv(population_path,show_col_types=FALSE)
sum_reported <- function(x) if(all(is.na(x))) NA_real_ else sum(x,na.rm=TRUE)
data <- raw %>%
  mutate(season_start_year=if_else(week>=32L,year,year-1L),state=if_else(region=='New York City','New York',region)) %>%
  filter(week>=32|week<=22,season_start_year %in% unlist(config$model_fit_seasons),state %in% population$state) %>%
  group_by(state,mmwr_year=year,mmwr_week=week,week_start,season_start_year) %>%
  summarise(ilitotal=sum_reported(ilitotal),total_patients=sum_reported(total_patients),.groups='drop') %>%
  mutate(season=sprintf('%d/%02d',season_start_year,(season_start_year+1)%%100),age_group='all')
stopifnot(n_distinct(data$state)==51,all(data$ilitotal>=0 & data$ilitotal<=data$total_patients,na.rm=TRUE))
coverage <- data %>% filter(season_start_year!=2010) %>% group_by(state,season) %>%
  summarise(baseline_rows=sum(mmwr_week %in% 32:35),baseline_valid=sum(mmwr_week %in% 32:35 & is.finite(total_patients) & total_patients>0 & is.finite(ilitotal)),.groups='drop')
stopifnot(all(coverage$baseline_rows==4),all(tapply(coverage$baseline_valid,coverage$state,sum)>0))
write_csv(data,file.path(out,'model-data.csv.gz'),na='NA')
write_csv(population,file.path(out,'state-population.csv'))
sources <- c(raw_path,early_path,aug_path,population_path,'R/fluview_download.R','R/latent_curve_gam.R','R/calendar.R','R/decision_engine.R','R/protection_models.R',file.path(root,'scripts/prepare_august_baseline.R'))
write_json(list(design_sha256=digest::digest(file=file.path(out,'design.json'),algo='sha256'),
                downloaded_august_source='https://gis.cdc.gov/flu2/PostPhase02DataDownload',
                retrieved_utc=format(Sys.time(),tz='UTC',usetz=TRUE),
                source_files=lapply(sources,function(p)list(path=p,sha256=digest::digest(file=p,algo='sha256'))),
                model_data_sha256=digest::digest(file=file.path(out,'model-data.csv.gz'),algo='sha256'),
                incomplete_baselines=filter(coverage,baseline_valid<4),
                rows=nrow(data),seasons=sort(unique(data$season))),
           file.path(out,'data-provenance.json'),auto_unbox=TRUE,pretty=TRUE)
message('Prepared August-inclusive data: ',nrow(data),' state-weeks; incomplete baseline cells: ',sum(coverage$baseline_valid<4))
