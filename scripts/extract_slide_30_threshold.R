#!/usr/bin/env Rscript
# Read the manuscript caches; write only to the slide's separate output folder.
suppressPackageStartupMessages({
  library(dplyr)
  library(jsonlite)
  library(readr)
})
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 3L, args[[3]] %in% c("training", "evaluation", "expanded", "early"))
project <- normalizePath(args[[1]])
out <- normalizePath(args[[2]])
mode <- args[[3]]
config <- read_json(file.path(out, "design.json"), simplifyVector = TRUE)
design_path <- file.path(out,"design.json")
if (mode %in% c("expanded","early")) {
  design_path <- file.path(out,"extended-evaluation.json")
  config <- c(config, read_json(design_path, simplifyVector=TRUE))
}
if (mode != "training") stopifnot(file.exists(file.path(out, "threshold-fit.json")))
setwd(project)
source("R/latent_curve_gam.R")
source("R/decision_engine.R")
source("R/ve_draws_from_estimates.R")
manifest_path <- if (mode == "training") {
  "outputs/sensitivity/gam_precovid_primary/tables/gam_precovid_primary_analysis_manifest.json"
} else "outputs/primary/tables/gam_primary_analysis_manifest.json"
manifest <- read_json(manifest_path, simplifyVector = TRUE)
stopifnot(all(unname(tools::md5sum(manifest$inputs$path)) == manifest$inputs$md5))
if (mode == "early") {
  extra <- read_json(file.path(out,"early-model-manifest.json"),simplifyVector=TRUE)
  stopifnot(digest::digest(file=extra$model_path,algo="sha256")==extra$model_sha256)
  models <- readRDS(extra$model_path)
} else models <- readRDS(manifest$model_path)
population <- read_csv("data/processed/state_population.csv", show_col_types = FALSE)
weights <- population$population[match(names(models), population$state)]
stopifnot(length(models) == 51L, all(is.finite(weights)), all(weights > 0))
weights <- weights / sum(weights)
n <- config[[paste0(mode, "_draws")]]
years <- config[[paste0(mode, "_season_start_years")]]
seeds <- config[[paste0(mode, "_seeds")]]
seasons <- available_decision_seasons(models, complete_only = TRUE)
seasons <- seasons[as.integer(substr(seasons, 1, 4)) %in% years]
stopifnot(identical(sort(as.integer(substr(seasons, 1, 4))), as.integer(years)))
if (mode == "training") {
  stopifnot(all(vapply(models, function(obj) {
    all(as.integer(substr(as.character(obj$data$season), 1, 4)) <= 2018)
  }, logical(1))))
}
set.seed(seeds$season)
scenarios <- tibble(draw = seq_len(n), sampled_season = sample(seasons, n, replace = TRUE),
                    timing_shift_weeks = rnorm(n, 0, .75))
