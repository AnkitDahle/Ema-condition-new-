import requests
import pandas as pd
from supabase import create_client
import os
from datetime import datetime
import pytz

# Supabase Credentials (GitHub Secrets se uthayega)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Supabase credentials nahi mile. GitHub Secrets check karein.")
    exit()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🚀 Fetching LIVE data from TradingView Screener...")

# TradingView API request
tv_url = "https://scanner.tradingview.com/india/scan"
query = {
    "columns": ["name", "close", "SMA20", "SMA50"],
    "filter": [{"left": "exchange", "operation": "equal", "right": "NSE"}]
}

try:
    response = requests.post(tv_url, json=query).json()
    raw_tv_data = response.get('data', [])
except Exception as e:
    print(f"❌ TradingView API fail: {e}")
    exit()

print(f"✅ Downloaded {len(raw_tv_data)} stocks from TradingView.")

# Nifty 500 stocks ki list load karna
try:
    nifty_df = pd.read_csv('ind_nifty500list.csv')
    nifty_symbols = nifty_df['Symbol'].str.upper().tolist()
except Exception as e:
    print("⚠️ Nifty 500 file nahi mili. Kripya file GitHub par upload karein.")
    nifty_symbols = []

# Calculation Logic
all_above_20 = all_below_20 = all_above_50 = all_below_50 = 0
n500_above_20 = n500_below_20 = n500_above_50 = n500_below_50 = 0

for item in raw_tv_data:
    symbol = item['d'][0].upper()
    close_price = item['d'][1]
    sma20 = item['d'][2]
    sma50 = item['d'][3]
    
    if close_price is None or sma20 is None or sma50 is None:
        continue

    # 1. ALL STOCKS
    if close_price > sma20: all_above_20 += 1
    else: all_below_20 += 1
    if close_price > sma50: all_above_50 += 1
    else: all_below_50 += 1
        
    # 2. NIFTY 500
    if symbol in nifty_symbols:
        if close_price > sma20: n500_above_20 += 1
        else: n500_below_20 += 1
        if close_price > sma50: n500_above_50 += 1
        else: n500_below_50 += 1

# Aaj ki date nikalna
ist = pytz.timezone('Asia/Kolkata')
today_str = datetime.now(ist).strftime('%Y-%m-%d')

print(f"📊 ALL STOCKS - Above 20: {all_above_20}, Above 50: {all_above_50}")
print(f"📊 NIFTY 500  - Above 20: {n500_above_20}, Above 50: {n500_above_50}")

# Nayi tables mein push karna (YAHI MAIN FIX HAI)
def push_to_db(table, data):
    try:
        supabase.table(table).upsert(data).execute()
        print(f"✅ Data successfully saved to {table}")
    except Exception as e:
        print(f"❌ Error saving to {table}: {e}")

# All stocks ka data push
push_to_db('market_breadth_all', {
    "date": today_str, "above_20dma": all_above_20, "below_20dma": all_below_20,
    "above_50dma": all_above_50, "below_50dma": all_below_50
})

# Nifty 500 ka data push
push_to_db('market_breadth_nifty500', {
    "date": today_str, "above_20dma": n500_above_20, "below_20dma": n500_below_20,
    "above_50dma": n500_above_50, "below_50dma": n500_below_50
})
