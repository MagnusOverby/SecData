import os, time
import pandas as pd
from edgar import Company, set_identity

BASE_DIR = r"D:\code\SEC_Fundamentals"
OUT_PATH  = os.path.join(BASE_DIR, "sector_map.csv")

def GetAllTickers(base_dir=BASE_DIR):
    path = os.path.join(base_dir, "allTickers.csv")  # must have a 'ticker' column
    return pd.read_csv(path)

def sic_to_sector(sic):
    if pd.isna(sic): return "Unknown"
    s = int(sic)
    if 6000 <= s <= 6999: return "Financials"
    if 4900 <= s <= 4949: return "Utilities"
    if 6500 <= s <= 6799: return "Real Estate"
    if 1000 <= s <= 1499: return "Energy"
    if 4810 <= s <= 4899: return "Telecom"
    if 7300 <= s <= 7399 or 3570 <= s <= 3579: return "Technology"
    if 8000 <= s <= 8999: return "Health Services"
    if 2000 <= s <= 3999: return "Manufacturing"
    if 5000 <= s <= 5199: return "Wholesale"
    if 5200 <= s <= 5999: return "Retail"
    if 7000 <= s <= 7299 or 7900 <= s <= 7999: return "Leisure"
    return "Other"

def build_sector_map_single_thread(email):
    # 1) set SEC identity ONCE before any EDGAR calls
    set_identity(email)

    # 2) load tickers
    tickers = GetAllTickers(BASE_DIR)["ticker"].astype(str).dropna().unique().tolist()[:2500]

    # 3) build mapping
    rows = []
    for i, t in enumerate(tickers, 1):
        try:
            c = Company(t)  # uses SEC endpoints; identity must be set
            sic = getattr(c.data, "sic", None)
            sec = sic_to_sector(sic)
            desc = getattr(c.data, "sic_description", "") or ""
            rows.append((t, sic, sec, desc))
        except Exception as e:
            rows.append((t, None, "Unknown", ""))

        # small pause to be polite to SEC
        if i % 25 == 0:
            print(f"{i}/{len(tickers)} processed…")
        time.sleep(0.15)

    # 4) save
    out = pd.DataFrame(rows, columns=["ticker", "sic", "sector", "sic_description"])
    out.drop_duplicates("ticker", keep="last").to_csv(OUT_PATH, index=False)
    print(f"Saved {len(out)} rows to {OUT_PATH}")

# ---- run ----
# build_sector_map_single_thread("your.email@domain.com")
if __name__ == "__main__":
    build_sector_map_single_thread("magnus@pagnus.com")
    