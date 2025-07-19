import os
import pandas as pd
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt

# Base directory for CSV files. Override with SEC_FUNDAMENTALS_DIR
BASE_DIR = os.environ.get('SEC_FUNDAMENTALS_DIR', r'D:\code\SEC\SecData')

def GetDataFromFiles(base_path: str | None = None):
        base_path = base_path or BASE_DIR
        tickers = [name for name in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, name))]
    
        # Dictionary: {ticker: {'balanceSheet': df, ...}}
        data = {}
    
        # Counters to collect column frequencies
        incomeStatement_columns = Counter()
        balanceSheet_columns = Counter()
        cashflowStatement_columns = Counter()
    
        for ticker in tickers:
            folder = os.path.join(base_path, ticker)
            data[ticker] = {}
            for statement in ["balanceSheet", "cashflowStatement", "IncomeStatement"]:
                fpath = os.path.join(folder, f"{statement}.csv")
                if os.path.exists(fpath):
                    df = pd.read_csv(fpath)
                    data[ticker][statement] = df
                    # Count column frequencies
                    if statement == "IncomeStatement":
                        incomeStatement_columns.update(df.columns)
                    elif statement == "balanceSheet":
                        balanceSheet_columns.update(df.columns)
                    elif statement == "cashflowStatement":
                        cashflowStatement_columns.update(df.columns)
    
        # Print or save column frequency dicts
        
        return data,[incomeStatement_columns,balanceSheet_columns,cashflowStatement_columns]



def fuzzy_map_col(col, reverse_map):
    
    percent_match = 0.7
    col_lower = col.lower()
    # 1. Try exact match first
    if col_lower in reverse_map:
        return reverse_map[col_lower]
    # 2. Try fuzzy/substring match basically we are checking, if either the first 8 are the same or if 70% matches, which ever is longer.
    for alias, std_key in reverse_map.items():
        # Require at least 70% of alias length as a prefix match (tweakable)
        if col_lower.startswith(alias[:max(10, int(len(alias)*percent_match))]):
            return std_key
        if alias in col_lower:
            return std_key
    return "other"  # if no match we need to return other.
    
def ReverseMap(statementMap):
    reverse_map = {}
    for std_key, aliases in statementMap.items():
        for alias in aliases:
            reverse_map[alias.lower()] = std_key
    
    return reverse_map
        
