#!/usr/bin/env Rscript
# Independent, vectorized checks against the saved paired draws.
library(jsonlite)
raw <- fromJSON(gzfile('data/august-baseline/training-draws.json.gz'), simplifyVector=FALSE)
shown <- fromJSON('data/slide-32/diagnostic.json', simplifyVector=FALSE)
aligned <- fromJSON('data/august-baseline/alignment.json', simplifyVector=FALSE)$alignment
as_points <- function(x) do.call(rbind, lapply(x, unlist))
time <- function(w, max_week) ifelse(w >= 32, w-36, max_week-36+w)
offsets <- matrix(NA_real_, length(raw$scenarios), 2,
                  dimnames=list(NULL, c('dose', 'onset')))
seasons <- character(nrow(offsets))
curve_error <- slope_error <- marker_error <- mean_error <- 0
mean_grid <- as_points(shown$mean$activity)
slope_grid <- as_points(shown$mean$slope)
activity_matrix <- matrix(NA_real_, nrow(mean_grid), 50)
slope_matrix <- matrix(NA_real_, nrow(slope_grid), 50)
origin <- min(vapply(aligned$profiles, function(p) p$shift, numeric(1)))

for (i in seq_along(raw$scenarios)) {
  r <- raw$scenarios[[i]]
  t <- time(unlist(r$weeks), r$max_week)
  y <- 100*unlist(r$burden)
  # Average adjacent first differences, independently of Python's secant code.
  delta <- diff(y)
  slope <- (head(delta, -1)+tail(delta, -1))/2
  st <- t[2:(length(t)-1)]
  slope <- slope[st >= 0]
  st <- st[st >= 0]
  best <- which.max(unlist(r$utility))
  dose <- time(raw$candidate_weeks[[best]], r$max_week)
  onset <- dose+r$parameters$immune_lag_weeks
  fastest <- st[which.max(slope)]
  offsets[i, ] <- c(dose, onset)-fastest
  seasons[i] <- r$season
  if (i <= 50) {
    s <- shown$scenarios[[i]]
    stopifnot(s$draw == r$draw, s$season == r$season,
              s$dose_week == raw$candidate_weeks[[best]], s$fastest == fastest)
    slope_error <- max(slope_error, abs(as_points(s$slope)-cbind(st, slope)))
    curve_error <- max(curve_error, abs(as_points(s$activity)-cbind(t[t>=0], y[t>=0])))
    marker_error <- max(marker_error, abs(c(s$dose, s$onset)-c(dose, onset)))
    shift <- aligned$profiles[[i]]$shift-origin
    stopifnot(s$shift == shift)
    activity_matrix[,i] <- approx(t+shift, y, xout=mean_grid[,1])$y
    slope_matrix[,i] <- approx(st+shift, slope, xout=slope_grid[,1])$y
  }
}
mean_error <- max(abs(rowMeans(activity_matrix)-mean_grid[,2]),
                  abs(rowMeans(slope_matrix)-slope_grid[,2]))
stopifnot(!anyNA(activity_matrix), !anyNA(slope_matrix))
summary_error <- 0
for (s in shown$seasons) {
  keep <- seasons == s$season
  stopifnot(sum(keep) == s$n, sum(head(keep, 50)) == s$display_n)
  for (kind in c('dose','onset')) {
    actual <- unname(quantile(offsets[keep,kind], c(.25,.5,.75), type=7))
    expected <- unlist(s[[kind]][c('q1','median','q3')])
    summary_error <- max(summary_error, abs(actual-expected))
  }
}
aligned_dose <- vapply(shown$scenarios, function(s) s$dose+s$shift, numeric(1))
aligned_onset <- vapply(shown$scenarios, function(s) s$onset+s$shift, numeric(1))
stopifnot(median(aligned_dose) == shown$mean$dose,
          median(aligned_onset) == shown$mean$onset,
          slope_grid[which.max(slope_grid[,2]),1] == shown$mean$fastest)
errors <- c(curve=curve_error, slope=slope_error, markers=marker_error,
            aligned_mean=mean_error, season_summaries=summary_error)
stopifnot(all(errors < 1e-12))
result <- list(status='PASS', method='Independent R adjacent differences and type-7 quantiles',
               checked_pairs=nrow(offsets), checked_plotted_pairs=50,
               maximum_absolute_errors=as.list(errors),
               pooled_onset_quartiles=unname(quantile(offsets[,'onset'], c(.25,.5,.75))),
               pooled_onset_within_two_weeks=mean(abs(offsets[,'onset']) <= 2),
               sources_sha256=shown$sources_sha256)
write_json(result, 'data/slide-32/independent-validation.json', pretty=TRUE,
           auto_unbox=TRUE, digits=16)
print(result)
