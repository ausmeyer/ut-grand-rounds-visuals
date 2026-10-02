#!/usr/bin/env Rscript
# Independently verify the current ILINet observations, calendar, and threshold.
library(jsonlite)
folder <- 'data/slide-32/current-ilinet'
d <- fromJSON(file.path(folder, 'slide.json'), simplifyVector=FALSE)
p <- fromJSON(file.path(folder, 'provenance.json'), simplifyVector=FALSE)
for (name in names(p$source_sha256)) {
  stopifnot(digest::digest(file=file.path(folder,name), algo='sha256') == p$source_sha256[[name]])
}
fit <- fromJSON('data/august-baseline/threshold-fit.json')
stopifnot(digest::digest(file='data/august-baseline/threshold-fit.json', algo='sha256') == d$threshold_fit_sha256,
          d$threshold_multiplier == fit$threshold_multiplier,
          identical(unlist(d$baseline_weeks), as.integer(fit$baseline_weeks)))
read_source <- function(name) read.csv(file.path(folder,name), skip=1, check.names=FALSE,
                                      na.strings=c('X','NA',''), stringsAsFactors=FALSE)
national <- read_source('national.csv')
states <- read_source('states.csv')
maximum_error <- 0
results <- list()
for (location in c(list(d$national), d$states)) {
  source <- if (location$name == 'United States') national else states[states$REGION == location$name,]
  source <- source[source$YEAR == d$year & source$WEEK >= d$first_week & source$WEEK <= d$latest_week,]
  source <- source[order(source$WEEK),]
  weeks <- vapply(location$points, function(x) x$week, integer(1))
  values <- vapply(location$points, function(x) if(is.null(x$value)) NA_real_ else x$value, numeric(1))
  dates <- vapply(location$points, function(x) x$week_ending, character(1))
  expected <- source[[location$source_column]]
  stopifnot(identical(weeks, source$WEEK), identical(is.na(values), is.na(expected)),
            identical(dates, as.character(MMWRweek::MMWRweek2Date(source$YEAR,source$WEEK)+6)))
  baseline <- mean(expected[weeks %in% 32:35])
  threshold <- baseline*fit$threshold_multiplier
  maximum_error <- max(maximum_error, abs(values-expected),
                        abs(baseline-location$baseline_percentage),
                        abs(threshold-location$threshold_percentage), na.rm=TRUE)
  crosses <- weeks[weeks >= fit$first_trigger_week & !is.na(expected) & expected >= threshold]
  if(length(crosses)) stopifnot(location$first_crossing_week == crosses[1]) else stopifnot(is.null(location$first_crossing_week))
  if(location$name != 'United States') {
    # The published state percentages are rounded. Counts provide a second check.
    stopifnot(max(abs(100*source$ILITOTAL/source[['TOTAL PATIENTS']]-expected), na.rm=TRUE) < 1e-5)
  }
  results[[location$name]] <- list(points=length(values), baseline=baseline, threshold=threshold,
                                   latest=tail(values,1), crossed=length(crosses)>0)
}
nyc <- subset(states, REGION == 'New York City' & YEAR == d$year & WEEK >= d$first_week & WEEK <= d$latest_week)
stopifnot(all(is.na(nyc[['%UNWEIGHTED ILI']])), all(is.na(nyc$ILITOTAL)),
          d$states[[4]]$label == 'New York (excl. NYC)', maximum_error < 1e-12)
result <- list(status='PASS', method='Independent R CSV parsing, MMWR calendar conversion, means, count ratios, and thresholds',
               latest_week_ending=d$latest_week_ending, maximum_absolute_error=maximum_error,
               locations=results, threshold_fit_sha256=d$threshold_fit_sha256,
               source_sha256=p$source_sha256)
write_json(result, file.path(folder,'validation.json'), pretty=TRUE, auto_unbox=TRUE, digits=16)
print(result[c('status','latest_week_ending','maximum_absolute_error','locations')])
