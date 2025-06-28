# -*- coding: utf-8 -*-
"""
Created on Sat May  3 14:00:50 2025

@author: lambe
"""

import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from sec_edgar_downloader import Downloader


def get_cik_mapping():
    """
    Fetch SEC ticker-to-CIK mapping.
    Returns a dict mapping ticker symbols to zero-padded CIK strings.
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    resp = requests.get(url)
    data = resp.json()
    return {v['ticker'].upper(): str(v['cik_str']).zfill(10) for v in data.values()}



if __name__=="__main__":
    CIK_MAP = get_cik_mapping()
    