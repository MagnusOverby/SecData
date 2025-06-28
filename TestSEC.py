import os
import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
from sec_edgar_downloader import Downloader

# Install requirements:
# pip install sec-edgar-downloader beautifulsoup4 lxml pandas python-xbrl

# Configure your SEC-compliant User-Agent info here:
COMPANY_NAME = "Your Company or App Name"
EMAIL_ADDRESS = "your.email@domain.com"
addl = "D:\\code\\SEC_Fundamentals\\" # Not a good solution. fix it...


def download_10q_filings(ticker, num_filings=4, download_dir="edgar_data"):
    """
    Download the latest `num_filings` 10-Q filings for `ticker`.
    Returns the local directory containing downloaded filings.
    """
    dl = Downloader(COMPANY_NAME, EMAIL_ADDRESS, download_dir)
    ticker = ticker.upper()
    dl.get("10-Q", ticker, limit=num_filings)
    return os.path.join(download_dir, "sec-edgar-filings", ticker, "10-Q")


def find_xbrl_instance_file(filing_folder):
    """
    Locate the XBRL instance document. First look for standalone .xml files,
    then fall back to streaming out of full_submission.txt without regex.
    """
    # 1) Look for standalone .xml instance files
    for root, _, files in os.walk(filing_folder):
        for fname in files:
            if fname.endswith('.xml') and 'cal' not in fname and 'def' not in fname:
                return os.path.join(root, fname)

    # 2) Fallback: stream parse full_submission.txt
    txt_path = os.path.join(filing_folder, 'full-submission.txt')
    if os.path.exists(txt_path):
        try:
            xml_lines = []
            recording = False
            with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if not recording:
                        if line.lstrip().startswith('<?xml'):
                            recording = True
                            xml_lines.append(line)
                    else:
                        xml_lines.append(line)
                        if '</xbrli:xbrl>' in line:
                            break
            if xml_lines:
                xml_str = ''.join(xml_lines)
                out_path = os.path.join(filing_folder, 'instance.xml')
                with open(out_path, 'w', encoding='utf-8') as outf:
                    outf.write(xml_str)
                return out_path
        except Exception:
            pass
    return None


def parse_xbrl_xml(path):
    """
    Parse an XBRL instance file robustly with lxml, using a recovering XMLParser.
    Flattens all namespaced elements into a simple tag→text dict.
    """
    from lxml import etree
    # Use recover to handle non-well-formed wrappers or stray tokens
    parser = etree.XMLParser(recover=True, ns_clean=True, encoding='utf-8')
    try:
        tree = etree.parse(path, parser)
    except Exception as e:
        raise RuntimeError(f"Failed to parse XML instance at {path}: {e}")
    root = tree.getroot()
    xbrl_dict = {}
    # Iterate every element, strip namespace, capture text
    for el in root.iter():
        tag = el.tag
        if isinstance(tag, str) and '}' in tag:
            tag = tag.split('}', 1)[1]
        text = el.text.strip() if el.text and el.text.strip() else None
        if text is not None:
            xbrl_dict[tag] = text
    return xbrl_dict


def extract_income_items(xbrl_dict):
    """
    Extract key income statement items from parsed XBRL dict.
    """
    tags = {
        'Revenue': ['Revenues', 'SalesRevenueNet'],
        'COGS': ['CostOfGoodsSold'],
        'OperatingIncome': ['OperatingIncomeLoss'],
        'Capex': ['CapitalExpenditures'],
        'InterestExpense': ['InterestExpense'],
        'ExtraordinaryItems': ['ExtraordinaryItems'],
        'NetIncome': ['NetIncomeLoss']
    }
    row = {}
    for key, candidates in tags.items():
        for tag in candidates:
            if tag in xbrl_dict:
                row[key] = xbrl_dict[tag]
                break
        else:
            row[key] = None
    return row


def build_income_statements(ticker, num_filings=4):
    """
    Download, parse, and compile income statements for a given ticker.
    Returns two dicts:
      fundamentals[ticker][filing_date] = full XBRL dict
      IncomeStatement[ticker][filing_date] = pandas.DataFrame of key items
    """
    base_dir = download_10q_filings(ticker, num_filings)
    fundamentals = {ticker: {}}
    IncomeStatement = {ticker: {}}

    for filing in sorted(os.listdir(base_dir)):
        folder = os.path.join(base_dir, filing)
        xml_path = find_xbrl_instance_file(folder)
        if not xml_path:
            continue
        xbrl_data = parse_xbrl_xml(xml_path)
        date = xbrl_data.get('DocumentPeriodEndDate')
        fundamentals[ticker][date] = xbrl_data
        items = extract_income_items(xbrl_data)
        df = pd.DataFrame([items], index=[date])
        IncomeStatement[ticker][date] = df

    return fundamentals, IncomeStatement


if __name__ == '__main__':
    ticker_input = "AAPL"
    fund, inc = build_income_statements(ticker_input, num_filings=4)
    for date, df in inc[ticker_input].items():
        print(f"\nIncome Statement for {ticker_input} on {date}:")
        print(df)
