# -*- coding: utf-8 -*-
"""
Created on Sat May 31 09:11:22 2025

@author: magnu
"""

import requests
import pandas as pd
import os

if __name__=="__main__":
    
    
    headers = {
    "User-Agent": "Magnus Overby lambert.overby@gmail.com"
        }
        
        # Fetch the JSON with the header
    resp = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=headers
        )
    mapping = resp.json()    




    df  = pd.DataFrame.from_dict(mapping,orient="index")
    
    path = os.getcwd()
    
    df_new = df.loc[:,["cik_str","ticker"]]
    df_new.to_csv(path+"\\allTickers.csv")