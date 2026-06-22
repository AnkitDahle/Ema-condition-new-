import os
import yfinance as yf
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import logging
import warnings

# Faltu warnings ko mute karna
warnings.filterwarnings('ignore')
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# 1. Supabase Connection Set Karna
url_sb = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url_sb, key)

today_date = datetime.now().strftime("%Y-%m-%d")

# 2. Zerodha API se Master List nikalna
def get_full_nse_list():
    try:
        print("Zerodha API se list download kar rahe hain...")
        df = pd.read_csv("https://api.kite.trade/instruments", low_memory=False) 
        df_nse = df[(df['exchange'] == 'NSE') & (df['instrument_type'] == 'EQ')]
        nse_symbols = df_nse['tradingsymbol'].tolist()
        
        clean_symbols = []
        for s in nse_symbols:
            s = str(s)
            if '-SG' in s or '-SF' in s or '-SD' in s or '-GS' in s: continue
            if ' ' in s: continue
            if s.endswith("BEES") or "ETF" in s or "LIQUID" in s: continue
            clean_symbols.append(s)
            
        print(f"✅ Kachra hatane ke baad {len(clean_symbols)} pure stocks mil gaye!")
        return clean_symbols
    except Exception as e:
        return ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ZOMATO"]

nse_stocks = get_full_nse_list()
stocks = [s + ".NS" for s in nse_stocks]

print(f"🚀 MASTERPLAN ACTIVE: Ek sath {len(stocks)} stocks ka data download ho raha hai...")
print("⏳ Isme 1-2 minute lag sakte hain, kripya wait karein...")

# --- THE MAGIC: BULK DOWNLOAD ---
bulk_data = yf.download(stocks, period="2y", interval="1d", threads=True, progress=False)

print("✅ Bulk Download Complete! Ab calculation shuru karte hain...")

# Extracting specific dataframes for fast calculation
close_df = bulk_data['Close']
high_df = bulk_data['High']
vol_df = bulk_data['Volume']

matched_stocks_data = [] # Data ek sath save karne ke liye list
saved_count = 0

# 3. Memory mein Fast Calculation (Bina internet ke)
for ticker in stocks:
    try:
        if ticker not in close_df.columns:
            continue

        close_data = close_df[ticker].dropna()
        high_data = high_df[ticker].dropna()
        vol_data = vol_df[ticker].dropna()

        if len(close_data) > 252:
            sma_200 = close_data.rolling(window=200).mean()
            sma_50 = close_data.rolling(window=50).mean()
            vol_sma_20 = vol_data.rolling(window=20).mean()
            turnover_data = close_data * vol_sma_20
            
            close_22_ago = close_data.shift(22)
            close_66_ago = close_data.shift(66)
            max_high_252 = high_data.shift(1).rolling(window=252).max()
            
            close = float(close_data.iloc[-1])
            close_22 = float(close_22_ago.iloc[-1])
            close_66 = float(close_66_ago.iloc[-1])
            sma_200_val = float(sma_200.iloc[-1])
            sma_50_val = float(sma_50.iloc[-1])
            turnover = float(turnover_data.iloc[-1])
            max_high = float(max_high_252.iloc[-1])
            
            # --- AAPKE CHARTINK WALE STRICT RULES ---
            tech_cond1 = (close / close_22 > 1.2) and (turnover > 100000000) and (close > sma_200_val)
            tech_cond2 = (close / close_66 >= 1.3) and (close >= 1) and (turnover > 100000000) and (close > sma_200_val)
            tech_cond3 = (close > max_high * 0.75) and (close > sma_50_val) and (close > sma_200_val) and (turnover > 100000000)
            
            if tech_cond1 or tech_cond2 or tech_cond3:
                # Market Cap Check
                try:
                    raw_mcap = yf.Ticker(ticker).info.get('marketCap', 15000000000)
                    mcap_cr = (raw_mcap / 10000000)
                except:
                    mcap_cr = 1500 
                
                cond1 = tech_cond1 and (mcap_cr > 1)
                cond2 = tech_cond2 and (mcap_cr > 0)
                cond3 = tech_cond3 and (mcap_cr >= 1000)
                
                if cond1 or cond2 or cond3:
                    match_type = []
                    if cond1: match_type.append("1M Momentum")
                    if cond2: match_type.append("3M Momentum")
                    if cond3: match_type.append("52W High Pullback")
                    
                    condition_str = " + ".join(match_type)
                    symbol_clean = ticker.replace(".NS", "")
                    
                    matched_stocks_data.append({
                        "scan_date": today_date,
                        "stock_symbol": symbol_clean,
                        "close_price": round(close, 2),
                        "turnover_cr": round(turnover / 10000000, 2),
                        "condition_matched": condition_str
                    })
                    print(f"🔥 Found Breakout: {symbol_clean} - {condition_str}")
                    saved_count += 1
    except Exception as e:
        pass

# --- THE MAGIC: BULK INSERT TO DATABASE ---
if matched_stocks_data:
    print(f"\n💾 Saving {len(matched_stocks_data)} stocks to Database in one go...")
    supabase.table('swing_stocks').insert(matched_stocks_data).execute()

print(f"🎉 BOOM! Scan complete! Chartink ki tarah {saved_count} stocks ek jhatke mein save ho gaye.")
