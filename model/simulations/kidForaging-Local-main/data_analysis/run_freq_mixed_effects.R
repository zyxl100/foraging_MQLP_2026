library(lme4)
library(ggplot2)
library(lmerTest)
library(MuMIn)

setwd("/Users/nharhen/Desktop/Projects/foraging/Harhen-Hartley-Bornstein-2025/data_analysis")
linear_df <- read.csv("transformed_data/linear_df_20241221.csv")
rt_df <- read.csv("transformed_data/stay_num_RT_20241221.csv")

################################################################################
# checking for relationships between predictors
################################################################################
m1 <- lmer(prt_rel_om ~  agez + (1|sub_num), data = linear_df,control=lmerControl(optimizer="bobyqa",optCtrl=list(maxfun=10000)))
summary(m1)

m2 <- lmer(prt_rel_om ~  agez*galaxy*planet_n_norm + (1 + galaxy*planet_n_norm|sub_num), data = linear_df,control=lmerControl(optimizer="bobyqa",optCtrl=list(maxfun=10000)))
summary(m2)

m3 <- lmer(prt_rel_om ~  agez*switch*planet_n_norm + (1 + planet_n_norm|sub_num), data = linear_df,control=lmerControl(optimizer="bobyqa",optCtrl=list(maxfun=10000))) # did not converge when including switch 
summary(m3)

m4<- lmer(zlog_rt ~ agez*switch*planet_n_norm + (1+switch|sub_num), data = rt_df,control=lmerControl(optimizer="bobyqa",optCtrl=list(maxfun=10000)))
summary(m4)

