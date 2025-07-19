# -*- coding: utf-8 -*-
"""
Created on Thu Jul 10 10:12:01 2025

@author: magnu
"""

import pandas as pd
import numpy as np
import os 


def normalize_by_ticker_baseline(df):
    def baseline_normalize(group):
        group = group.sort_values("date")
        numeric_cols = group.drop(columns=['ticker', 'date']).columns
        result = group.copy()
        for col in numeric_cols:
            first_val = group[col].dropna().iloc[0] if not group[col].dropna().empty else None
            if first_val is not None and first_val != 0:
                result[col] = group[col] / first_val
            else:
                result[col] = group[col]
        return result
    return df.groupby('ticker', group_keys=False).apply(baseline_normalize)



def CheckNumberOfColumns(df):
    
    numeric_cols = df.drop(columns=['ticker', 'date']).columns

    # Step 2: Compute % non-NaN per column for each ticker
    non_nan_ratios = (
        df.groupby('ticker')[numeric_cols]
        .apply(lambda x: x.notna().mean())
    )
    
    # Step 3: Count how many columns per ticker have >=50% non-NaN
    valid_counts = (non_nan_ratios >= 0.5).sum(axis=1)
    
    # Step 4: Determine total number of numeric columns
    total_columns = len(numeric_cols)
    
    # Step 5: Keep tickers with at least 50% of columns populated
    valid_tickers = valid_counts[valid_counts >= (0.5 * total_columns)].index
    
    # Step 6: Filter original dataframe to only valid tickers
    filtered_df = df[df['ticker'].isin(valid_tickers)]

    return valid_tickers,filtered_df


if __name__=="__main__":
    
    
    
    path = r'D:\code\SEC\SecData\summary_statement'
    
    filenmn =["balance_sheet.csv"]
    
    df = pd.read_csv(os.path.join(path,filenmn[0]))
    
    _,df_a = CheckNumberOfColumns(df)
    #df_a = baseline_normalize(df_a)

