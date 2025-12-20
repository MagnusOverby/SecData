# -*- coding: utf-8 -*-
"""
Created on Sun Aug 24 21:50:49 2025

@author: lambe
"""

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
import os
import numpy as np
import sklearn as sk
from scipy import stats

def assign_quintiles(x, col):
    return pd.qcut(x[col], 5, labels=False, duplicates="drop") + 1


"""

need to finish this one up, it is not very complicated.


"""

def varianceEstimate(X,Y):
    pass

def TEST_HYPOTHESIS(df_ready,sectors_to_keep,col_to_test):
    df_test = df_ready[df_ready["sector"].isin(sectors_to_keep)].copy()
    
    
    df_test = df_test.dropna(subset=["inv_vol", col_to_test]).copy()
    
    try:
        # Assign quintiles each quarter
        df_test["q_invvol"] = (
        df_test.groupby("filing_date_cs")["inv_vol"]
               .transform(lambda x: pd.qcut(x, 5, labels=False, duplicates="drop") + 1))
        # Average revenue growth per quintile each quarter
        port = (df_test.groupby(["filing_date_cs","q_invvol"])[col_to_test]
                   .mean()
                   .reset_index())
        
        wide = port.pivot(index="filing_date_cs", columns="q_invvol", values=col_to_test).dropna(subset=[1,5])
        hml = (wide[5] - wide[1]).dropna()
        
        nr_tickers = len(set(df_test["ticker"]))
        
        # --- significance: one-sample t-test against 0 ---
        t_stat, p_val = stats.ttest_1samp(hml.values, 0.0)
        sectors_to_keep = "".join(sectors_to_keep)
        print(f"{sectors_to_keep} - Predicting column {col_to_test} - HML mean: {hml.mean():.4f}  |  t-stat: {t_stat:.2f}  |  p={p_val:.3f} | Number of companies: {nr_tickers}")
    except:
        pass

if __name__=="__main__":
    
    path = r"D:\code\SEC_Fundamentals\summary_statement\summary_statement_with_features.csv"
    df_ready = pd.read_csv(path)
    df_ready["inv_vol"] = df_ready["capex_vol_RND_xs"]
    
    """
    x["capex_vol_base_xs"]    = inv_base_rate.rolling(window, min_periods=6).std()
    x["capex_vol_RND_xs"]      = inv_base_RND_rate.rolling(window,min_periods=6).std()
    x["capex_vol_advanced_xs"] = inv_blended_rate.rolling(window, min_periods=6).std()
    """
    
    sectors = list(set(df_ready["sector"]))
    #ni_growth_next
    #rev_growth_next
    for s in sectors:
        TEST_HYPOTHESIS(df_ready,[s],"rev_growth_next_xs")
        TEST_HYPOTHESIS(df_ready,[s],"ni_growth_next_xs")
        TEST_HYPOTHESIS(df_ready,[s],"shareholder_return_proxy_prev_xs")