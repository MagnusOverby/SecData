# -*- coding: utf-8 -*-
"""
Created on Sat May  3 17:40:53 2025

@author: lambe
"""
from edgar import *
from edgar.xbrl import *
import pandas as pd
from typing import Optional
import numpy as np
import os

# Default directory for reading/writing data. Can be overridden by
# the SEC_FUNDAMENTALS_DIR environment variable.
BASE_DIR = os.environ.get('SEC_FUNDAMENTALS_DIR', r'D:\code\SEC_Fundamentals')

def get_income_statement_edgartools(ticker, form_type="10-Q"):
    """
    Fetches and returns the income statement as a pandas DataFrame using edgartools.
    """
    client = EdgarClient()
    # Grab all financials, filter for income statement, then pivot
    df = client.get_financials(ticker, form_type=form_type)
    inc = df[df['statement'] == 'income']
    return inc.pivot(index='period_end', columns='account', values='value')


def BuildDataFrames(df_input:pd.DataFrame)->(pd.DataFrame,pd.DataFrame):
    
    df1 = df_input.drop("concept",axis=1)
    df1 = df1.set_index("label")
    df1 = df1.T
    df2 = df_input.loc[:,["concept","label"]]
    df2 = df2.set_index("label")
    return df1,df2
    

def get_income_dataframe(ticker:str):
    
    c = Company(ticker)
    
    Time_Frame = 10
    
    industry = c.data.industry
    filings = c.get_filings(form="10-Q").latest(5)
    
    if filings is None:
        return [],[],""
    
    # here we need some logic to check if they are foreign. #
    
    
    print(ticker)
    data_output,concept_mapping = {},{}
    try:
        xbs = XBRLS.from_filings(filings)
    
        sts = xbs.statements.income_statement()
        data_output["income_statement"],concept_mapping["income_statement"] = BuildDataFrames(sts.to_dataframe())
        sts = xbs.statements.cashflow_statement()
        data_output["cashflow_statement"],concept_mapping["cashflow_statement"] = BuildDataFrames(sts.to_dataframe()) 
        sts = xbs.statements.balance_sheet()
        data_output["balance_sheet"],concept_mapping["balance_sheet"] = BuildDataFrames(sts.to_dataframe())
    
    except Exception as e:
        print(f"Error getting ticker: {e}")
    
    return data_output,concept_mapping,industry
    
 
    
def get_sales_marketing_expense(row: pd.Series) -> Optional[float]:
    """
    Returns the Sales & Marketing expense from a single income-statement row.
    
    Preference order:
      1. "Sales and marketing"
      2. "Selling, General and Administrative Expense" (proxy)
    
    Args:
        row: A pandas Series indexed by label (one period's data).
    
    Returns:
        The expense as a float, or None if neither field is present.
    """
    if "Sales and marketing" in row.index:
        return float(row["Sales and marketing"])
    
    elif "Selling, General and Administrative Expense" in row.index:
        return float(row["Selling, General and Administrative Expense"])
    
    elif "Selling, general and administrative" in row.index:
        return float(row["Selling, general and administrative"])
    
    return None

def getOperatingIncome(row:pd.Series)->Optional[float]:

    if "Income (loss) from operations" in row.index:
            return row["Income (loss) from operations"]
    
    # 2. Check "Operating Income"
    if "Operating Income" in row.index:
            return row["Operating Income"]
    
    # 3. Proxy calculation
    try:
            gp = row.get("Gross Profit", 0)
            sga = row.get("Selling, General and Administrative Expense", 0)
            rnd = row.get("Research and Development Expense", 0)
            return gp - sga - rnd
    except KeyError:
            return None  # In case all components are missing
     
def getReveue(df_in:pd.Series)->Optional[float]:
    
    if "Revenue" in df_in.index:
        return df_in["Revenue"]
    elif "Net sales" in df_in.index:
        return df_in["Net sales"]
    else:
        return df_in["Total sales"]

def getOperatingCashflow(row: pd.Series, row2: pd.Series) -> Optional[Union[float, int]]:
    """
    Returns Operating Cash Flow from a cashflow statement row.
    Preference order:
    1. Direct: "Net cash provided by operating activities"
    2. Inverted: "Net cash used in operating activities"
    3. Proxy: Constructed using key non-cash and working capital adjustments (requires net_income)
    """
    
    # 1. Direct value
    if "Net cash provided by operating activities" in row:
        return row["Net cash provided by operating activities"]

    # 2. Inverted value
    if "Net cash used in operating activities" in row:
        return -row["Net cash used in operating activities"]

    # 3. Proxy this is pretty crap. Should not do it.
    if row2 is not None:
        net_income = row2.get("Net Income",0) 
        d_and_a = row2.get("Depreciation, amortization, and impairment", 0)
        sbc = row2.get("Share-based compensation", 0)
        wc = row2.get("Changes in operating assets and liabilities, excluding effect of acquisitions, divestitures, and currency", 0)
        deferred_tax = row2.get("Deferred income taxes, net", 0)
        equity_income = row2.get("Equity in (income)/loss of affiliated companies", 0)
        other = row2.get("Other, net", 0)

        return net_income + d_and_a + sbc + wc + deferred_tax + equity_income + other

    # 4. No viable data
    return None

