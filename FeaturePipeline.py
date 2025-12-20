# -*- coding: utf-8 -*-
"""
Created on Mon Jul 14 11:45:22 2025

@author: magnu
"""
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
import os
import numpy as np


def CheckNumberOfColumns(df):
    
    numeric_cols = df.drop(columns=['ticker', 'filing_date']).columns

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
        group = group.sort_values("filing_date")
        numeric_cols = group.drop(columns=['ticker', 'filing_date']).columns
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
            
            nmn = x.replace(".csv", "")
            dataframes[nmn]=pd.read_csv(y)
        
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

def pre_cook_dataframe(df):
    
    df = df.sort_values(["ticker","filing_date"])
    grp = df.groupby("ticker",group_keys=False)
    return grp

def rev_rec_gap(df)->pd.DataFrame:
    
    
    grp = pre_cook_dataframe(df)
    
    
    rev_growth = grp['totalrevenue_is'].pct_change(fill_method=None)
    rec_growth = grp['accountsreceivable_bs'].pct_change(fill_method=None)
    output = (rec_growth - rev_growth).rename('receivables_to_revenue_gap')
    output = pd.concat([df["filing_date"],df["ticker"],output],axis=1)
    return output


def CashflowNetIncome(df)->pd.DataFrame:
    
    op_cashflow = df["netcashprovidedbyoperatingactivities_cs"]
    is_netincome = df["netincome_is"]
    output = op_cashflow/is_netincome
    output = pd.concat([df["filing_date"],df["ticker"],output],axis=1)
    return output

def ProfitMargin(df)->pd.DataFrame:
    
    is_totalRevenue = df["totalrevenue_is"]
    is_netincome = df["netincome_is"]
    output = is_netincome/is_totalRevenue
    output = pd.concat([df["filing_date"],df["ticker"],output],axis=1)
    

    return

def ProfitMarginVol(df)->pd.DataFrame:
    
    mrg = ProfitMargin(df)
    
    grp = pre_cook_dataframe(mrg)
    
    #not sure how i grab the last one this below is just a template.
    
    return grp["margin"].pct_change(fill_method=None).std()
    
def CapExVolatility(df):
    
    #Need to find a good proxy for investments in assets. Be they capitalized or expensed.
    pass


class FactorConstructor(BaseEstimator, TransformerMixin):
    """Constructs financial factors from balance sheet data"""
    def __init__(self, factor_function):
        self.factor_function = factor_function

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X:{}) -> pd.DataFrame:
        
        if not isinstance(X, dict):
            raise ValueError("X needs to be a dictionary with keys for balance_sheet and income_statement named just so")
        
        b_s = X["balance_sheet"]
        i_s = X["income_statement"]
        return self.factor_function(b_s,i_s)
        

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


def prepare(df, name):
    df = df.copy()
    df['filing_date'] = pd.to_datetime(df['filing_date'], errors='coerce')
    df = df.loc[df['ticker'].notna() & df['filing_date'].notna()]
    df = df.sort_values(['ticker', 'filing_date'])
    # check per-group monotonicity
    bad = []
    for t, sub in df.groupby('ticker'):
        if not sub['filing_date'].is_monotonic_increasing:
            bad.append(t)
    if bad:
        print(f"[{name}] tickers with unsorted dates: {bad[:5]} (showing up to 5)")
    return df


