# -*- coding: utf-8 -*-
"""
Created on Sun Sep 14 07:48:06 2025

@author: lambe
"""

import pandas as pd



if __name__=="__main__":
    
    path = r"D:\code\SEC_Fundamentals\sector_map.csv"
    
    df = pd.read_csv(path)
    
    df = df.set_index("ticker")
    
    df = df["sector"]
    
    d_df = df.to_dict()
    
    print(d_df["AAPL"])