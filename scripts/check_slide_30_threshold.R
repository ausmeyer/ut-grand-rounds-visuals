suppressPackageStartupMessages(library(jsonlite))
f <- 'data/slide-30/threshold-example/'
args <- commandArgs(trailingOnly=TRUE)
mode <- if(length(args)) args[[1]] else 'evaluation'
a <- fromJSON(gzfile(paste0(f,'training-draws.json.gz')), simplifyVector=FALSE)
b <- fromJSON(gzfile(paste0(f,mode,'-draws.json.gz')), simplifyVector=FALSE)
fit <- fromJSON(paste0(f,'threshold-fit.json'))
result_path <- paste0(f,mode,'-results.json')
results <- fromJSON(if(file.exists(result_path)) result_path else gzfile(paste0(result_path,'.gz')), simplifyVector=FALSE)
candidates <- as.numeric(unlist(a$candidate_weeks))
ratio <- vapply(a$scenarios,function(s) {
  weeks <- unlist(s$weeks); activity <- unlist(s$burden); u <- unlist(s$utility)
  median(activity[match(candidates[abs(u-max(u))<1e-12],weeks)])/mean(activity[match(36:39,weeks)])
}, numeric(1))
u <- do.call(rbind,lapply(a$scenarios,function(s)unlist(s$utility)))
stopifnot(abs(median(ratio)-fit$optimal_activity_ratio_median)<1e-12,
          floor(median(ratio)*10+.5)/10==fit$threshold_multiplier,
          candidates[which.max(colMeans(u))]==fit$fixed_week)
for(i in seq_along(b$scenarios)) {
  s <- b$scenarios[[i]]; r <- results$scenarios[[i]]
  weeks <- unlist(s$weeks); values <- unlist(s$burden); utility <- unlist(s$utility)
  base <- mean(values[match(36:39,weeks)])
  candidate_value <- values[match(candidates,weeks)]/base
  trigger <- which(seq_along(candidates)>4 & candidate_value>=fit$threshold_multiplier)[1]
  opt <- which(abs(utility-max(utility))<1e-12)
  times <- ifelse(candidates>=36,candidates-36,s$max_week-36+candidates)
  for(policy in c('fixed','threshold')) {
    k <- if(policy=='fixed') match(fit$fixed_week,candidates) else trigger
    delta <- times[k]-times[opt]
    delta <- delta[which.min(abs(delta))]
    loss <- (max(utility)-utility[k])/max(utility)
    stopifnot(candidates[k]==r[[paste0(policy,'_week')]],
              delta==r[[paste0(policy,'_timing_error')]],
              abs(loss-r[[paste0(policy,'_relative_loss')]])<1e-12)
  }
}
cat('Independent R check passed:', mode, length(b$scenarios), 'pairs; frozen threshold, fixed week, triggers, per-draw timing and loss.\n')
