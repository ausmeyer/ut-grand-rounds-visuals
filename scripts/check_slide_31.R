#!/usr/bin/env Rscript
# Read-only independent check of every state/draw policy result and summary.
suppressPackageStartupMessages(library(jsonlite))
folder <- 'data/slide-31/'
config <- fromJSON(paste0(folder,'design.json'))
source <- fromJSON(gzfile(paste0(folder,'states-draws.json.gz')))
results <- fromJSON(gzfile(paste0(folder,'states-results.json.gz')),simplifyVector=FALSE)
fit <- fromJSON('data/slide-30/threshold-example/threshold-fit.json')
guidance <- fromJSON(paste0(folder,'guidance-comparator.json'))
policies <- c('guidance','fixed','threshold')
stopifnot(source$n_draws==5000, identical(source$draw_ids,1:5000),
          identical(names(source$states),config$states),
          fit$threshold_multiplier==1.7, fit$fixed_week==47, guidance$week==44,
          results$guidance_comparator_sha256==digest::digest(file=paste0(folder,'guidance-comparator.json'),algo='sha256'))
for(state_name in config$states) {
  input <- source$states[[state_name]]
  output <- results$states[[state_name]]
  weeks <- input$weeks; candidates <- source$candidate_weeks
  times <- ifelse(candidates>=36,candidates-36,input$max_week-36+candidates)
  timing <- benefit <- matrix(NA_real_,5000,length(policies),dimnames=list(NULL,policies))
  optima <- numeric(5000); baseline_optima <- boundary_optima <- 0L
  stopifnot(nrow(input$burden)==5000,nrow(input$utility)==5000,
            length(output$scenarios)==5000)
  for(i in 1:5000) {
    row <- output$scenarios[[i]]
    burden <- input$burden[i,]; utility <- input$utility[i,]
    baseline <- mean(burden[match(36:39,weeks)])
    trigger <- which(times>3 & burden[match(candidates,weeks)]>=1.7*baseline)[1]
    optimum <- which(abs(utility-max(utility))<1e-12)
    optima[i] <- max(utility)
    baseline_optima <- baseline_optima+any(times[optimum]<=3)
    boundary_optima <- boundary_optima+any(optimum==1)
    stopifnot(row$draw==i,abs(baseline-row$baseline)<1e-12,
              identical(as.numeric(unlist(row$optimal_weeks)),as.numeric(candidates[optimum])),
              abs(row$optimal_utility-optima[i])<1e-12)
    plotted <- do.call(rbind,row$burden_points)
    stopifnot(max(abs(as.numeric(plotted[,2])-burden/baseline))<1e-12)
    for(policy in policies) {
      k <- switch(policy,guidance=match(guidance$week,candidates),fixed=match(47,candidates),threshold=trigger)
      benefit[i,policy] <- if(is.na(k)) 0 else utility[k]
      if(is.na(k)) {
        stopifnot(is.null(row[[paste0(policy,'_week')]]))
      } else {
        delta <- times[k]-times[optimum]
        timing[i,policy] <- delta[which.min(abs(delta))]
        stopifnot(row[[paste0(policy,'_week')]]==candidates[k],
                  row[[paste0(policy,'_timing_error')]]==timing[i,policy],
                  abs(row[[paste0(policy,'_height')]]-burden[match(candidates[k],weeks)]/baseline)<1e-12)
      }
      loss <- (optima[i]-benefit[i,policy])/optima[i]
      stopifnot(abs(row[[paste0(policy,'_utility')]]-benefit[i,policy])<1e-12,
                abs(row[[paste0(policy,'_relative_loss')]]-loss)<1e-12)
    }
  }
  for(policy in policies) {
    reported <- output$summary[[policy]]
    error <- timing[,policy]; loss <- 1-benefit[,policy]/optima
    stopifnot(reported$n==5000,reported$non_crossings==sum(is.na(error)),
              reported$median_absolute_weeks==median(abs(error),na.rm=TRUE),
              reported$median_signed_weeks==median(error,na.rm=TRUE),
              reported$within_2_weeks==sum(abs(error)<=2,na.rm=TRUE),
              abs(reported$mean_absolute_weeks-mean(abs(error),na.rm=TRUE))<1e-12,
              abs(reported$pooled_relative_loss-(1-sum(benefit[,policy])/sum(optima)))<1e-12,
              abs(reported$mean_relative_loss-mean(loss))<1e-12,
              abs(reported$median_relative_loss-median(loss))<1e-12)
  }
  stopifnot(output$summary$threshold_better_draws==sum(benefit[,'threshold']>benefit[,'fixed']+1e-12))
  cat(state_name,': 5000 pairs passed; optimal during baseline =',baseline_optima,
      '; earliest-candidate optimum =',boundary_optima,'\n')
}
cat('Independent R check passed: all 20,000 state pairs, trigger dates, optima, timing gaps, losses and pooled summaries.\n')
