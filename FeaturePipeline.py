# -*- coding: utf-8 -*-
"""
Created on Mon Jul 14 11:45:22 2025

@author: magnu
"""
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
import os



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


class DataLoader:
    """Loads balance sheet data from CSV files"""
    def __init__(self, filepath: str,filenmn):
        self.filepath = filepath
        self.filenmn = filenmn
        self.load_data()

    def load_data(self) -> {}:
        
        path = [os.path.join(self.filepath,x) for x in self.filenmn]
        dataframes = {}
        for x,y in zip(self.filenmn,path):
            dataframes[x.repalce(".csv","")]=pd.read_csv(y)
        
        self.data = dataframes
        return self.data
     

class TimeSeriesPreprocessor(BaseEstimator, TransformerMixin):
    """Preprocesses time series data (e.g., sorting, handling dates, etc.)"""
    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        
        
        X = normalize_by_ticker_baseline(CheckNumberOfColumns(X))
        
        return X
        
        # now I would have to normalize across tickers.
        # 
        
        """
        1) group by tickers
        2) now we sort by dates
        3) 
        
        """        
        


#================ CONSTRUCT FACTORS ================#
"""






"""

class FactorConstructor(BaseEstimator, TransformerMixin):
    """Constructs financial factors from balance sheet data"""
    def __init__(self, factors: list):
        self.factors = factors

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        pass


class TimeSeriesNormalizer(BaseEstimator, TransformerMixin):
    """Normalizes factors while respecting time-series constraints (no look-ahead bias)"""
    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        pass
    

class FactorPipeline:
    """Main pipeline to manage data loading, factor construction, and normalization"""
    def __init__(self, loader: DataLoader, preprocessors: list, factor_constructor: FactorConstructor, normalizer: TimeSeriesNormalizer):
        self.loader = loader
        self.preprocessors = preprocessors
        self.factor_constructor = factor_constructor
        self.normalizer = normalizer

    def run_pipeline(self) -> pd.DataFrame:
        pass



if __name__=="__main__":
    
    
    path  = r"D:\code\SEC\SecData\summary_statement"
    flnmn = ["balacne_sheet.csv","cashflow_statement.csv","income_statement.csv"]
    DL = DataLoader