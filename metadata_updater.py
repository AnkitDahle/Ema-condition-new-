import os
import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import time
import requests
import logging

# Faltu warnings mute karna
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# Fake Browser Session taaki Yahoo block na kare
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

# Supabase Connection
url_sb = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url_sb, key)

# 🚫 HARDCODED BLACKLIST (Yahan aap aur bhi kachra stocks comma lagakar add kar sakte hain)
KACHRA_STOCKS = [
    "SNXT50BE", "ITADD", "MOLOWV", "ARTEMISM", "SILVERADD", "NEXT50", "PVTBANKA", 
    "MOMENTUM", "GOLDADD", "SILVERAG", "NIFTYADD", "MONQ50", "MIDQ50ADD", "SILVERBET", 
    "MAKEINDIA", "PSUBANK", "SILVER", "MIDCAP", "MOMOMEI", "LOWVOL1", "LICNFNHG", 
    "MOQUALIT", "QGOLDHA", "QNIFTY", "SENSEXAD", "LOWVOL", "AXSENSEX", "GOLD1", 
    "HDFCMID", "HDFCNEXT", "GOLDBETA", "GSEC10YE", "BANKADD", "EQUAL50A", "NPBET", 
    "HDFCPVTE", "TECH", "MOHEALTI", "HDFCBSE5", "BANKNIFTY", "MASPTOP5", "HDFCSENS", 
    "HDFCLOW", "HDFCMON", "HDFCNIF1", "HEALTHY", "HDFCNIFT", "ICICIB22", "SILVER1", 
    "CONS", "ESG", "NIFTYBETA", "HDFCSML", "SENSEXBE", "BFSI", "MAHKTECI", "MOGSEC", 
    "NIFTYQLIT", "MOVALUE", "ALPHA", "ABSLNN50", "NV20", "GUJRAFFIA", "JSWDULUX"
]

# Master List nikalna (Strict & Hardcoded Filter ke sath)
def get_full_nse_list():
    print("Zerodha se latest list nikal rahe hain...")
    try:
        df = pd.read_csv("https://api.kite.trade/instruments", low_memory=False) 
        df_nse = df[(df['exchange'] == 'NSE') & (df['instrument_type'] == 'EQ') & (df['lot_size'] == 1)]
        
        clean_symbols = []
        for s in df_nse['tradingsymbol'].tolist():
            s = str(s)
            
            # 1. KADAK FILTER: NAV, MF, BEES aur kachra block!
            if '-' in s or ' ' in s or s.endswith("BEES") or s.endswith("NAV") or "ETF" in s or "LIQUID" in s or "MF" in s: 
                continue
                
            # 2. HARDCODED FILTER: Jo list aapne di hai use ignore karo
            if s in KACHRA_STOCKS:
                continue
                
            clean_symbols.append(s)
        return clean_symbols
    except Exception as e:
        print(f"⚠️ API Error: {e}")
        return []

nse_stocks = get_full_nse_list()
print(f"Total {len(nse_stocks)} premium stocks mile. Slow fetching shuru kar rahe hain...\n")

batch_data = []

# Ek-ek karke aaram se data nikalna (Slow & Steady Mode - 1.5s delay)
for index, symbol in enumerate(nse_stocks):
    ticker = symbol + ".NS"
    try:
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

    # Har 100 stocks ke baad Database me bhejna 
    if len(batch_data) >= 100:
        try:
            supabase.table('stock_metadata').upsert(batch_data).execute()
            print("💾 100 stocks ka batch database me update ho gaya!\n")
        except Exception as db_error:
            print(f"❌ Supabase Save Error: {db_error}")
        finally:
            batch_data = [] # List ko hamesha khali karo taaki aage badh sakein

# Bacha hua aakhri data save karna
if batch_data:
    try:
        supabase.table('stock_metadata').upsert(batch_data).execute()
        print("💾 Aakhri batch database me update ho gaya!\n")
    except Exception as db_error:
        print(f"❌ Supabase Save Error on final batch: {db_error}")
    
print("🎉 BOOM! Poore market ka Sector aur Proxy data update cycle complete!")