def IS_Hard_Mapping():
    INCOME_STATEMENT_HEADER_MAP = {
    "date":["date"],
    "TotalRevenue": [
        "Revenue", 
        "Total revenue", 
        "Net sales", 
        "Total revenues", 
        "Net revenues", 
        "Sales", 
        "Total net sales"
    ],
    "CostOfRevenue": [
        "Cost of revenue", 
        "Cost of sales", 
        "Cost of goods sold", 
        "Cost of products sold",
        "Cost of sales, exclusive of depreciation and amortization",
        "Total operating expenses"
    ],
    "GrossProfit": [
        "Gross profit", 
        "Gross margin", 
        "Gross profit, total"
    ],
    "OperatingIncome": [
        "Operating income", 
        "Income from operations", 
        "Operating profit", 
        "Operating earnings", 
        "Income before interest and taxes", 
        "Earnings from operations"
    ],
    "NetIncome": [
        "Net income", 
        "Net earnings", 
        "Net income attributable to shareholders", 
        "Net income attributable to common stockholders", 
        "Net earnings attributable to common shareholders", 
        "Net profit"
    ],
    "EBIT": [
        "Earnings before interest and taxes", 
        "EBIT", 
        "Income before interest and income taxes"
    ],
    "EBITDA": [
        "EBITDA", 
        "Earnings before interest, taxes, depreciation and amortization"
    ],
    "InterestExpense": [
        "Interest expense", 
        "Interest and debt expense", 
        "Interest expense, net", 
        "Interest and other financial charges"
    ],
    "InterestIncome": [
        "Interest income", 
        "Interest and dividend income"
    ],
    "ResearchAndDevelopment": [
        "Research and development", 
        "R&D expense", 
        "Research, development and engineering", 
        "Research and development expense"
    ],
    "SGA": [
        "Selling, general and administrative", 
        "General and administrative", 
        "Selling and administrative expense", 
        "Sales and marketing", 
        "Marketing, general and administrative", 
        "General, administrative and other"
    ],
    "IncomeTaxExpense": [
        "Income tax expense", 
        "Provision for income taxes", 
        "Income tax provision", 
        "Provision for taxes on income", 
        "Taxes on income"
    ],
    "EPSBasic": [
        "Earnings per share—basic", 
        "Basic earnings per share", 
        "Net income per share—basic", 
        "Basic (in dollars per share)"
    ],
    "EPSDiluted": [
        "Earnings per share—diluted", 
        "Diluted earnings per share", 
        "Net income per share—diluted", 
        "Diluted (in dollars per share)"
    ],
    "SharesOutstandingBasic": [
        "Weighted average shares outstanding—basic", 
        "Basic (in shares)", 
        "Weighted-average basic shares outstanding (in shares)"
    ],
    "SharesOutstandingDiluted": [
        "Weighted average shares outstanding—diluted", 
        "Diluted (in shares)", 
        "Weighted-average diluted shares outstanding (in shares)"
    ],
    "DepreciationAmortization": [
            "Depreciation and amortization",
            "Depreciation, depletion and amortization",
            "Depreciation",
            "Amortization of intangible assets"
        ],
        "NonRecurringItems": [
            "Restructuring charges",
            "Asset impairment charges",
            "Gain (loss) on disposal of assets",
            "Other income (expense), net"
        ],
        "TaxBenefit": [
            "Income tax benefit",
            "Benefit from income taxes"
        ],
        "MinorityInterest": [
            "Net income attributable to noncontrolling interests",
            "Minority interest in net income"
        ],
        # Handle negative values properly
        "TaxExpenseCredit": [  # More comprehensive than just expense
            "Income tax expense",
            "Provision for income taxes",
            "Provision for (benefit from) income taxes",
            "Income tax provision",
            "Income tax benefit",
            "Benefit from income taxes"
        ]
    # Add more as you need for your KPIs
}
    return INCOME_STATEMENT_HEADER_MAP

