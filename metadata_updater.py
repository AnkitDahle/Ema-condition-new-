import os
import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Faltu warnings mute karna
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# Fake Browser Session
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

# Supabase Connection
url_sb = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url_sb, key)

def get_full_nse_list():
    print("Zerodha se list nikal rahe hain...")
    try:
        df = pd.read_csv("https://api.kite.trade/instruments", low_memory=False) 
        df_nse = df[(df['exchange'] == 'NSE') & (df['instrument_type'] == 'EQ') & (df['lot_size'] == 1)]
        clean_symbols = []
        for s in df_nse['tradingsymbol'].tolist():
            s = str(s)
            if '-' in s or ' ' in s or s.endswith("BEES") or "ETF" in s or "LIQUID" in s: continue
            clean_symbols.append(s)
        return clean_symbols
    except Exception as e:
        return []

# Har ek stock ka data nikalne ka worker function
def fetch_metadata(symbol):
    ticker = symbol + ".NS"
    try:
        info = yf.Ticker(ticker, session=session).info
        sector = info.get('sector', 'Unknown')
        proxy = info.get('industry', 'Unknown')
        
        if not sector or str(sector).strip() == "": sector = 'Unknown'
        if not proxy or str(proxy).strip() == "": proxy = 'Unknown'
        return {"stock_symbol": symbol, "sector": sector, "industry_proxy": proxy}
    except:
        return {"stock_symbol": symbol, "sector": 'Unknown', "industry_proxy": 'Unknown'}

nse_stocks = get_full_nse_list()
print(f"🚀 TOTAL {len(nse_stocks)} STOCKS! Turbo Mode ON (Multi-threading)...\n")

batch_data = []
success_count = 0

# Ek sath 15 parallel requests jayengi (Superfast)
with ThreadPoolExecutor(max_workers=15) as executor:
    futures = {executor.submit(fetch_metadata, symbol): symbol for symbol in nse_stocks}
    
    for count, future in enumerate(as_completed(futures), 1):
        res = future.result()
        batch_data.append(res)
        success_count += 1
        
        # Har 200 stocks ke baad database me thonk do (Save)
        if len(batch_data) >= 200:
            try:
                supabase.table('stock_metadata').upsert(batch_data).execute()
                print(f"✅ {count} stocks ka data database me chala gaya...")
            except Exception as db_error:
                print(f"❌ Database Error: {db_error}")
            batch_data = []

# Bacha hua aakhri data save karna
if batch_data:
    supabase.table('stock_metadata').upsert(batch_data).execute()

print(f"🎉 BOOM! Poore {success_count} stocks ka Sector Data bullet ki speed se save ho gaya!")
