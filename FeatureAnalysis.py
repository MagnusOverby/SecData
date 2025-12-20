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


def assign_quintiles(x, col):
    return pd.qcut(x[col], 5, labels=False, duplicates="drop") + 1


"""

need to finish this one up, it is not very complicated.


"""

def varianceEstimate(X,Y):
    

if __name__=="__main__":
    
    path = r"D:\code\SEC_Fundamentals\summary_statement\summary_statement_with_features.csv"
    df_ready = pd.read_csv(path)
    df_ready["inv_vol"] = df_ready["inv_base_RND"]
    
    df_test = df_ready.dropna(subset=["inv_vol", "rev_growth_next"]).copy()
    
    # Assign quintiles each quarter
    df_test["q_invvol"] = df_test.groupby("date").apply(assign_quintiles, "inv_vol").reset_index(level=0, drop=True)
    
    # Average revenue growth per quintile each quarter
    portfolios = df_test.groupby(["date", "q_invvol"])["rev_growth_next"].mean().reset_index()
    
    # Average across time
    avg_growth = portfolios.groupby("q_invvol")["rev_growth_next"].mean()
    print(avg_growth)
    
    # High - Low spread each period
    spread = portfolios.pivot(index="date", columns="q_invvol", values="rev_growth_next")
    spread["HML"] = spread[5] - spread[1]
    
    # T-test across time
    from sklearn import linear_model as lm
    regr = lm.LinearRegression()
    
    X = spread["HML"].dropna().values
    X = X[~np.isinf(X)]
    X = X.reshape(-1,1)
    
    Y = np.ones(len(X))
    
    regr.fit(X,Y)
    
    regr.score(X, Y)