def BS_Hard_Mapping():
    balance_sheet_mapping = {
    # General Name      # Possible SEC/XBRL/column names (hard mapping)
    "date":["date"],
    "CashAndCashEquivalents": [
        "Cash and cash equivalents", "Cash and Cash Equivalents",
        "Cash", "Cash equivalents"
    ],
    "ShortTermInvestments": [
        "Short-term investments", "Short Term Investments", "Marketable securities, current"
    ],
    "AccountsReceivable": [
        "Accounts receivable, net", "Accounts Receivable", "Receivables, net"
    ],
    "Inventory": [
        "Inventories", "Inventory", "Total inventories"
    ],
    "PrepaidExpenses": [
        "Prepaid expenses", "Prepaid Expenses and Other Current Assets", "Prepaid expenses and other assets"
    ],
    "OtherCurrentAssets": [
        "Other current assets", "Other Current Assets"
    ],
    "TotalCurrentAssets": [
        "Total current assets", "Current Assets"
    ],
    "PropertyPlantEquipmentNet": [
        "Property, plant and equipment, net", "Property, plant and equipment—net",
        "Property and equipment, net", "Property and Equipment, net"
    ],
    "Goodwill": [
        "Goodwill"
    ],
    "IntangibleAssetsNet": [
        "Intangible assets, net", "Intangible Assets, net"
    ],
    "OtherNoncurrentAssets": [
        "Other noncurrent assets", "Other Noncurrent Assets", "Other assets"
    ],
    "TotalAssets": [
        "Total assets", "Assets"
    ],
    "AccountsPayable": [
        "Accounts payable", "Accounts Payable", "Payables"
    ],
    "AccruedExpenses": [
        "Accrued expenses", "Accrued Expenses and Other Current Liabilities", "Accrued liabilities"
    ],
    "ShortTermDebt": [
        "Short-term debt", "Short Term Debt", "Current portion of long-term debt"
    ],
    "OtherCurrentLiabilities": [
        "Other current liabilities", "Other Current Liabilities"
    ],
    "TotalCurrentLiabilities": [
        "Total current liabilities", "Current Liabilities"
    ],
    "LongTermDebt": [
        "Long-term debt", "Long Term Debt", "Long-term borrowings"
    ],
    "DeferredIncomeTaxes": [
        "Deferred income taxes", "Deferred Income Taxes", "Deferred tax liabilities"
    ],
    "OtherNoncurrentLiabilities": [
        "Other noncurrent liabilities", "Other Noncurrent Liabilities"
    ],
    "TotalLiabilities": [
        "Total liabilities", "Liabilities"
    ],
    "CommonStock": [
        "Common stock", "Common Stock", "Common shares"
    ],
    "AdditionalPaidInCapital": [
        "Additional paid-in capital", "Paid-in capital"
    ],
    "RetainedEarnings": [
        "Retained earnings", "Retained Earnings"
    ],
    "AccumulatedOtherComprehensiveIncome": [
        "Accumulated other comprehensive income (loss)", "Accumulated Other Comprehensive Income (Loss)"
    ],
    "TreasuryStock": [
        "Treasury stock", "Treasury Stock"
    ],
    "TotalEquity": [
        "Total stockholders’ equity", "Total shareholders’ equity", "Stockholders’ equity", "Shareholders’ equity", "Total equity"
    ],
    "TotalLiabilitiesAndEquity": [
        "Total liabilities and stockholders’ equity", "Total liabilities and shareholders’ equity", "Total liabilities and equity"
    ],
    "LongTermInvestments": [
            "Long-term investments",
            "Investments in equity method investees",
            "Available-for-sale securities, noncurrent"
        ],
        "DeferredTaxAssetsNoncurrent": [
            "Deferred tax assets, noncurrent",
            "Deferred income tax assets"
        ],
        "NoncontrollingInterest": [
            "Noncontrolling interests",
            "Minority interest"
        ],
        "PreferredStock": [
            "Preferred stock",
            "Preferred shares"
        ],
        "ShareBasedCompensation": [
            "Share-based compensation",
            "Stock compensation"
        ]
    
    }
    return balance_sheet_mapping

def CS_Hard_Mapping():
    cashflow_statement_mapping = {
    "date":["date"],
    "NetCashProvidedByOperatingActivities": [
        "Net cash provided by operating activities",
        "Net cash used in operating activities",
        "Net cash provided by (used in) operating activities",
        "Net cash from operating activities"
    ],
    "NetCashProvidedByInvestingActivities": [
        "Net cash provided by investing activities",
        "Net cash used in investing activities",
        "Net cash provided by (used in) investing activities",
        "Net cash from investing activities"
    ],
    "NetCashProvidedByFinancingActivities": [
        "Net cash provided by financing activities",
        "Net cash used in financing activities",
        "Net cash provided by (used in) financing activities",
        "Net cash from financing activities"
    ],
    "DepreciationAmortization": [
        "Depreciation and amortization",
        "Depreciation", "Amortization"
    ],
    "StockBasedCompensation": [
        "Stock-based compensation", "Share-based compensation"
    ],
    "DeferredIncomeTaxes": [
        "Deferred income taxes", "Deferred tax (benefit) provision", "Deferred tax expense"
    ],
    "ChangeInAccountsReceivable": [
        "Accounts receivable", "Change in accounts receivable", "Decrease (increase) in accounts receivable"
    ],
    "ChangeInInventory": [
        "Inventories", "Change in inventories", "Decrease (increase) in inventories"
    ],
    "ChangeInAccountsPayable": [
        "Accounts payable", "Change in accounts payable", "Increase (decrease) in accounts payable"
    ],
    "ChangeInAccruedExpenses": [
        "Accrued expenses", "Change in accrued expenses", "Increase (decrease) in accrued expenses"
    ],
    "CapitalExpenditures": [
        "Purchases of property and equipment",
        "Capital expenditures", "Additions to property, plant and equipment"
    ],
    "ProceedsFromIssuanceOfDebt": [
        "Proceeds from issuance of long-term debt", "Proceeds from issuance of debt"
    ],
    "RepaymentsOfDebt": [
        "Repayments of long-term debt", "Repayment of debt", "Payments of long-term debt"
    ],
    "ProceedsFromIssuanceOfStock": [
        "Proceeds from issuance of common stock", "Proceeds from issuance of stock"
    ],
    "RepurchaseOfStock": [
        "Repurchase of common stock", "Repurchase of stock", "Purchase of treasury stock"
    ],
    "DividendsPaid": [
        "Dividends paid", "Dividends paid to shareholders", "Dividends paid to stockholders"
    ],
    "EffectOfExchangeRateChangesOnCash": [
        "Effect of exchange rate changes on cash and cash equivalents",
        "Effect of exchange rates on cash", "Effect of exchange rate changes on cash"
    ],
    "NetIncreaseDecreaseInCash": [
        "Net increase (decrease) in cash and cash equivalents",
        "Net increase in cash and cash equivalents",
        "Net decrease in cash and cash equivalents"
    ],
    "CashAndCashEquivalentsAtBeginningOfPeriod": [
        "Cash and cash equivalents at beginning of period", "Cash and cash equivalents, beginning of period"
    ],
    "CashAndCashEquivalentsAtEndOfPeriod": [
        "Cash and cash equivalents at end of period", "Cash and cash equivalents, end of period"
    ]
    }
    return cashflow_statement_mapping