groups <- lapply(seasons, function(s) which(scenarios$sampled_season == s))
names(groups) <- seasons
national <- season_weeks <- list()
for (k in seq_along(models)) {
  obj <- models[[k]]
  grid <- make_prediction_grid(obj$data)
  design <- stats::predict(obj$fit, newdata = grid, type = "lpmatrix")
  set.seed(seeds$posterior + k)
  coefficients <- MASS::mvrnorm(n, stats::coef(obj$fit), obj$fit$Vp)
  for (s in seasons) {
    ids <- groups[[s]]
    rows <- which(as.character(grid$season) == s)
    weeks <- grid$mmwr_week[rows]
    stopifnot(all(config$baseline_weeks %in% weeks))
    max_week <- if (53L %in% weeks) 53L else 52L
    pos <- week_to_season_index(weeks, start_week = 36L, max_week = max_week)
    stopifnot(length(ids) > 0L, all(diff(pos) == 1L))
    if (k == 1L) {
      season_weeks[[s]] <- weeks
      national[[s]] <- matrix(0, length(ids), length(weeks))
    }
    stopifnot(identical(weeks, season_weeks[[s]]))
    posterior <- plogis(coefficients[ids, , drop = FALSE] %*% t(design[rows, , drop = FALSE]))
    x <- outer(scenarios$timing_shift_weeks[ids], seq_along(pos), function(shift, t) t - shift)
    x <- pmin(pmax(x, 1), length(pos))
    lo <- floor(x)
    hi <- pmin(lo + 1L, length(pos))
    r <- rep(seq_along(ids), times = length(pos))
    shifted <- matrix(posterior[cbind(r, as.vector(lo))] * as.vector(1 - (x - lo)) +
                      posterior[cbind(r, as.vector(hi))] * as.vector(x - lo),
                      nrow = length(ids))
    national[[s]] <- national[[s]] + shifted * weights[[k]]
  }
  if (k %% 10L == 0L || k == length(models)) message(mode, ": sampled ", k, "/51 cached states")
}
burden <- bind_rows(lapply(seasons, function(s) {
  ids <- groups[[s]]
  weeks <- season_weeks[[s]]
  tibble(draw = rep(ids, each = length(weeks)), state = "US", age_group = "all",
         season = s, week = rep(weeks, times = length(ids)),
         max_week = if (53L %in% weeks) 53L else 52L,
         burden = as.vector(t(national[[s]])))
}))
estimates <- read_csv("data/processed/cdc_ve_estimates.csv", show_col_types = FALSE) %>%
  filter(as.integer(substr(.data$season, 1, 4)) %in% config$ve_source_season_start_years)
ve <- draw_primary_ve_waning(estimates, n_draws = n, reference_weeks = 8,
                             waning_prior = "ray_2019", immune_lag_prior = "discrete_about_2w",
                             seed = seeds$protection)
stopifnot(all(as.integer(substr(ve$ve_source_season, 1, 4)) <= 2018))
utility <- evaluate_candidate_utilities(burden, ve, config$candidate_weeks)
examples <- lapply(seq_len(n), function(id) {
  b <- burden %>% filter(.data$draw == id)
  p <- ve %>% filter(.data$draw == id)
  u <- utility %>% filter(.data$draw == id) %>%
    slice(match(config$candidate_weeks, .data$vaccination_week))
  list(draw = id, season = b$season[[1]], weeks = b$week,
       max_week = b$max_week[[1]], burden = b$burden,
       timing_shift_weeks = scenarios$timing_shift_weeks[[id]],
       parameters = as.list(p[1, c("initial_ve", "beta_wane_per_28d", "immune_lag_weeks",
                                  "protection_model", "ve_reference_weeks", "ve_source_season")]),
       utility = u$utility)
})
sources <- unique(c(if (mode != "early") c(manifest_path, manifest$model_path), manifest$inputs$path,
                    "R/calendar.R", "R/latent_curve_gam.R", "R/decision_engine.R", "R/protection_models.R", "R/ve_priors.R", "R/ve_draws_from_estimates.R"))
fingerprints <- lapply(sources, function(p) list(path = p,
  sha256 = digest::digest(file = p, algo = "sha256")))
export <- list(mode = mode, n_draws = n, candidate_weeks = config$candidate_weeks,
               season_counts = as.list(table(scenarios$sampled_season)),
               scenarios = examples, sources = fingerprints,
               design_sha256 = digest::digest(file = design_path, algo = "sha256"))
if (mode == "early") export$early_model_manifest_sha256 <- digest::digest(file=file.path(out,"early-model-manifest.json"),algo="sha256")
if (mode != "training") export$threshold_fit_sha256 <- digest::digest(
  file = file.path(out, "threshold-fit.json"), algo = "sha256")
con <- gzfile(file.path(out, paste0(mode, "-draws.json.gz")), "wt")
writeLines(toJSON(export, auto_unbox = TRUE, digits = 16), con)
close(con)
message("Saved ", n, " ", mode, " pairs without changing manuscript files.")