def getTotalEquity(row: pd.Series) -> Optional[Union[float, int]]:
    """
    Returns total shareholders' equity from a balance sheet row.
    Checks common label variations.
    """
    possible_labels = [
        "Total Stockholders' Equity",
        "Total shareholders' equity",
        "Stockholders' equity",
        "Total equity",
        "Shareholders’ equity",  # note typographic quote variant
    ]

    for label in possible_labels:
        if label in row:
            return row[label]

    return None

def getCurrentLongTermDebt(row: pd.Series) -> Optional[float]:
    """
    Returns the current portion of long-term debt from a balance sheet row.
    Checks common label variations.
    """
    possible_labels = [
        "Current portion of long-term debt",
        "Current maturities of long-term debt",
        "Short-term portion of long-term borrowings",
        "Short-term debt"  # may include other items
    ] 
    
    for label in possible_labels:
        if label in row:
            return row[label]
    
    # Use keywords !!
    
    key_word = ["long-term debt","long term debt"]
    
    for label in row.index:  
        l_low = label.lower()
        for k in key_word:
            if k in l_low:
                return row[label]
            
    
    

    return None

def CheckLatest(ticker_data:{}) -> str:
    
    last_entry = []
    for v in ticker_data.values():
    
        last_entry.append(v.index.max())
        
    return last_entry
    

"""
This will have to be refined on an industry basis.

Will have to transform this to a_over time metric


What to do:
    
    1) Handle missing inputs. Balancesheets are not always availalbe in every 10-Q
    2) Create a function that takes the below and projects it into a time series. So that we can see how these figures have looked over time.
    3) Get ahold of a bunch of tickers to test this on (could use Yahoo finance or whatever...)
    4) Define other more useful metrics.
    
Predictor:
    
    A) How well does these metrics predict:
    
    1) Net Income growth (this will be the key metric)

"""

def accruals_ratio(IS, BS_this, BS_prev):
    # Use FCF proxy from previous function or use accruals_balance_sheet
    accruals = accruals_balance_sheet(BS_this, BS_prev)
    avg_assets = 0.5 * (BS_this['Total Assets'] + BS_prev['Total Assets'])
    return accruals / avg_assets if avg_assets != 0 else None

def accruals_balance_sheet(BS_this, BS_prev):
    delta_ca = BS_this['Total Current Assets'] - BS_prev['Total Current Assets']
    delta_cl = BS_this['Total Current Liabilities'] - BS_prev['Total Current Liabilities']
    delta_cash = BS_this['Cash and Cash Equivalents'] - BS_prev['Cash and Cash Equivalents']
    delta_debt = (BS_this['Long-Term Debt'] + BS_this['Current portion of long-term debt']) - \
                 (BS_prev['Long-Term Debt'] + BS_prev['Current portion of long-term debt'])

    accruals = (delta_ca - delta_cash) - (delta_cl - delta_debt)
    return accruals

def GetPPE(row):
    
    runner = 0 
    for c in row.index:
        if "Property and equipment" in c:
            try:
                runner+=int(row.loc[c])
            except:
                pass

    return runner
        
def calculate_fcf_conversion(IS, BS_this, BS_prev):
    # IS: Income Statement row (quarter)
    # BS_this: Current Balance Sheet
    # BS_prev: Previous Quarter Balance Sheet

    # 1. Net Income
    net_income = IS['Net Income']

    # 2. Estimate Capex as negative change in PP&E
    delta_ppe = GetPPE(BS_this) - GetPPE(BS_prev)
    capex_proxy = -delta_ppe if delta_ppe < 0 else 0  # Only if PP&E increases (new investments)

    # 3. FCF Proxy
    fcf_proxy = net_income + capex_proxy

    # 4. Conversion Ratio
    fcf_conversion = fcf_proxy / net_income if net_income != 0 else None
    return fcf_conversion

def GetReceivables(row):
    
    runner = 0 
    for c in row.index:
        if "'receivables, net'" in c:
            try:
                runner+=int(row.loc[c])
            except:
                pass

    return runner

