#!/usr/bin/env Rscript
# Read cached manuscript fits and export slide data; never fit or write there.
suppressPackageStartupMessages({
  library(dplyr)
  library(jsonlite)
  library(readr)
})
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2L)
project <- normalizePath(args[[1]])
out <- normalizePath(args[[2]], mustWork = FALSE)
dir.create(out, recursive = TRUE, showWarnings = FALSE)
setwd(project)
source("R/latent_curve_gam.R")
source("R/decision_engine.R")
manifest_path <- "outputs/primary/tables/gam_primary_analysis_manifest.json"
ve_path <- "outputs/primary/tables/gam_primary_ve_waning_draws.csv"
regret_path <- "outputs/primary/tables/gam_primary_regret_curve.csv"
optimum_path <- "outputs/primary/tables/gam_primary_optimal_week_draws.csv"
manifest <- read_json(manifest_path, simplifyVector = TRUE)
stopifnot(all(unname(tools::md5sum(manifest$inputs$path)) == manifest$inputs$md5))
models <- readRDS(manifest$model_path)
population <- read_csv("data/processed/state_population.csv", show_col_types = FALSE)
weights <- population$population[match(names(models), population$state)]
stopifnot(length(models) == 51L, all(is.finite(weights)), all(weights > 0))
weights <- weights / sum(weights)
ve <- read_csv(ve_path, show_col_types = FALSE) %>% arrange(.data$draw)
n <- manifest$configuration$n_draws
stopifnot(n == 5000L, nrow(ve) == n, identical(ve$draw, as.numeric(seq_len(n))),
          all(ve$age_group == "all"), all(ve$protection_model == "exponential_effect_ratio"))
scenarios <- sample_decision_scenarios(models, n, seed = 20260507,
                                      sample_complete_seasons_only = TRUE,
                                      timing_shift_sd = 0.75)
seasons <- sort(unique(scenarios$sampled_season))
groups <- lapply(seasons, function(s) which(scenarios$sampled_season == s))
names(groups) <- seasons
national <- list()
season_weeks <- list()

# Preserve the original state's RNG sequence. Matrix prediction and linear
# interpolation stream the same draws without materializing 10M state rows.
set.seed(20260508)
for (k in seq_along(models)) {
  state_seed <- sample.int(.Machine$integer.max, 1L)
  obj <- models[[k]]
  set.seed(state_seed)
  grid <- make_prediction_grid(obj$data)
  design <- stats::predict(obj$fit, newdata = grid, type = "lpmatrix")
  coefficients <- MASS::mvrnorm(n, stats::coef(obj$fit), obj$fit$Vp)
  for (s in seasons) {
    ids <- groups[[s]]
    rows <- which(as.character(grid$season) == s)
    weeks <- grid$mmwr_week[rows]
    max_week <- if (53L %in% weeks) 53L else 52L
    pos <- week_to_season_index(weeks, start_week = 36L, max_week = max_week)
    stopifnot(all(diff(pos) == 1L))
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
  if (k %% 10L == 0L || k == length(models)) message("Replayed ", k, "/51 cached states")
}
burden <- bind_rows(lapply(seasons, function(s) {
  ids <- groups[[s]]
  weeks <- season_weeks[[s]]
  tibble(draw = rep(ids, each = length(weeks)), state = "US", age_group = "all",
         season = s, week = rep(weeks, times = length(ids)),
         max_week = if (53L %in% weeks) 53L else 52L,
         burden = as.vector(t(national[[s]])))
}))
candidate_weeks <- c(36:52, 1:12)
utility <- evaluate_candidate_utilities(burden, ve, candidate_weeks)
total <- burden %>% group_by(.data$draw) %>% summarise(baseline = sum(.data$burden))
remaining <- utility %>% left_join(total, by = "draw") %>%
  mutate(remaining = .data$baseline - .data$utility)
mean_curve <- remaining %>% group_by(.data$vaccination_week) %>%
  summarise(remaining = mean(.data$remaining)) %>%
  slice(match(candidate_weeks, .data$vaccination_week))
regret <- summarise_regret_curve(utility)
saved_regret <- read_csv(regret_path, show_col_types = FALSE) %>%
  filter(.data$state == "US", .data$age_group == "all")
regret_error <- max(abs(regret$mean_regret - saved_regret$mean_regret[
  match(regret$vaccination_week, saved_regret$vaccination_week)]))
saved_optimum <- read_csv(optimum_path, show_col_types = FALSE) %>%
  filter(.data$state == "US", .data$age_group == "all")
best_utility <- utility %>% group_by(.data$draw) %>% summarise(best = max(.data$utility))
optimum_error <- max(abs(best_utility$best - saved_optimum$optimal_utility[
  match(best_utility$draw, saved_optimum$draw)]))
best_index <- which.min(mean_curve$remaining)
stopifnot(regret_error < 1e-10, optimum_error < 1e-10,
          mean_curve$vaccination_week[[best_index]] == 47L)

set.seed(20260928)
shown_ids <- sample.int(n, 10L, replace = FALSE)
examples <- lapply(shown_ids, function(id) {
  b <- burden %>% filter(.data$draw == id)
  p <- ve %>% filter(.data$draw == id)
  r <- remaining %>% filter(.data$draw == id) %>%
    slice(match(candidate_weeks, .data$vaccination_week))
  list(draw = id, season = b$season[[1]], weeks = b$week,
       max_week = b$max_week[[1]], burden = b$burden,
       timing_shift_weeks = scenarios$timing_shift_weeks[[id]],
       parameters = as.list(p[1, c("initial_ve", "beta_wane_per_28d", "immune_lag_weeks",
                                  "protection_model", "ve_reference_weeks", "ve_source_season")]),
       remaining = r$remaining)
})
sources <- unique(c(manifest_path, ve_path, regret_path, optimum_path,
                    manifest$model_path, manifest$inputs$path,
                    "R/calendar.R", "R/protection_models.R"))
fingerprints <- lapply(sources, function(p) list(path = p,
  sha256 = digest::digest(file = p, algo = "sha256")))
export <- list(slide = 25, analysis = "gam_primary", n_draws = n,
  selection = list(seed = 20260928, method = "Simple random sample without replacement", draw_ids = shown_ids),
  candidate_weeks = candidate_weeks, mean_remaining = mean_curve$remaining,
  mean_baseline = mean(total$baseline),
  mean_minimum_remaining = mean(total$baseline - best_utility$best[match(total$draw, best_utility$draw)]),
  best_index = best_index - 1L, best_week = 47L, scenarios = examples,
  scale = "US population-weighted weekly ILI proportions summed across the season; no per-scenario normalization",
  validation = list(mean_regret_max_absolute_error = regret_error,
                    all_5000_optimal_utilities_max_absolute_error = optimum_error,
                    compared_candidate_weeks = 29L),
  sources = fingerprints)
write_json(export, file.path(out, "inputs.json"), auto_unbox = TRUE, pretty = TRUE, digits = 16)
message("Saved ten original scenarios and exact 5,000-draw mean; regret error = ",
        format(regret_error), "; optimal-utility error = ", format(optimum_error))