def manual_asof(
    bs,
    is_,
    tol=pd.Timedelta("90D"),
    bs_suffix="_bs",
    is_suffix="",  # e.g. "_is" if you want IS columns tagged
):
    # 1. Prepare
    for df in (bs, is_):
        df['filing_date'] = pd.to_datetime(df['filing_date'], errors='coerce')
        df['ticker'] = df['ticker'].astype(str).str.strip().str.upper()
    bs = bs.dropna(subset=['ticker', 'filing_date']).sort_values(['ticker', 'filing_date'])
    is_ = is_.dropna(subset=['ticker', 'filing_date']).sort_values(['ticker', 'filing_date'])

    out_rows = []

    # 2. Per-ticker loop
    is_groups = is_.groupby('ticker', sort=False)
    for ticker, is_grp in is_groups:
        bs_grp = bs[bs['ticker'] == ticker]

        # 3. No BS available: emit IS rows with NaNs for BS fields
        if bs_grp.empty:
            for _, is_row in is_grp.iterrows():
                is_data = {f"{k}{is_suffix}": v for k, v in is_row.to_dict().items()}
                nan_bs = {f"{c}{bs_suffix}": np.nan for c in bs.columns if c not in ['ticker', 'filing_date']}
                out_rows.append({**is_data, **nan_bs})
            continue

        # 4. Setup for lookup
        bs_dates = bs_grp['filing_date'].to_numpy()
        bs_vals = bs_grp.drop(columns=['ticker', 'filing_date'])  # keep original index

        # 5. Match each IS row
        for _, is_row in is_grp.iterrows():
            d = np.datetime64(is_row['filing_date'])
            pos = np.searchsorted(bs_dates, d, side='right') - 1  # last <= d

            if pos >= 0:
                bs_date = bs_dates[pos]
                if d - bs_date <= tol:
                    matched = bs_vals.iloc[pos].to_dict()
                    matched['filing_date'] = pd.Timestamp(bs_date)
                else:
                    matched = {c: np.nan for c in bs_vals.columns}
                    matched['filing_date'] = pd.NaT
            else:
                matched = {c: np.nan for c in bs_vals.columns}
                matched['filing_date'] = pd.NaT

            # 6. Combine with suffixes
            is_data = {f"{k}{is_suffix}": v for k, v in is_row.to_dict().items()}
            bs_data = {f"{k}{bs_suffix}": v for k, v in matched.items()}
            out_rows.append({**is_data, **bs_data})

    # 7. Assemble
    merged_manual = pd.DataFrame(out_rows)
    merged_manual = merged_manual.sort_values([f'ticker{is_suffix}', f'date{is_suffix}']) \
                                 .reset_index(drop=True)
         
    merged_manual["filing_date"] = merged_manual[f'filing_date{is_suffix}'].combine_first(merged_manual[f"filing_date{bs_suffix}"])
    merged_manual["ticker"] = merged_manual[f'ticker{is_suffix}']
    return merged_manual   
def clean_and_sort(df, name):
    if 'filing_date' not in df or 'ticker' not in df:
        raise KeyError(f"{name} must contain 'filing_date' and 'ticker'")
    df = df.copy()
    df['filing_date'] = pd.to_datetime(df['filing_date'], errors='coerce')
    df = df.loc[df['ticker'].notna() & df['filing_date'].notna()]
    return df.sort_values(['ticker', 'filing_date'])

def cook_unified_df(bs, is_, cs, tol=pd.Timedelta("90D")):
    
    
    b_s = clean_and_sort(bs, 'balance_sheet')
    i_s = clean_and_sort(is_, 'income_statement')
    c_s = clean_and_sort(cs, 'cashflow_statement')

    # Merge IS with most recent prior BS
    m1 = manual_asof(
        b_s, 
        i_s,
        tol=tol, 
        bs_suffix="_bs",
        is_suffix="_is"
    )
    
    
    # Merge that with most recent prior CF
    merged = manual_asof(
        m1, 
        c_s,
        tol=tol, 
        bs_suffix="",
        is_suffix="_cs"
    )
    return merged.sort_values(['ticker', 'filing_date'])

def generate_mock_data():
    pass
    

#================================= CAPEX VOL  ==================== #