def receivables_growth(BS_this, BS_prev, IS):
    delta_receivables = GetReceivables(BS_this)- GetReceivables(BS_prev)
    revenue = IS['Revenue']
    return delta_receivables / revenue if revenue != 0 else None

def Compute_Latest_QualityMetric(ticker_data,concep):
    
    
    latest_period = CheckLatest(ticker_data)
    
    return compute_quality_metrics(ticker_data,concep,latest_period)
    
def compute_quality_metrics(ticker_data,concep,latest_period):
    income = ticker_data["income_statement"]
    cashflow = ticker_data["cashflow_statement"]
    balance = ticker_data["balance_sheet"]
    
    
    # I could transform it 
    
    # Use latest available data
    
    ni = income.loc[latest_period[0]]["Net Income"]
    rev = getReveue(income.loc[latest_period[0]])
    gm = getOperatingIncome(income.loc[latest_period[0]]) / rev
    sga = get_sales_marketing_expense(income.loc[latest_period[0]]) / rev

    ocf = getOperatingCashflow(cashflow.loc[latest_period[1]],income.loc[latest_period[0]])
    capex = cashflow.loc[latest_period[0]].get("Net cash used in investing activities", 0)
    fcf = ocf + capex #Basically capex is always a negative figure in the cashflow statement ?
    
    if fcf == ni:
        index_prev = list((balance.index)).index(latest_period[2])
        fcf_conversion = calculate_fcf_conversion(income.loc[latest_period[0]],balance.iloc[index_prev],balance.iloc[index_prev+1])        
    else:
        fcf_conversion = fcf / ni if ni else 0
    
    """
    How good of a proxy is really Net Cash used in Investing activites for Capex ? 
    """

    total_equity = getTotalEquity(balance.loc[latest_period[2]])
    invested_capital = total_equity + getCurrentLongTermDebt(balance.loc[latest_period[2]])

        # Ratios
   
    ocf_margin = ocf / rev if rev else 0
    roe = ni / total_equity if total_equity else 0
    roic = ni / invested_capital if invested_capital else 0
    
    
    index_prev_bs = list((balance.index)).index(latest_period[2])
    
    accr_bs = accruals_ratio(income.loc[latest_period[0]],balance.iloc[index_prev_bs],balance.iloc[index_prev_bs+1])
    
    rec_growth =receivables_growth(balance.iloc[index_prev_bs],balance.iloc[index_prev_bs+1],income.loc[latest_period[0]])
    
    return {
            "FCF/NI": fcf_conversion if fcf_conversion<1 else np.nan,
            "OCF Margin": ocf_margin,
            "ROE": roe,
            "ROIC": roic,
            "Gross Margin": gm,
            "SGA/Rev": sga,
            "accrual_ratio":accr_bs,
            "rec_growth": rec_growth
        }
    


def GetQualityScores(QualityData):
    
    quality_scores = {}
    
    for ticker, data in consumer_disc_data.items():
        metrics = compute_quality_metrics(data)
        if metrics:
            quality_scores[ticker] = metrics

    df_scores = pd.DataFrame(quality_scores).T
    return df_scores



def GetQualityMericsFromTickers(aTicker:list):
    
    ticker_data = {}
    QMetrics = {}
    concept = {}
    
    for ticker in aTicker:
        ticker_data[ticker],concept[ticker],industry = get_income_dataframe(ticker)
        
        if len(ticker_data[ticker])>0:
            QMetrics[ticker] = Compute_Latest_QualityMetric(ticker_data[ticker],concept[ticker])
            QMetrics[ticker]["industry"] = industry
    
    return QMetrics,ticker_data


def testRun(ticker):
    
    email = "magnus@pagnus.com"
    set_identity(email)
    
    #conDisc = ["ABNB","AMCR","AS","APTV","BBY","BROS","BURL","CCL","CHWY","CMG","CPNG","CVNA","DECK","DHI","DKNG","EBAY","F","EXPE","GME","GPC","H","HLT","HMC","IHG","IP","JD", "LULU","NKE"]   
    #conDisc = ["AS","APTV","BBY","BROS"]
    ratios,data = GetQualityMericsFromTickers(ticker)
    return ratios,data
    

def ReadSPXItems(base_dir: str | None = None):

    base_dir = base_dir or BASE_DIR
    path = os.path.join(base_dir, "allTickers.csv")
    df_ticker = pd.read_csv(path)
    return df_ticker


if __name__=="__main__":

    ticker = ReadSPXItems(BASE_DIR)
    r, d = testRun(ticker["ticker"].iloc[:10])
        
