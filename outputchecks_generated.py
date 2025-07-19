
import os
import pandas as pd
from typing import List, Tuple, Optional


def _find_column(df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
    """Return the first column containing any of the given patterns."""
    for col in df.columns:
        col_low = str(col).lower()
        for p in patterns:
            if p.lower() in col_low:
                return col
    return None


def check_balance_sheet(df: pd.DataFrame, tol: float = 1e-2) -> List[Tuple]:
    """Check the accounting identity: Assets = Liabilities  Equity."""
    assets_col = _find_column(df, ["totalassets"])
    liabilities_col = _find_column(df, ["totalliabilities"])
    equity_col = _find_column(
        df,
        [
            "totalstockholders' equity",
            "totalshareholders' equity",
            "shareholders' equity",
            "stockholders' equity",
            "totalequity",
        ],
    )
    liab_eq_col = _find_column(
        df,
        [
            "totalliabilitiesandstockholders' equity",
            "totalliabilitiesandshareholders' equity",
            "totalliabilitiesandequity",
        ],
    )

    errors = []
    if assets_col is None:
        return errors

    for idx, row in df.iterrows():
        assets = row.get(assets_col)
        if pd.isna(assets):
            continue
        if liab_eq_col and pd.notna(row.get(liab_eq_col)):
            diff = assets - row[liab_eq_col]
        elif liabilities_col and equity_col and pd.notna(row.get(liabilities_col)) and pd.notna(row.get(equity_col)):
            diff = assets - (row[liabilities_col] + row[equity_col])
        else:
            continue
        if abs(diff) > tol * max(abs(assets), 1):
            errors.append((idx, diff))
    return errors


def check_income_statement(df: pd.DataFrame, tol: float = 1e-2) -> List[Tuple]:
    """Check that Gross Profit roughly equals Revenue minus COGS."""
    revenue_col = _find_column(df, ["revenue", "sales"])
    cogs_col = _find_column(df, ["costofrevenue", "costofgoods", "costofsales"])
    gp_col = _find_column(df, ["grossprofit", "grossmargin"])
    errors = []
    if not (revenue_col and cogs_col and gp_col):
        return errors
    for idx, row in df.iterrows():
        rev = row.get(revenue_col)
        cogs = row.get(cogs_col)
        gp = row.get(gp_col)
        if pd.notna(rev) and pd.notna(cogs) and pd.notna(gp):
            diff = rev - cogs - gp
            if abs(diff) > tol * max(abs(rev), 1):
                errors.append((idx, diff))
    return errors


def check_cashflow(df: pd.DataFrame, tol: float = 1e-2) -> List[Tuple]:
    """Check that changes in cash equal sum of cash flow components."""
    op_col = _find_column(df, ["net cash provided by operating", "net cash used in operating"])
    inv_col = _find_column(df, ["net cash used in investing", "net cash provided by investing"])
    fin_col = _find_column(df, ["net cash provided by financing", "net cash used in financing"])
    change_col = _find_column(df, ["net increase", "net decrease", "change in cash"])
    beg_col = _find_column(df, ["beginning of period", "beginning of year"])
    end_col = _find_column(df, ["end of period", "end of year"])

    errors = []
    for idx, row in df.iterrows():
        calc_change = None
        if beg_col and end_col and pd.notna(row.get(beg_col)) and pd.notna(row.get(end_col)):
            calc_change = row[end_col] - row[beg_col]
        elif op_col and inv_col and fin_col:
            op = row.get(op_col, 0)
            inv = row.get(inv_col, 0)
            fin = row.get(fin_col, 0)
            if pd.notna(op) and pd.notna(inv) and pd.notna(fin):
                calc_change = op + inv + fin
        if calc_change is None:
            continue
        reported_change = None
        if change_col:
            reported_change = row.get(change_col)
        if reported_change is not None and pd.notna(reported_change):
            diff = reported_change - calc_change
            if abs(diff) > tol * max(abs(reported_change), 1):
                errors.append((idx, diff))
    return errors


def run_sanity_checks(company_dir: str) -> None:
    """Run checks on csv outputs located in `company_dir`."""
    bs_path = os.path.join(company_dir, "balance_sheet.csv")
    is_path = os.path.join(company_dir, "income_statement.csv")
    cf_path = os.path.join(company_dir, "cashflow_statement.csv")

    if os.path.exists(bs_path):
        bs_df = pd.read_csv(bs_path)
        bs_errs = check_balance_sheet(bs_df)
        if bs_errs:
            print(f"Balance sheet check failed for {company_dir}:")
            for idx, diff in bs_errs:
                print(f"  Row {idx}: assets differ by {diff}")

    if os.path.exists(is_path):
        is_df = pd.read_csv(is_path)
        is_errs = check_income_statement(is_df)
        if is_errs:
            print(f"Income statement check failed for {company_dir}:")
            for idx, diff in is_errs:
                print(f"  Row {idx}: gross profit mismatch {diff}")

    if os.path.exists(cf_path):
        cf_df = pd.read_csv(cf_path)
        cf_errs = check_cashflow(cf_df)
        if cf_errs:
            print(f"Cashflow statement check failed for {company_dir}:")
            for idx, diff in cf_errs:
                print(f"  Row {idx}: change in cash mismatch {diff}")


if __name__ == "__main__":
    #import argparse
    
    
    #parser = argparse.ArgumentParser(description="Run sanity checks on statement csvs")
    #parser.add_argument("data_dir", help="Directory containing statement csv files")
    
    data_dir = r"D:\code\SEC\SecData"
    run_sanity_checks(data_dir)
