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

# 2. Zerodha API se Master List nikalna (With SMART FILTER)
def get_full_nse_list():
    try:
        print("Zerodha API se list download kar rahe hain...")
        df = pd.read_csv("https://api.kite.trade/instruments", low_memory=False) 
        
        # THE MAGIC FILTER: lot_size == 1 (Isse saare SME aur kachra stocks bahar)
        df_nse = df[
            (df['exchange'] == 'NSE') & 
            (df['instrument_type'] == 'EQ') & 
            (df['lot_size'] == 1)
        ]
        
        nse_symbols = df_nse['tradingsymbol'].tolist()
        
        clean_symbols = []
        for s in nse_symbols:
            s = str(s)
            # Gold Bonds aur Govt Bonds saaf karna
            if '-SG' in s or '-SF' in s or '-SD' in s or '-GS' in s: continue
            if ' ' in s: continue
            if s.endswith("BEES") or "ETF" in s or "LIQUID" in s: continue
            clean_symbols.append(s)
            
        print(f"✅ Master Filter Applied: Kachra hatane ke baad strictly {len(clean_symbols)} premium stocks mil gaye!")
        return clean_symbols
    except Exception as e:
        print(f"⚠️ Error in Zerodha list: {e}")
        return ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ZOMATO"]

nse_stocks = get_full_nse_list()
stocks = [s + ".NS" for s in nse_stocks]

print(f"🚀 MASTERPLAN BATCH MODE: {len(stocks)} stocks ko 500-500 ke tukdo mein process kar rahe hain...\n")

matched_stocks_data = [] 
saved_count = 0
chunk_size = 500  # Ek baar mein sirf 500 stocks (Taaki Yahoo block na kare)

# 3. Batch Calculation (Har 500 stocks ka alag round)
for i in range(0, len(stocks), chunk_size):
    batch = stocks[i : i + chunk_size]
    print(f"📦 Downloading Batch {i//chunk_size + 1} ({len(batch)} stocks)...")
    
    try:
        # Sirf is batch ka data download karo
        batch_data = yf.download(batch, period="2y", interval="1d", threads=True, progress=False)

        # Check: Data proper table me aaya ya nahi
        if isinstance(batch_data.columns, pd.MultiIndex):
            close_df = batch_data['Close']
            high_df = batch_data['High']
            vol_df = batch_data['Volume']
        else:
            continue

        for ticker in batch:
            if ticker not in close_df.columns:
                continue

            close_data = close_df[ticker].dropna()
            high_data = high_df[ticker].dropna()
            vol_data = vol_df[ticker].dropna()

            # IPO Included: Sirf 22 din purana data chahiye
            if len(close_data) > 22:
                
                # min_periods=1 lagane se IPOs ka data theek se calculate hoga
                sma_200 = close_data.rolling(window=200, min_periods=1).mean()
                sma_50 = close_data.rolling(window=50, min_periods=1).mean()
                vol_sma_20 = vol_data.rolling(window=20, min_periods=1).mean()
                turnover_data = close_data * vol_sma_20
                
                close_22_ago = close_data.shift(22)
                close_66_ago = close_data.shift(66)
                max_high_252 = high_data.shift(1).rolling(window=252, min_periods=1).max()
                
                close = float(close_data.iloc[-1])
                sma_200_val = float(sma_200.iloc[-1])
                sma_50_val = float(sma_50.iloc[-1])
                turnover = float(turnover_data.iloc[-1])
                max_high = float(max_high_252.iloc[-1])
                
                # Agar stock naya hai (IPO), toh pichla data skip kar dega bina crash hue
                close_22 = float(close_22_ago.iloc[-1]) if pd.notna(close_22_ago.iloc[-1]) else 999999.0
                close_66 = float(close_66_ago.iloc[-1]) if pd.notna(close_66_ago.iloc[-1]) else 999999.0
                
                # --- AAPKE CHARTINK WALE STRICT RULES ---
                tech_cond1 = (close / close_22 > 1.2) and (turnover > 100000000) and (close > sma_200_val)
                tech_cond2 = (close / close_66 >= 1.3) and (close >= 1) and (turnover > 100000000) and (close > sma_200_val)
                tech_cond3 = (close > max_high * 0.75) and (close > sma_50_val) and (close > sma_200_val) and (turnover > 100000000)
                
                if tech_cond1 or tech_cond2 or tech_cond3:
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
        print(f"⚠️ Batch me koi error aaya, par aage badh rahe hain...")

# --- THE MAGIC: BULK INSERT TO DATABASE ---
if matched_stocks_data:
    print(f"\n💾 Saving {len(matched_stocks_data)} stocks to Database in one go...")
    supabase.table('swing_stocks').insert(matched_stocks_data).execute()

print(f"🎉 BOOM! Scan complete! Total {saved_count} stocks ek jhatke mein save ho gaye.")