# Fill this out.
"""

This is how it should be used :
    aggregator = SECDataAggregator(base_path, {
    "income": income_statement_mapping,
    "balance": balance_sheet_mapping,
    "cashflow": cashflow_statement_mapping
})
aggregator.load_and_standardize()
df_balance = aggregator.get_balance_sheet()
df_income = aggregator.get_income_statement()
# Now easy to query or join as needed

So 1) read the files - > easy
2) Read all tickers in the data, for each extract the dataframe and standardize it.
3) add a column called "ticker"
4) add it to the main TS 
5) VICTORY!!!!!



"""


class SECDataAggregator:
    def __init__(self, base_path, mappings):
        self.base_path = base_path
        self.mappings = mappings
        self.balance_sheets = None
        self.income_statements = None
        self.cash_flow_statements = None
        
    
    
    def _standardize_columns(self, df, mapping):
        
        df = df.iloc[1:,:].copy()
        reverse_map = ReverseMap(mapping)
        all_col = list([x.lower() for x in df.columns])
        if all_col[0] =="unnamed: 0":
            all_col[0] = "date"
        df.columns =all_col 
        #=========== SET EVERYTHING TO NUMBERS ================ #
        df.iloc[:,1:] = df.iloc[:,1:].apply(lambda col: pd.to_numeric(col, errors='coerce'))
        df = df.fillna(0.0)        
        #========================================================#
    
        new_cols = [fuzzy_map_col(col, reverse_map).lower() for col in df.columns]
        adj_cols = list(new_cols)
        df.columns = adj_cols
       
        return df
    
    def standardize_date_column(self, df):
        """Standardize date formats commonly found in SEC filings"""
        if 'date' in df.columns:
            
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        return df
    
    
    def clean_numeric_data(self, df):
        """Clean numeric columns to handle SEC formatting quirks"""
        
        cols = df.shape[1]
        
        
        
        for i in range(0,cols):
            
            
            col = df.columns[i]
            
            if col != 'date' and col != 'ticker':
                # Remove parentheses and convert to negative
                df.iloc[:,i] = df.iloc[:,i].astype(str).str.replace(r'\((.*?)\)', r'-\1', regex=True)
                # Remove commas and dollar signs
                df.iloc[:,i] = df.iloc[:,i].str.replace(',', '').str.replace('$', '').str.replace('—', '0')
                # Convert to numeric
                df.iloc[:,i] = pd.to_numeric(df.iloc[:,i], errors='coerce')
        return df
    
    
    def detect_and_apply_scale(self, df, ticker):
        """Detect if numbers are in thousands/millions and normalize to actual values"""
        # This would require reading the scale information from the original filing
        # For now, implement a heuristic based on magnitude
        numeric_cols = df.select_dtypes(include=[np.number]).columns
    
        for col in numeric_cols:
            if col not in ['date', 'ticker']:
                median_val = df[col].median()
                if median_val > 0:
                    if median_val < 1000000:  # Likely in thousands
                        df[col] = df[col] * 1000
                    elif median_val > 1000000000:  # Likely in millions already
                        df[col] = df[col] * 1000000
        
        return df
    

    def load_and_standardize(self, statement: str):
        """
        Loads and remaps all tickers for the specified statement type.
        statement: 'income', 'balance', or 'cashflow'
        Returns the combined standardized DataFrame with a 'ticker' column.
        """
        data = []
        mapping = self.mappings[statement]
        tickers = [name for name in os.listdir(self.base_path) if os.path.isdir(os.path.join(self.base_path, name))]
        file_name_map = {
            "income": "IncomeStatement.csv",
            "balance": "balanceSheet.csv",
            "cashflow": "cashflowStatement.csv"
        }
        file_name = file_name_map[statement]
    
        for ticker in tickers:
            fpath = os.path.join(self.base_path, ticker, file_name)
            if os.path.exists(fpath):
                df = pd.read_csv(fpath)
                
                #Some side bar stuff to get the date columns  there
                cols = list(df.columns)
                cols[0] = "date"
                df.columns = [x.lower() for x in cols]
                
                df = df.iloc[1:,:]
                
                df = self.clean_numeric_data(df)
                
                df_t = self._standardize_columns(df, mapping)
                
                df_t = df_t.set_index("date")
                
                df_t = df_t.T.groupby(level=0).sum().T
                
                df_t =df_t.reset_index()
                
                #df_t = self.standardize_date_column(df)
                
                #
                
                df_t['ticker'] = ticker
                df_t = self.detect_and_apply_scale(df_t,ticker)
                df_t = self.standardize_date_column(df_t)
                data.append(df_t)
        if data:
            result = pd.concat(data, ignore_index=True,axis=0,join="outer")
        else:
            result = pd.DataFrame()
        
        # Save result to appropriate attribute
        if statement == 'income':
            self.income_statements = result
        elif statement == 'balance':
            self.balance_sheets = result
        elif statement == 'cashflow':
            self.cash_flow_statements = result
        
        return result

    def get_income_statement(self):
            return self.income_statements
        
  

