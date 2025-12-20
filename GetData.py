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
BASE_DIR = os.environ.get('SEC_FUNDAMENTALS_DIR', r"D:\code\SEC_Fundamentals")

def saveAccountingData(df_dict,path):
    
    output_dir = f"{path}"
    os.makedirs(output_dir, exist_ok=True)
    
    
    for key,df in df_dict.items():
        file_path = os.path.join(output_dir, f"{key}.csv")
        #neet to concat them now
        df_out = pd.concat(df,axis=0,sort=False,keys=range(len(df)),ignore_index=True)
        df_out.to_csv(file_path)


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



def _pivot_statement(df: pd.DataFrame) -> pd.DataFrame:
    # If header rows present, build column names from label/concept
    if "label" in df.index:
        labels = df.loc["label"].astype(str).str.strip()
        concepts = df.loc["concept"].astype(str).str.strip() if "concept" in df.index else None
        cols = labels.copy()
        if concepts is not None:
            dup = cols.duplicated(keep=False)
            cols[dup] = cols[dup] + " (" + concepts[dup] + ")"
        df = df.copy()
        df.columns = cols
        df = df.drop(index=[r for r in ["label","concept","level","abstract","dimension"] if r in df.index])

    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df.loc[df.index.notna()].sort_index()
    return df.apply(pd.to_numeric, errors="coerce")

def GetAccountingData_Redux(ticker: str, howFarBack: int, base_dir: Optional[str] = None):
    """
    Pull last `howFarBack` 10-Q and 10-K filings, parse XBRL, and save one CSV per filing:
      <BASE_DIR>/<TICKER>/{IS|CF|BS}_<YYYY-MM-DD>.csv
    """
    base_dir = base_dir or BASE_DIR
    base_path = os.path.join(base_dir, ticker)
    os.makedirs(base_path, exist_ok=True)

    c = Company(ticker)
    
    output = {}
    output["IS"] = []
    output["BS"] = []
    output["CF"] = [] 
    

    # --- fetch both 10-Q and 10-K, then merge & sort ---
    filings_q = c.get_filings(form="10-Q").latest(howFarBack)
    filings_k = c.get_filings(form="10-K").latest(howFarBack)
    filings = sorted(
        {f.accession_no: f for f in list(filings_q) + list(filings_k)}.values(),
        key=lambda f: f.filing_date
    )

    # --- iterate filings; parse and save statements per filing ---
    for f in filings:
        try:
            # Some libraries expose XBRL.from_filing; others only XBRLS.from_filings
            try:
                xb = XBRLS.from_filings([f]) 
                #xb = XBRL.from_filing(f)  # preferred if available
            except Exception:
                xb = XBRLS.from_filings([f])  # fallback: one-at-a-time batch

            # determine period end (prefer DEI, fallback filing_date)
            try:
                period_end = pd.to_datetime(xb.dei.document_period_end_date).date()
            except Exception:
                period_end = pd.to_datetime(f.filing_date).date()

            # extract statements -> DataFrames (rows: periods, cols: items)
            stmts = []
            for tag, getter in [
                ("IS", xb.statements.income_statement),
                ("CF", xb.statements.cashflow_statement),
                ("BS", xb.statements.balance_sheet),
            ]:
                try:
                    df = getter().to_dataframe()
                    if df is None or df.empty:
                        continue
                    
                    wide = _pivot_statement(df.T)
                    if wide.shape[0] > 0: 
                        wide["filing_date"] = pd.to_datetime(getattr(f,"filing_date",None))
                        wide["accession_no"] = getattr(f, "accession_no", None)
                        wide["form"]         = getattr(f, "form", None)
                        output[tag].append(wide)
                   
                    
                    
                    
                    stmts.append(tag)
                except Exception:
                    output[tag] = None
                    continue

            # skip silently if no statements parsed (e.g., no XBRL)
            if not stmts:
                continue

        except Exception:
            # skip filings that fail to parse
            continue
    
    saveAccountingData(output,base_path)
    

    print(f"Saved {ticker} to {base_path}")

def GetAccountingData(ticker: str, howFarBack, base_dir: Optional[str] = None):
    """
    Pull both 10-Q and 10-K (last `howFarBack` each), batch-parse with XBRLS.from_filings,
    then save ONE file per statement via your existing GetAccountingDict + saveAccountingData.
    """
    c = Company(ticker)
    base_dir = base_dir or BASE_DIR
    base_path = os.path.join(base_dir, ticker)

    Time_Frame = howFarBack

    # NEW (1): fetch 10-Q **and** 10-K so you get Q1–Q3 (10-Q) and Q4 (10-K)
    filings_q = list(c.get_filings(form="10-Q").latest(Time_Frame, paginate=True))
    filings_k = list(c.get_filings(form="10-K").latest(Time_Frame, paginate=True))

    # NEW (2): merge, de-duplicate by accession_no, and sort by filing_date
    #          (keeps your batch flow intact while avoiding duplicates)
    filings = sorted(
        {f.accession_no: f for f in filings_q + filings_k}.values(),
        key=lambda f: f.filing_date
    )

    # NEW (3, optional but safe): drop very old, non-XBRL era filings (pre-2011) to reduce parse errors
    #     Comment out if you want to try parsing everything.
    filings = [f for f in filings if pd.to_datetime(f.filing_date) >= pd.Timestamp("2011-01-01")]

    try:
        # unchanged: you used this; keep to avoid side effects elsewhere
        industry = c.data.industry

        # unchanged: your original batch parse + pivot logic
        df_dict = GetAccountingDict(filings)

        # unchanged: single CSV per statement
        saveAccountingData(df_dict, base_path)
        print(f"Saved {ticker} to {base_path}")
    except Exception as e:
        # tiny improvement: surface the error (helps debug missing XBRL, etc.)
        print(f"{ticker}: failed to parse/save ({e})")
    

from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def Main_Multi():
    email = "magnus@pagnus.com"
    set_identity(email)
    base_dir =BASE_DIR
    tickers = GetAllTickers(base_dir)
    tickers = tickers["ticker"][1500:2250]
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(fetch_one, t,base_dir): t for t in tickers}
        done = 0
        for fut in as_completed(futures):
            tkr, status = fut.result()
            done += 1
            if status != "ok":
                print(f"Error fetching {tkr}: {status}")
            if done % 50 == 0:
                print(f"{done}/{len(tickers)} completed")

    print(f"Elapsed: {time.time()-t0:.1f}s")
    

def fetch_one(tkr,base_dir):
    
    try:
        GetAccountingData_Redux(tkr, 50,base_dir)
        return (tkr,"ok")
    except Exception as e:
        return (tkr,f"err: {e}")





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
    for ticker in tickers[:1000]:
        
        try:
            GetAccountingData_Redux(ticker, 50, base_dir)
        except:
            print(f"Error fetching {ticker}")

if __name__ == "__main__":
    Main_Multi()
    