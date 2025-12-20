# xgb_baseline.py
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score

CSV_PATH =  r"D:\code\SEC_Fundamentals\summary_statement\summary_statement_with_features.csv"
USE_SECTOR = True          # include sector as one-hot
SCALE_BY_ASSETS = False    # set True if you want simple ratio scaling by totalassets_bs
RANDOM_STATE = 42

# ---------- Load & unify identifiers ----------
df = pd.read_csv(CSV_PATH)
df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed:")], errors="ignore")

# unify ticker
tickers = [c for c in ["ticker","ticker_is","ticker_cs","ticker_bs"] if c in df.columns]
assert tickers, "No ticker column"
df["ticker_u"] = df[tickers].bfill(axis=1).iloc[:,0]

# unify sector (optional)
if USE_SECTOR:
    sectors = [c for c in ["sector","sector_is","sector_cs","sector_bs"] if c in df.columns]
    if sectors:
        df["sector_u"] = df[sectors].bfill(axis=1).iloc[:,0]
    else:
        df["sector_u"] = "unknown"

# unify date -> dt
date_candidates = [c for c in [
    "filing_date","date_is","date_cs","date_bs",
    "filing_date_is","filing_date_cs","filing_date_bs"
] if c in df.columns]
assert date_candidates, "No date column found"
df["dt"] = pd.to_datetime(df[date_candidates].bfill(axis=1).iloc[:,0], errors="coerce")
assert df["dt"].notna().any(), "All dt are NaT"
df = df.sort_values(["ticker_u","dt"]).reset_index(drop=True)

# ---------- Features / target ----------
feat_cols = [c for c in df.columns
             if c.endswith(("_cs","_is","_bs","_xs"))
             and ("date" not in c and "filing_date" not in c and "ticker" not in c and "sector" not in c)]
assert feat_cols, "No numeric _cs/_is/_bs features found"

# simple ratio scaling (optional)
if SCALE_BY_ASSETS:
    denom = df.get("totalassets_bs", pd.Series([np.nan]*len(df))).replace(0, np.nan).fillna(1.0)
    df[feat_cols] = df[feat_cols].astype(float).div(denom, axis=0)

# sector one-hot (optional)
if USE_SECTOR:
    sec_dum = pd.get_dummies(df["sector_u"], prefix="sec", dummy_na=True)
    X_frame = pd.concat([df[feat_cols].astype(float), sec_dum], axis=1)
else:
    X_frame = df[feat_cols].astype(float)

# XGBoost handles NaNs internally; keep them as NaN
y = pd.to_numeric(df["rev_growth_next_xs"], errors="coerce").replace([np.inf,-np.inf], np.nan)
# if target has NaN, drop those rows from both X and y
mask = y.notna()
X_frame = X_frame.loc[mask]
y = y.loc[mask]
dt = df.loc[mask, "dt"]

# ---------- Time split (last 20% of dates -> validation) ----------
unique_dates = np.array(sorted(dt.unique()))
cutoff = unique_dates[int(0.8 * len(unique_dates))] if len(unique_dates) > 5 else unique_dates[-2]
train_idx = dt <  cutoff
val_idx   = dt >= cutoff

X_train, y_train = X_frame.loc[train_idx], y.loc[train_idx]
X_val,   y_val   = X_frame.loc[val_idx],   y.loc[val_idx]
assert len(X_train) and len(X_val), "Empty train/val after split"

# For interpretability: sigma units of MAE
y_mu, y_sd = y_train.mean(), y_train.std() + 1e-8

# ---------- Model ----------
model = XGBRegressor(
    n_estimators=100,
    learning_rate=0.05,
    max_depth=10,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    min_child_weight=1.0,
    tree_method="hist",       # fast on CPU/GPU
    random_state=RANDOM_STATE,
    n_jobs=0,
    eval_metric="mae",
    early_stopping_rounds=100
)

model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    verbose=False,
    
)

# ---------- Eval ----------
pred = model.predict(X_val)
mae = mean_absolute_error(y_val, pred)
r2  = r2_score(y_val, pred)
mae_sigma = mean_absolute_error((y_val - y_mu)/y_sd, (pred - y_mu)/y_sd)

print({
    "cutoff": str(cutoff),
    "val_rows": int(len(y_val)),
    "best_ntree_limit": int(model.get_booster().best_iteration+1),
    "MAE": float(mae),
    "MAE_in_sigmas": float(mae_sigma),
    "R2": float(r2),
})

# Optional: top features
importances = pd.Series(model.feature_importances_, index=X_frame.columns).sort_values(ascending=False).head(20)
print("\nTop features:\n", importances.round(4).to_string())
