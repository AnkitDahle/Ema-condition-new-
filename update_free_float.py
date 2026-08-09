import yfinance as yf
import pandas as pd
from supabase import create_client
import os
import time

# Supabase Connect
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 👇 Aapki scanner table ka 100% exact naam
TABLE_NAME = "swing_stocks"

print(f"🌐 Fetching Breakout Stocks from Supabase table: {TABLE_NAME}...")

try:
    # Scanner table se poora data mangwana
    res = supabase.table(TABLE_NAME).select('*').execute()
    df = pd.DataFrame(res.data)
    
    if df.empty:
        print("🤷‍♂️ Scanner table is empty. No stocks to update.")
        exit()

    # Column ka naam dhoondhna (scanner_job.py me 'stock_symbol' save hota hai)
    sym_col = 'stock_symbol' if 'stock_symbol' in df.columns else ('symbol' if 'symbol' in df.columns else None)
    
    if not sym_col:
        print("⚠️ Error: Scanner table me Symbol wala column nahi mila.")
        exit()
        
    # Unique stocks ki list banana taaki Yahoo API fast chale
    symbols = df[sym_col].dropna().unique().tolist()
    print(f"✅ Found {len(symbols)} unique breakout stocks in scanner.")

except Exception as e:
    print(f"⚠️ Failed to fetch stocks from Supabase: {e}")
    exit()

print(f"🚀 Fetching Free Float from Yahoo Finance for these {len(symbols)} stocks...\n")

for sym in symbols:
    try:
        # Yahoo Finance ke liye '.NS' lagana zaroori hai
        tkr = yf.Ticker(f"{sym}.NS")
        info = tkr.info
        
        total_shares = info.get('sharesOutstanding')
        float_shares = info.get('floatShares')
        
        if total_shares and float_shares:
            float_cr = round(float_shares / 10000000, 2) # Crore mein convert
            ff_pct = round((float_shares / total_shares) * 100, 2) # % nikalna
            
            # Upsert into free_float_master table (Supabase)
            supabase.table('free_float_master').upsert({
                "symbol": sym,
                "float_shares_cr": float_cr,
                "free_float_pct": ff_pct
            }).execute()
            print(f"✅ Saved {sym}: Float {float_cr}Cr ({ff_pct}%)")
        else:
            print(f"⚠️ Free Float data not found on Yahoo for {sym}")
            
    except Exception as e:
        print(f"❌ Failed for {sym}: {e}")
        
    # Yahoo block na kare isliye 0.5 second ka pause
    time.sleep(0.5) 
    
print("\n🎉 Free Float for Breakout Stocks Updated Successfully!")
