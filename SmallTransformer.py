"""
Minimal, teach-by-skeleton Transformer for financial time series (PyTorch)
— Keep this file tiny; fill the TODOs for your data shape and task. —

Includes:
1) Sinusoidal positional encoding for month/year.
2) Simple Transformer encoder block.
3) Placeholder function `load_data()` where **you** implement data loading.
"""
from __future__ import annotations
import math
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import torch
import torch.nn as nn

# =============================
# 1) Data loader placeholder
# =============================

def load_data() -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Load and preprocess your accounting data.
    Expected outputs (all torch.Tensors):
        X: [N, T, F] standardized features
        Y: [N, F] or [N, T, F] targets
        years: [N, T] integer years (e.g., 2001..2025)
        months: [N, T] integer months (1..12)
    TODO: Implement this according to your schema (CSV, DB, etc.).
    """
    raise NotImplementedError("Implement load_data() for your dataset")


# =============================
# 2) POSitional encoding for dates (month index)
# =============================

def month_index(year: torch.Tensor, month: torch.Tensor) -> torch.Tensor:
    return year.long() * 12 + (month.long() - 1)


def sinusoidal_encoding(pos_idx: torch.Tensor, d_model: int) -> torch.Tensor:
    pos = pos_idx.float().unsqueeze(-1)
    i = torch.arange(0, d_model, 2, device=pos.device)
    div = torch.exp(-math.log(10000.0) * i / d_model)
    angles = pos * div
    pe_even = torch.sin(angles)
    pe_odd = torch.cos(angles)
    pe = torch.zeros(pos_idx.shape + (d_model,), device=pos.device)
    pe[..., 0::2] = pe_even
    pe[..., 1::2] = pe_odd
    return pe

# =============================
# 3) Minimal Transformer encoder
# =============================

class TimeTransformer(nn.Module):
    def __init__(self, n_features: int, d_model: int=128, n_heads: int=4, n_layers: int=3, dim_ff: int=256, dropout: float=0.1):
        super().__init__()
        self.input_proj = nn.Linear(n_features, d_model)
        enc_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=dim_ff,
            dropout=dropout, batch_first=True, activation="gelu", norm_first=True
        )
        self.encoder = nn.TransformerEncoder(enc_layer, num_layers=n_layers)

    def forward(self, x: torch.Tensor, pos_idx: torch.Tensor) -> torch.Tensor:
        h = self.input_proj(x)
        h = h + sinusoidal_encoding(pos_idx, h.size(-1))
        h = self.encoder(h)
        return h


# =============================
# 4) Example training skeleton
# =============================

def example_training_step():
    """Synthetic example showing structure; replace with real data."""
   
    X, Y, years, months,_,_,_,_ = load_data()
    

    pos = month_index(years, months)
    model = TimeTransformer(X.size(-1),d_model=1000)
    head = nn.Linear(1000, 1)  # example prediction head

    opt = torch.optim.AdamW(list(model.parameters()) + list(head.parameters()), lr=3e-4, weight_decay=1e-2)

    h = model(X, pos)
    last = h[:, -1, :]
    y_hat = head(last)
    loss = nn.functional.smooth_l1_loss(y_hat, Y)
    loss.backward()
    opt.step(); opt.zero_grad(set_to_none=True)
    print({"loss": float(loss.item())})



def load_data(csv_path: str = r"D:\code\SEC_Fundamentals\summary_statement\summary_statement_with_features.csv", seq_len: int = 32, standardize: bool = True) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    
  
    
    df = pd.read_csv(csv_path)
    
    
    # --- Drop junk index columns ---
    df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed:")], errors="ignore")
    
    
    # --- Unify ticker ---
    ticker_candidates = [c for c in ["ticker", "ticker_is", "ticker_cs", "ticker_bs"] if c in df.columns]
    assert ticker_candidates, "No ticker column found"
    df["ticker_u"] = df[ticker_candidates].bfill(axis=1).iloc[:, 0]
    
    
    # --- Unify date ---
    date_candidates = [c for c in [
    "filing_date", "date_is", "date_cs", "date_bs",
    "filing_date_is", "filing_date_cs", "filing_date_bs"
    ] if c in df.columns]
    
    
    assert ticker_candidates, "No ticker column found"
    df["ticker_u"] = df[ticker_candidates].bfill(axis=1).iloc[:, 0]
    
    
    # --- Unify date ---
    date_candidates = [c for c in [
    "filing_date", "date_is", "date_cs", "date_bs",
    "filing_date_is", "filing_date_cs", "filing_date_bs"
    ] if c in df.columns]
    
    assert date_candidates, "No date column found (expected one of filing_date/date_* or filing_date_*)"
    
    dt = pd.to_datetime(df[date_candidates].bfill(axis=1).iloc[:, 0], errors="coerce")
    
    assert dt.notna().any(), "All parsed dates are NaT—please check date columns."
    df["dt"] = dt
    df["year"] = df["dt"].dt.year.astype(int)
    df["month"] = df["dt"].dt.month.astype(int)
    
    
    # --- Select numeric feature columns ending with _cs/_is/_bs, exclude id/date/sector ---
    suffixes = ("_cs", "_is", "_bs")
    exclude_tokens = ("date", "filing_date", "ticker", "sector")
    feat_cols = [
    c for c in df.columns
    if c.endswith(suffixes) and not any(tok in c for tok in exclude_tokens) and pd.api.types.is_numeric_dtype(df[c])]
    assert len(feat_cols) > 0, "No numeric feature columns with suffix _cs/_is/_bs were found."
    
    
    # --- Target ---
    assert "rev_growth_next" in df.columns, "Target column 'rev_growth_next' missing"
    
    
    # --- Sort and group by ticker, then make sliding windows ---
    df = df.sort_values(["ticker_u", "dt"]).reset_index(drop=True)
    
    #==================================================================#
    #ALIGNMENT TEST
    end_dt_list = []     # last date in the input window
    target_dt_list = []  # date corresponding to the target (next observation)
    ticker_id_list = []  # numeric ID for the ticker
    
    
    X_list, Y_list, YR_list, MO_list = [], [], [], []
    for _, g in df.groupby("ticker_u", sort=False):
        if len(g) <= seq_len:
            continue
        G = g.copy()

        G = G.sort_values("dt")
        dts = G["dt"].values
        #G_feat = G[feat_cols].astype(float)
        #denom = G["totalassets_bs"].replace(0, np.nan).fillna(1.0).values[:, None]
        G_Feat = G[feat_cols].fillna(0.0)
        F = G_Feat.astype(float).values # [n, F]
        if standardize:
            mu = F.mean(axis=0, keepdims=True)
            sd = F.std(axis=0, keepdims=True) + 1e-8
            F = (F - mu) / sd
            F[F>3] = 3.0
            F[F<-3]=-3.0
        #Y_target = G["rev_growth_next"].fillna(0.0).astype(float).values # [n]
        Y_target = (
                    pd.to_numeric(G["rev_growth_next"], errors="coerce")  # strings -> NaN
                    .replace([np.inf, -np.inf], np.nan)                 # infinities -> NaN
                    .fillna(0.0)                                        # NaN -> 0
                    .astype(float)
                    .values
                    )
        
        
        years = G["year"].values.astype(int)
        months = G["month"].values.astype(int)
        
        
        n = len(G)
        for t in range(n - seq_len - 1):
            X_list.append(F[t:t+seq_len])
            Y_list.append(Y_target[t+seq_len])
            YR_list.append(years[t:t+seq_len])
            MO_list.append(months[t:t+seq_len])
            end_dt_list.append(dts[t+seq_len-1])     # date of last row in the window
            target_dt_list.append(dts[t+seq_len])    # date of the target row
            ticker_id_list.append(G["ticker"].iloc[0])            # string ticker name
        
    
    assert X_list, "No sequences created—check seq_len or grouping."
    
    
    X = torch.tensor(np.stack(X_list), dtype=torch.float32) # [B,T,F]
    Y = torch.tensor(np.stack(Y_list), dtype=torch.float32) # [B]
    years = torch.tensor(np.stack(YR_list), dtype=torch.long) # [B,T]
    months = torch.tensor(np.stack(MO_list), dtype=torch.long) # [B,T]
    
    
    return X, Y, years, months, end_dt_list,target_dt_list,ticker_id_list,df

if __name__ == "__main__":
    #└X,Y,years,months,end_dts,trgt,ticker,df =load_data()
    example_training_step()
    