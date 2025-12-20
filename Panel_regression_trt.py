import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_hac

def tile_auto(s, targets=(5, 3, 2)):
    """Return 1..k tiles per date, adapting k. Works even with many ties."""
    s = pd.to_numeric(s, errors="coerce")
    s = s.replace([np.inf, -np.inf], np.nan)
    if s.isna().all():
        return pd.Series(index=s.index, dtype="float64")

    # If all equal, put everyone in bin 1 (still usable for T/B spread if another date works)
    if s.nunique(dropna=True) == 1:
        return pd.Series(1, index=s.index, dtype="float64")

    # Try qcut with decreasing number of bins
    for q in targets:
        try:
            bins = pd.qcut(s, q, labels=False, duplicates="drop")
            # If qcut collapsed (e.g., only 2–3 bins), still accept if >=2 bins exist
            if pd.Series(bins).nunique(dropna=True) >= 2:
                return bins.astype("float64") + 1
        except Exception:
            continue

    # Fallback: rank then cut into halves
    r = s.rank(method="first", pct=True)
    bins = pd.cut(r, [0, .5, 1.0], labels=False, include_lowest=True)
    if pd.Series(bins).nunique(dropna=True) >= 2:
        return bins.astype("float64") + 1
    return pd.Series(index=s.index, dtype="float64")

def varianceEstimate(hml_series, nlags=4):
    y = pd.Series(hml_series).replace([np.inf, -np.inf], np.nan).dropna()
    if len(y) < 8:
        return np.nan, np.nan, np.nan
    X = sm.add_constant(np.ones(len(y)))
    res = sm.OLS(y.values, X).fit()
    cov = cov_hac(res, nlags=nlags)
    mu = res.params[0]
    se = np.sqrt(cov[0, 0])
    t = mu / se if se > 0 else np.nan
    p = 2 * (1 - sm.distributions.norm.cdf(abs(t))) if np.isfinite(t) else np.nan
    return mu, t, p

def TEST_HYPOTHESIS(df_ready, sectors_to_keep, date_col="filing_date_cs", nlags=4):
    df = (df_ready[df_ready["sector"].isin(sectors_to_keep)]
          .replace([np.inf, -np.inf], np.nan)
          .dropna(subset=["inv_vol", "rev_growth_next", date_col])
          .copy())
    df[date_col] = pd.to_datetime(df[date_col])

    # Tile within EACH DATE (after your sector filter)
    df["q_invvol"] = df.groupby(date_col)["inv_vol"].transform(tile_auto)

    # Build spread using whatever bins exist (prefer Q5-Q1, else T3-T1, else H-L=2-1)
    port = (df.dropna(subset=["q_invvol"])
              .assign(q_invvol=lambda d: d["q_invvol"].astype(int))
              .groupby([date_col, "q_invvol"])["rev_growth_next"]
              .mean().reset_index())
    wide = port.pivot(index=date_col, columns="q_invvol", values="rev_growth_next")

    hml, label = None, None
    if {1, 5}.issubset(wide.columns):
        hml, label = (wide[5] - wide[1]).dropna(), "Q5–Q1"
    elif {1, 3}.issubset(wide.columns):
        hml, label = (wide[3] - wide[1]).dropna(), "T3–T1"
    elif {1, 2}.issubset(wide.columns):
        hml, label = (wide[2] - wide[1]).dropna(), "H–L (2–1)"
    else:
        print(f"{'/'.join(sectors_to_keep)} – not enough bins on any date.")
        return

    mu, t, p = varianceEstimate(hml, nlags=nlags)
    print(f"{'/'.join(sectors_to_keep)} – {label} mean: {mu:.4f} | t: {t:.2f} | p={p:.3f}")
    
if __name__=="__main__":
    
    path = r"D:\code\SEC_Fundamentals\summary_statement\summary_statement_with_features.csv"
    df_ready = pd.read_csv(path)
    df_ready["inv_vol"] = df_ready["capex_vol_advanced"]
    bad_sectors = ["Telecom"]
    sectors = list(set(df_ready["sector"]))

    
    for s in sectors:
        TEST_HYPOTHESIS(df_ready,[s])
    
    TEST_HYPOTHESIS(df_ready,["Wholesale","Utilities","Energy"])