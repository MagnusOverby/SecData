# -*- coding: utf-8 -*-
"""
Created on Sat Jun  7 17:40:51 2025

@author: lambe
"""

"""
The idea here is to get all the data from edgar.
We then save it in flat text files.
Basically we create a folder stucture like follows:
/Company/IS_[Date].csv
/Company/CS_[Date].csv
/Company/BS_[Date].csv
I can then at a later statge make them look nicer.
"""



from edgar import *
from edgar.xbrl import *
import pandas as pd
from typing import Optional
import numpy as np
import os

# Base directory for saved data. Can be overridden with the
# SEC_FUNDAMENTALS_DIR environment variable.
BASE_DIR = os.environ.get('SEC_FUNDAMENTALS_DIR', r"D:\code\SEC\SecData")

def saveAccountingData(df_dict,path):
    
    output_dir = f"{path}"
    os.makedirs(output_dir, exist_ok=True)
    
    
    for key,df in df_dict.items():
        file_path = os.path.join(output_dir, f"{key}.csv")
        df.to_csv(file_path)


def GetAccountingDict(filings):
    xbs = XBRLS.from_filings(filings)
    data = {}
    for stmt_name, stmt_func in [
        ("incomeStatement", xbs.statements.income_statement),
        ("cashflowStatement", xbs.statements.cashflow_statement),
        ("balanceSheet", xbs.statements.balance_sheet)
    ]:
        try:
            df = stmt_func().to_dataframe()
            # Pivot so index is date, columns are features
            df_pivot = df.set_index("label").T
            data[stmt_name] = df_pivot
        except Exception as e:
            data[stmt_name] = None  # or {}
    return data


def GetAccountingData(ticker: str, howFarBack, base_dir: Optional[str] = None):

    c = Company(ticker)
    base_dir = base_dir or BASE_DIR
    base_path = os.path.join(base_dir, ticker)

    Time_Frame = howFarBack
    
    
    filings = c.get_filings(form="10-Q").latest(Time_Frame)
    
    try:
        industry = c.data.industry
        df_dict = GetAccountingDict(filings)
    
        print(f"Saved {ticker} to {base_path}")
        saveAccountingData(df_dict,base_path)
    except:
        pass
    


def GetAllTickers(base_dir: Optional[str] = None):

    base_dir = base_dir or BASE_DIR
    path = os.path.join(base_dir, "allTickers.csv")
    df_ticker = pd.read_csv(path)
    return df_ticker

def main():
    
    email = "magnus@pagnus.com"
    set_identity(email)
    base_dir = BASE_DIR
    tickers = GetAllTickers(base_dir)
    tickers = tickers["ticker"]
    for ticker in tickers[150:500]:
        
        try:
            GetAccountingData(ticker, 15, base_dir)
        except:
            print(f"Error fetching {ticker}")

if __name__ == "__main__":
    main()
    