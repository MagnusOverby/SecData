# -*- coding: utf-8 -*-
"""
Created on Sun Nov 23 20:47:58 2025

@author: lambe
"""

import xgboost as xg
import pandas as pd
import sklearn as sk
import numpy as np



def Normalize_X(df):
    
    df_t = df.copy()
    
    xs_cols = [x for x in df_t.columns if x.endswith("_xs")]
    
    df_t[xs_cols] = df_t.groupby("filing_date",group_keys=False)[xs_cols].apply(ZScorer)
    
    return df_t

    
def ZScorer(x):
    
    return (x-x.mean(axis=0))/x.std(axis=0)


def PrePareDataSet(X,Y):
    
    c = [i for i in X.columns if i.endswith("_xs")]
    c.append("filing_date")
    c.append("ticker")
    # this messes it up.
    X = X[c]
    
    Y_drop = Y.dropna()
    X_drop= X.loc[Y_drop.index,:]
    Y_drop= Y_drop.loc[X_drop.index]
    Y_drop[Y_drop==-1] = 0

    return  X_drop,Y_drop

def TrainTestSplit(X,Y,cutoff="2020-01-01"):
    
    
    X,Y = PrePareDataSet(X,Y) #ADD THIS ROW!

    df = X.copy()
    df["Y"] = Y
    df["filing_date"] = pd.to_datetime(df["filing_date"])

   
    df = df.sort_values(["filing_date", "ticker"])

    cutoff = pd.to_datetime(cutoff)
    train = df[df["filing_date"] <= cutoff]
    test  = df[df["filing_date"] >  cutoff]

    
    y_train = train["Y"]
    y_test  = test["Y"]
    X_train = train.drop(columns=["Y"])
    X_test  = test.drop(columns=["Y"])

    return X_train, X_test, y_train, y_test


from xgboost import XGBClassifier

def Classifier(X,Y,cutoff="2020-01-01"):
    
    X_train,X_test,y_train,y_test = TrainTestSplit(X,Y,cutoff)
    
    feature_cols = [c for c in X_train.columns if c.endswith("_xs")]
    
    model = XGBClassifier(
        max_depth=3,
        learning_rate=0.05,
        n_estimators=300,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
    )
    
    model.fit(X_train[feature_cols],y_train)
    
    y_prob_test = model.predict_proba(X_test[feature_cols])[:,1]
    y_pred_test = (y_prob_test>=0.5).astype(int)
    
    return model,X_test,y_test,y_prob_test,y_pred_test
    


from scipy.stats import spearmanr

def MDA(X,Y):
    
    
    # get the base line for MDA.
    # What is a decent performance baseline?
    
    model, X_test, y_test, y_prob, _ = Classifier(X, Y)
    
    base_IC, _ = spearmanr(y_prob,y_test)

    feature_cols = [x for x in X.columns if x.endswith("_xs")]
    
    output = {}
    #output["base"] = base_IC
    
    for feat in feature_cols:
        #Shuffle this columns
        X_shuf = X_test.copy()
        
        X_shuf[feat] = shuffle_feature(X_shuf[feat])
        
        y_prob_shuf = model.predict_proba(X_shuf[feature_cols])[:, 1]
        
        IC_shuf,_ = spearmanr(y_prob_shuf,y_test)
        print(f"checking without {feat:30s} : {IC_shuf:.4f} vs {base_IC:.4f} drop={base_IC - IC_shuf: .4f}")
        output[feat]=base_IC-IC_shuf
    
    return output
        
def shuffle_feature(col):
    return np.random.permutation(col.values)        


def MDI(model):
    
    print(model.get_booster().get_score(importance_type="gain"))


import matplotlib.pyplot as plt

if __name__=="__main__":
    
    path = r"D:\code\SEC_Fundamentals\summary_statement\summary_statement_with_features.csv"
    df_ready = pd.read_csv(path)
    X = Normalize_X(df_ready)
    
    Y_col = "shareholder_return_proxy_next_ys"
    Y = np.sign(df_ready[Y_col])
    
    if Y_col == "shareholder_return_proxy_next_ys":
        X = X.drop(columns=["shareholder_return_proxy_xs"])
    
    model,Xt,Yt,Ypr,Ypred = Classifier(X,Y)
    MDI(model)
    out = MDA(X,Y)
    
    
    
    