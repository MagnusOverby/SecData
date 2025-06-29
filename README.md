# SecData

Utilities for downloading and processing financial statements from the SEC.

## Prerequisites

Install Python 3 and the required packages:

```bash
pip install -r requirements.txt
```

## Generating CSV statements

1. **GetSPX_tickers.py** downloads a list of tickers using the SEC JSON endpoint and saves `allTickers.csv`.
2. **GetData.py** iterates through tickers and downloads quarterly filings using the `edgar` package. For each ticker a folder is created containing `incomeStatement.csv`, `balanceSheet.csv`, and `cashflowStatement.csv`.
3. **OrderDataFrame.py** standardizes the raw statements and produces the consolidated files in `summary_statement/` (`income_statement.csv`, `balance_sheet.csv`, `cashflow_statement.csv`).

## Checking the output

Run `outputchecks_generated.py` from the repository root after generating the summary CSVs:

```bash
python outputchecks_generated.py
```

This script validates that the data in the CSV files conforms to expected formats.