def add_investment_measures_advanced(df, window=12, alpha_rd=1, alpha_int=0.3, ma_thresh=0.05,vol_min_periods=6):
    df = df.sort_values(["ticker","filing_date"])
    g = df.groupby("ticker", group_keys=False)

    def _per_firm(x):
        x = x.copy()
        x = CAPEX_VOL(x)
        x = Quality_Factors_per_firm(x)
        x= GrowthFeatures_per_firm(x)
        x= capital_return_per_firm(x)
        
        return x
    
   
    def capital_return_per_firm(x):
        
        
        #We are just doing the annual stuff for now #
        wndw = 4 
        
        shrs = x['sharesoutstandingdiluted_is'].fillna(0.0)
        
        div = x["dividendspaid_cs"].fillna(0.0)
        
        annual_div = div.rolling(window=wndw).sum()/shrs
        
        shrs_net_change = x['sharesoutstandingdiluted_is'].fillna(0.0).diff().rolling(window=wndw).sum()/shrs
        
        ni    = x["netincome_is"].astype(float).fillna(0.0)
        
        current_ni = ni.diff().rolling(window=wndw).sum()
        
        prev_ni = ni.diff().rolling(window=wndw*2).sum()
        
        ni_change = (2*current_ni-prev_ni)/shrs
        
        total_sharesholder_proxy = annual_div+ni_change+shrs_net_change
        
        x["shareholder_return_proxy_xs"] = total_sharesholder_proxy
        
        return x
        
        
        
    
    def Quality_Factors_per_firm(x):
        x = x.copy()

        def col(name):
            return x[name] if name in x else pd.Series(np.nan, index=x.index)
    
        nz = lambda s: s.fillna(0)
    
        # ==== Sustainable Growth Capacity: sgc_rate = ROIC × InvRate ============
        # Investment (cash flow + R&D + Intangible this is to give some idea about M&A)
        capex  = nz(col("capitalexpenditures_cs")).abs()
        rd     = nz(col("researchanddevelopment_is"))
        intang = nz(col("intangibleassetsnet_bs"))
        d_intang = intang.diff().clip(lower=0).fillna(0)
    
        goodwill = col("goodwill_bs")
        ta = col("totalassets_bs").replace(0, np.nan)
        if goodwill.isna().all():
            d_intang_adj = d_intang
        else:
            dgw = goodwill.diff().fillna(0)
            ma_flag = (dgw / ta).fillna(0) > ma_thresh
            d_intang_adj = d_intang.mask(ma_flag, 0)
    
        inv_blended = capex + alpha_rd * rd + alpha_int * d_intang_adj
        avg_assets = (ta + ta.shift(-1)) / 2
        inv_rate = (inv_blended / avg_assets).replace([np.inf, -np.inf], np.nan)
    
        ## Return on invested capital ROIC approximation
        ebit = col("ebit_is")
        if ebit.isna().all():
            ebit = col("operatingincome_is")
    
        ##  EBT ≈ EBIT - interest expense + interest income
        iexp = nz(col("interestexpense_is"))
        
        iinc = nz(col("interestincome_is"))
        
        ebt_est = (ebit - iexp + iinc).replace([np.inf, -np.inf], np.nan)
    
        tax_exp = col("incometaxexpense_is") if "incometaxexpense_is" in x else col("taxexpensecredit_is")
        
        eff_tax = (tax_exp / ebt_est).clip(lower=0, upper=0.35).replace([np.inf, -np.inf], np.nan).fillna(0.21)
        nopat = ebit * (1 - eff_tax)
    
        cash = nz(col("cashandcashequivalents_bs"))
        
        tcl  = nz(col("totalcurrentliabilities_bs"))
        
        std  = nz(col("shorttermdebt_bs"))
        
        nibcl = (tcl - std).clip(lower=0)
        
        invested_capital = (ta - cash - nibcl).replace([np.inf, -np.inf], np.nan)
        
        avg_ic = (invested_capital + invested_capital.shift(-1)) / 2 # Does this has a look ahead bias ? 
        
        roic = (nopat / avg_ic.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
        
        #=================================================#
        x["sgc_rate_xs"] = (roic * inv_rate).astype(float)
        
        #============ ROIC STABILITY =====================#
        
   
        
        
    
        # ==== Accruals Quality (balance-sheet based) ============================
        # Using available fields: ΔCA - ΔCash - (ΔCL - ΔSTD) - Dep(IS)
        CA    = col("totalcurrentassets_bs")
        CL    = col("totalcurrentliabilities_bs")
        Cash  = col("cashandcashequivalents_bs")
        STD   = col("shorttermdebt_bs")
        DepIS = col("depreciationamortization_is")  # IS line is available
    
        dCA, dCL = CA.diff(), CL.diff()
        dCash, dSTD = Cash.diff(), nz(STD).diff()
        accruals_bs = (dCA - dCash) - (dCL - dSTD) - nz(DepIS)
        x["accruals_bs_ratio_xs"] = (accruals_bs / avg_assets).replace([np.inf, -np.inf], np.nan).astype(float)
    
        # ==== Margin Stability (vol + downside semideviation) ===================
        revenue = col("totalrevenue_is").replace(0, np.nan)
        cogs    = col("costofrevenue_is")
        sga     = col("sga_is")
        ebit2   = ebit if not ebit.isna().all() else (revenue - nz(cogs) - nz(sga))
    
        gm = (revenue - nz(cogs)) / revenue
        om = (ebit2) / revenue
    
        gm_roll = gm.rolling(window, min_periods=vol_min_periods)
        om_roll = om.rolling(window, min_periods=vol_min_periods)
    
        x["gm_vol_xs"] = gm_roll.std()
        x["om_vol_xs"] = om_roll.std()
    
        gm_mean = gm_roll.mean()
        om_mean = om_roll.mean()
        gm_down = (gm - gm_mean).clip(upper=0)
        om_down = (om - om_mean).clip(upper=0)
    
        x["gm_downside_semidev_xs"] = (gm_down.pow(2).rolling(window, min_periods=vol_min_periods).mean()) ** 0.5
        x["om_downside_semidev_xs"] = (om_down.pow(2).rolling(window, min_periods=vol_min_periods).mean()) ** 0.5
    
        x["margin_stability_score_xs"] = (
            x["gm_vol_xs"].rank(pct=True) +
            x["om_vol_xs"].rank(pct=True) +
            x["gm_downside_semidev_xs"].rank(pct=True) +
            x["om_downside_semidev_xs"].rank(pct=True)
        ) / 4.0
        
        
        
        #================ NEW FACTORS  ===========================#
        sales = col("totalrevenue_is").replace(0,np.nan); cogs=nz(col("costofrevenue_is")); ta=col("totalassets_bs").replace(0,np.nan)
        ebit = col("ebit_is");  ebit = ebit if not ebit.isna().all() else col("operatingincome_is")
        cfo  = col("netcashprovidedbyoperatingactivities_cs")
        shrs = col("sharesoutstandingdiluted_is").replace(0,np.nan)
        
        x["gross_prof_xs"]      = ((sales - cogs) / ta).replace([np.inf,-np.inf],np.nan)                    # Novy-Marx (2013)
        x["op_prof_xs"]         = (ebit / ta).replace([np.inf,-np.inf],np.nan)                               # FF profitability
        x["asset_growth_xs"]    = ta.pct_change(fill_method=None).clip(-5,5)                                 # Cooper et al. (2008)
        x["ocf_assets_xs"]      = (cfo / ta).replace([np.inf,-np.inf],np.nan)                                # Sloan-style cash emphasis
        x["net_issuance_rate_xs"]= shrs.pct_change(fill_method=None).clip(-2,2)                              # Pontiff & Woodgate (2008)
        
        
        std_debt = nz(col("shorttermdebt_bs"))
        ltd_debt = nz(col("longtermdebt_bs")) if "longtermdebt_bs" in x else 0
        
        lev = ((std_debt + ltd_debt) / ta).replace([np.inf, -np.inf], np.nan)
        x["leverage_xs"]   = lev
        x["d_leverage_xs"] = lev.diff()
        
    
        return x
    
    
    def GrowthFeatures_per_firm(x):
        x = x.copy()
    
        # ---- pull relevant fields
        sales = x["totalrevenue_is"].astype(float)
        ni    = x["netincome_is"].astype(float)
    
        capex = x["capitalexpenditures_cs"].abs().fillna(0.0)
        dep   = x["depreciationamortization_is"].fillna(0.0)
    
        goodwill = x["goodwill_bs"].fillna(0.0)
        ta       = x["totalassets_bs"].replace(0, np.nan)
    
        sga  = x["sga_is"].fillna(0.0)
        cogs = x["costofrevenue_is"].fillna(0.0)
    
        # ===============================
        #   Targets  (future growth)
        # ===============================
    
        x["rev_growth_next_ys"] = sales.pct_change().shift(-1).clip(-5,5)
        x["ni_growth_next_ys"]  = ni.pct_change().shift(-1).clip(-5,5)
    
        # ===============================
        #   Revenue-growth drivers
        # ===============================
    
        # 1) Capacity expansion
        x["capex_dep_xs"] = (capex / dep.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
    
        # 2) M&A → scope expansion
        x["d_goodwill_assets_xs"] = goodwill.diff() / ta
    
        # 3) Commercial effort
        x["d_sga_sales_xs"] = (sga / sales.replace(0, np.nan)).diff()
    
        # ===============================
        #   Net-income-growth drivers
        # ===============================
    
        # 1) Lagged revenue growth
        x["rev_growth_lag_xs"] = sales.pct_change().clip(-5,5)
    
        # 2) Margin trend
        gm = (sales - cogs) / sales.replace(0, np.nan)
        x["d_gm_xs"] = gm.diff()
    
        # 3) Operating leverage proxy
        # (same d_sga_sales_xs — already calculated)
    
        return x

        
    def CAPEX_VOL(x):
        capex_cf = x["capitalexpenditures_cs"].abs().fillna(0.0)
        # R&D
        rd = x["researchanddevelopment_is"].ffill().fillna(0)

        # Intangibles ex-goodwill: use reported intangibles; never add goodwill
        intang = x["intangibleassetsnet_bs"].ffill().fillna(0)

        # Δ intangible investment (only increases)
        dintang = intang.diff().clip(lower=0).fillna(0)

        # M&A guardrail: large goodwill jumps -> likely acquisition we have to show little vol incase they do not report. 
        # This will bias the thing a bit, ideally we should weight the volatility 
        # Moreover we need to somehow normalize the volatility.
        goodwill = x["sga_is"].ffill().fillna(0)
        dgoodwill = goodwill.diff().fillna(0)
        tot_assets = x["totalassets_bs"].replace(0, np.nan)

        ma_flag = (dgoodwill / tot_assets).fillna(0) > ma_thresh
        
        dintang_adj = dintang.mask(ma_flag, 0)

        # Blended economic investment (flow)
        x["inv_base_xs"]    = capex_cf
        x["inv_base_RND_xs"] = capex_cf +rd
        x["inv_blended_xs"] = capex_cf + rd + dintang_adj

        # Scale by size (assets)
        rd_base_rate =  rd/tot_assets
        intangeble_rate= dintang_adj / tot_assets
        inv_base_rate    = x["inv_base_xs"]    / tot_assets
        inv_base_RND_rate = x["inv_base_RND_xs"]  / tot_assets
        inv_blended_rate = x["inv_blended_xs"] / tot_assets

        # Rolling volatility (8Q std)
        x["intangeble_vol_xs"] = intangeble_rate.rolling(window,min_periods=6).std()
        x["RND_vol_xs"]    =   rd_base_rate.rolling(window,min_periods=6).std()
        x["capex_vol_base_xs"]    = inv_base_rate.rolling(window, min_periods=6).std()
        x["capex_vol_RND_xs"]      = inv_base_RND_rate.rolling(window,min_periods=6).std()
        x["capex_vol_advanced_xs"] = inv_blended_rate.rolling(window, min_periods=6).std()
        return x

    return g.apply(_per_firm,include_groups=True)

#=================================================================================================#



    bs = pd.DataFrame({
        'ticker': ['A', 'A', 'B'],
        'date': ['2023-01-31', '2023-04-30', '2023-03-31'],
        'accountsreceivable': [10, 20, 30]
    })
    is_ = pd.DataFrame({
        'ticker': ['A', 'A', 'B', 'B'],
        'date': ['2023-02-15', '2023-04-30', '2023-04-01', '2023-01-01'],
        'totalrevenue': [100, 110, 200, 190]
    })  
    return bs,is_


def GetSectors(df_in):
    path=r"D:\code\SEC_Fundamentals\sector_map.csv"
    df = pd.read_csv(path)
    df = df.set_index("ticker")
    sector_dict = df["sector"].to_dict()
    
    df_in["sector"] = df_in["ticker"].apply(lambda x:sector_dict[x])
    return df_in
            

if __name__=="__main__":
    
    
    path  = r"D:\code\SEC_Fundamentals\summary_statement"
    flnmn = ["balance_sheet.csv","cashflow_statement.csv","income_statement.csv"]
    DL = DataLoader(path,flnmn)
    
    df_unified = cook_unified_df(DL.data["balance_sheet"],DL.data["income_statement"],DL.data["cashflow_statement"])
    
    #Save the unified dataset#
    
    df_unified.to_csv(path+"unified.csv")
    RoA = CashflowNetIncome(df_unified)
    
    capexVol = add_investment_measures_advanced(df_unified)
    
    #  THIS IS A BIT MESSY !!!
    
    def get_ni_growth(df):
        
        df = df.sort_values(["ticker","filing_date"],ascending=[True,True]).copy()
        ne_next = df.groupby("ticker")["netincome_is"].shift(-1)

        df["ni_growth_next_ys"] = (ne_next / df["netincome_is"]) - 1
        
        df["ni_growth_next_ys"] = df["ni_growth_next_ys"].clip(lower=-5,upper=5)
        
        return df
    
    def get_rev_growth(df):
        df = df.sort_values(["ticker","filing_date"],ascending=[True,True]).copy()
        ne_next = df.groupby("ticker")["totalrevenue_is"].shift(-1)

        df["rev_growth_next_ys"] = (ne_next / df["totalrevenue_is"]) - 1
        
        df["rev_growth_next_ys"] = df["rev_growth_next_ys"].clip(lower=-5,upper=5)
        
        nn_shrd_ret = df.groupby("ticker")["shareholder_return_proxy_xs"].shift(-1)
        
        df["shareholder_return_proxy_next_ys"] = (nn_shrd_ret/df["shareholder_return_proxy_xs"]-1)
        
        df["shareholder_return_proxy_next_ys"] = df["shareholder_return_proxy_next_ys"].clip(lower=-5,upper=5)
        
        df["shareholder_return_proxy_lag_xs"] = df.groupby("ticker")["shareholder_return_proxy_xs"].shift(1)
        
        return df
        
    
    capexVol = get_ni_growth(capexVol)
    capexVol = get_rev_growth(capexVol)
    capexVol = GetSectors(capexVol)
    
    path2 = r"D:\code\SEC_Fundamentals\summary_statement\summary_statement_with_features.csv"
    capexVol.to_csv(path2)
    
    