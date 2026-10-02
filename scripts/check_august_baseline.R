#!/usr/bin/env Rscript
# Independent R audit of calibration, every policy result, and preservation.
suppressPackageStartupMessages(library(jsonlite))
folder <- 'data/august-baseline/'
sha <- function(path) digest::digest(file=path,algo='sha256')
design <- fromJSON(paste0(folder,'design.json'))
fit <- fromJSON(paste0(folder,'threshold-fit.json'))
read_pairs <- function(mode) fromJSON(gzfile(paste0(folder,mode,'-draws.json.gz')),simplifyVector=FALSE)
training <- read_pairs('training')
candidates <- as.integer(unlist(training$candidate_weeks));n <- design$n_draws
ratio <- vapply(training$scenarios,function(row) {
  weeks <- unlist(row$weeks);burden <- unlist(row$burden);utility <- unlist(row$utility)
  stopifnot(as.integer(substr(row$season,1,4)) %in% design$training_seasons)
  optimal <- which(abs(utility-max(utility))<1e-12)
  median(burden[match(candidates[optimal],weeks)]/mean(burden[match(32:35,weeks)]))
},numeric(1))
means <- colMeans(do.call(rbind,lapply(training$scenarios,function(r)unlist(r$utility))))
stopifnot(length(ratio)==n,abs(median(ratio)-fit$optimal_activity_ratio_median)<1e-12,
          floor(median(ratio)*10+.5)/10==fit$threshold_multiplier,
          candidates[which.max(means)]==fit$refitted_training_optimal_fixed_week,
          fit$fixed_week==47,fit$guidance_week==44,
          fit$training_draws_sha256==sha(paste0(folder,'training-draws.json.gz')))
policies <- c('guidance','fixed','threshold')
check_set <- function(label,inputs,output) {
  stopifnot(length(inputs)==n,length(output$scenarios)==n)
  timing <- benefit <- matrix(NA_real_,n,3,dimnames=list(NULL,policies))
  optima <- numeric(n);boundary_optima <- 0L
  seasons <- character(n)
  for(i in seq_len(n)) {
    input <- inputs[[i]];row <- output$scenarios[[i]]
    weeks <- unlist(input$weeks);burden <- unlist(input$burden);utility <- unlist(input$utility)
    times <- ifelse(candidates>=36,candidates-36,input$max_week-36+candidates)
    base <- mean(burden[match(32:35,weeks)])
    trigger <- which(times>=0 & burden[match(candidates,weeks)]>=fit$threshold_multiplier*base)[1]
    optimum <- which(abs(utility-max(utility))<1e-12);optima[i] <- max(utility)
    seasons[i] <- row$season;boundary_optima <- boundary_optima+any(optimum==1)
    stopifnot(row$draw==i,abs(base-row$baseline)<1e-12,
              identical(as.numeric(unlist(row$optimal_weeks)),as.numeric(candidates[optimum])),
              abs(row$optimal_utility-optima[i])<1e-12)
    keep <- weeks>=36 | weeks<=22
    plotted <- do.call(rbind,lapply(row$burden_points,unlist))
    expected_times <- ifelse(weeks[keep]>=36,weeks[keep]-36,input$max_week-36+weeks[keep])
    stopifnot(all(plotted[,1]==expected_times),max(abs(plotted[,2]-burden[keep]/base))<1e-12,
              max(abs(unlist(row$optimal_heights)-burden[match(candidates[optimum],weeks)]/base))<1e-12)
    for(policy in policies) {
      k <- switch(policy,guidance=match(44,candidates),fixed=match(47,candidates),threshold=trigger)
      benefit[i,policy] <- if(is.na(k))0 else utility[k]
      if(is.na(k)) {
        stopifnot(is.null(row[[paste0(policy,'_week')]]),is.null(row[[paste0(policy,'_timing_error')]]))
      } else {
        delta <- times[k]-times[optimum];timing[i,policy] <- delta[which.min(abs(delta))]
        stopifnot(row[[paste0(policy,'_week')]]==candidates[k],
                  row[[paste0(policy,'_time')]]==times[k],
                  row[[paste0(policy,'_timing_error')]]==timing[i,policy],
                  abs(row[[paste0(policy,'_height')]]-burden[match(candidates[k],weeks)]/base)<1e-12)
      }
      stopifnot(abs(row[[paste0(policy,'_utility')]]-benefit[i,policy])<1e-12,
                abs(row[[paste0(policy,'_relative_loss')]]-(1-benefit[i,policy]/optima[i]))<1e-12)
    }
  }
  check_summary <- function(ids,summary) for(policy in policies) {
    reported <- summary[[policy]];error <- timing[ids,policy];loss <- 1-benefit[ids,policy]/optima[ids]
    stopifnot(reported$n==length(ids),reported$n_timing==sum(!is.na(error)),reported$non_crossings==sum(is.na(error)),
              reported$median_absolute_weeks==median(abs(error),na.rm=TRUE),
              reported$median_signed_weeks==median(error,na.rm=TRUE),
              reported$within_2_weeks==sum(abs(error)<=2,na.rm=TRUE),
              abs(reported$mean_absolute_weeks-mean(abs(error),na.rm=TRUE))<1e-12,
              abs(reported$pooled_relative_loss-(1-sum(benefit[ids,policy])/sum(optima[ids])))<1e-12,
              abs(reported$mean_relative_loss-mean(loss))<1e-12,
              abs(reported$median_relative_loss-median(loss))<1e-12)
  }
  check_summary(seq_len(n),output$summary)
  for(s in unique(seasons)) check_summary(which(seasons==s),output$by_season[[s]])
  cat(label,':',n,'pairs passed; earliest-candidate optimum =',boundary_optima,'\n')
  list(n=n,earliest_candidate_optima=boundary_optima,all_policy_checks_passed=TRUE,
       threshold_better_than_fixed=sum(benefit[,'threshold']>benefit[,'fixed']+1e-12),
       threshold_better_than_guidance=sum(benefit[,'threshold']>benefit[,'guidance']+1e-12))
}
checks <- list()
for(mode in c('early','expanded')) {
  inputs <- read_pairs(mode)
  output <- fromJSON(gzfile(paste0(folder,mode,'-results.json.gz')),simplifyVector=FALSE)
  stopifnot(inputs$threshold_fit_sha256==sha(paste0(folder,'threshold-fit.json')),
            output$draws_sha256==sha(paste0(folder,mode,'-draws.json.gz')))
  checks[[mode]] <- check_set(mode,inputs$scenarios,output)
}
source <- fromJSON(gzfile(paste0(folder,'states-draws.json.gz')))
results <- fromJSON(gzfile(paste0(folder,'states-results.json.gz')),simplifyVector=FALSE)
for(name in design$states) {
  state <- source$states[[name]]
  rows <- lapply(seq_len(n),function(i)list(weeks=state$weeks,max_week=state$max_week,
                                          burden=state$burden[i,],utility=state$utility[i,]))
  checks[[name]] <- check_set(name,rows,results$states[[name]])
}
snapshot <- fromJSON(paste0(folder,'prior-snapshot.json'))
for(path in names(snapshot)) stopifnot(sha(path)==snapshot[[path]])
write_json(list(training_calibration_passed=TRUE,training_n=n,policy_checks=checks,
                preserved_prior_files=length(snapshot),threshold_fit_sha256=sha(paste0(folder,'threshold-fit.json'))),
           paste0(folder,'independent-validation.json'),auto_unbox=TRUE,pretty=TRUE)
cat('Independent R audit passed; preserved',length(snapshot),'prior data and unrelated slide files.\n')