def main(df2):
    df2 = data["MSFT"]["IncomeStatement"]
    df = data["MSFT"]["IncomeStatement"]
    df.columns = [fuzzy_map_col(c,ReverseMap(IS_Hard_Mapping())) for c in df.columns]
    return df


def accounting_checks(df_income):
    
    df = df_income
    
    df['netincome_calc'] = (df['operatingincome']
                        - df['interestexpense']
                        + df['interestincome']
                        - df['incometaxexpense']
                        + df['other'].fillna(0))
    mismatch_net = (df['netincome'] - df['netincome_calc']).abs() > 1e3
    print(f"Rows with Net Income mismatch: {mismatch_net.sum()}")



if __name__=="__main__":

    data, col_freq = GetDataFromFiles(BASE_DIR)
    base_path = BASE_DIR
    IS = col_freq[0]

    mappings = {
        'income': IS_Hard_Mapping(),
        'balance': BS_Hard_Mapping(),
        'cashflow': CS_Hard_Mapping() }

    aggregator = SECDataAggregator(base_path, mappings)
    df_income = aggregator.load_and_standardize('income')
    df_balance = aggregator.load_and_standardize("balance")
    df_cash = aggregator.load_and_standardize("cashflow")

    path = os.path.join(base_path, "summary_statement")
    #==================== PRINT THE DATA FRAMES TO CSV FILES =====================#
    df_income.to_csv(os.path.join(path, "income_statement.csv"))
    df_balance.to_csv(os.path.join(path, "balance_sheet.csv"))
    df_cash.to_csv(os.path.join(path, "cashflow_statement.csv"))
