import os
import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import time
import requests
import logging

# Faltu warnings mute karna
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# Fake Browser Session taaki bilkul block na ho
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

# Supabase Connection
url_sb = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url_sb, key)

# Master List nikalna
def get_full_nse_list():
    print("Zerodha se latest list nikal rahe hain...")
    df = pd.read_csv("https://api.kite.trade/instruments", low_memory=False) 
    df_nse = df[(df['exchange'] == 'NSE') & (df['instrument_type'] == 'EQ') & (df['lot_size'] == 1)]
    
    clean_symbols = []
    for s in df_nse['tradingsymbol'].tolist():
        s = str(s)
        if '-SG' in s or '-SF' in s or '-SD' in s or '-GS' in s: continue
        if ' ' in s: continue
        if s.endswith("BEES") or "ETF" in s or "LIQUID" in s: continue
        clean_symbols.append(s)
    return clean_symbols

nse_stocks = get_full_nse_list()
print(f"Total {len(nse_stocks)} stocks mile. Slow fetching shuru kar rahe hain...\n")

batch_data = []

# Ek-ek karke aaram se data nikalna
for index, symbol in enumerate(nse_stocks):
    ticker = symbol + ".NS"
    try:
        # Har stock ke pehle 1.5 second ka aaram (No Block Guarantee)
        time.sleep(1.5)
        
        info = yf.Ticker(ticker, session=session).info
        sector = info.get('sector', 'Unknown')
        proxy = info.get('industry', 'Unknown')
        
        if not sector or str(sector).strip() == "": sector = 'Unknown'
        if not proxy or str(proxy).strip() == "": proxy = 'Unknown'
        
        batch_data.append({
            "stock_symbol": symbol,
            "sector": sector,
            "industry_proxy": proxy
        })
        
        print(f"[{index+1}/{len(nse_stocks)}] ✅ Saved: {symbol} | {sector} | {proxy}")
        
    except Exception as e:
        print(f"[{index+1}/{len(nse_stocks)}] ⚠️ Failed: {symbol}")

    # Har 100 stocks ke baad Database me bhejna taaki computer ki memory na bhare
    if len(batch_data) >= 100:
        # upsert=True ka matlab hai: naya hai toh daal do, purana hai toh update kar do
        supabase.table('stock_metadata').upsert(batch_data).execute()
        print("💾 100 stocks ka batch database me update ho gaya!\n")
        batch_data = [] # List khali kardi agle 100 ke liye

# Bacha hua aakhri data save karna
if batch_data:
    supabase.table('stock_metadata').upsert(batch_data).execute()
    
print("🎉 BOOM! Poore market ka Sector aur Proxy data successfully update ho gaya!")

