import os
import yfinance as yf
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import logging

# Yahoo Finance ke faltu error messages ko mute karna
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
            
        print(f"✅ Success: Kachra hatane ke baad {len(clean_symbols)} pure stocks mil gaye!")
        return clean_symbols
    except Exception as e:
        return ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ZOMATO"]

nse_stocks = get_full_nse_list()
stocks = [s + ".NS" for s in nse_stocks]

print(f"Scanning started! (Full Market Scan for {len(stocks)} Stocks)...")
saved_count = 0
checked_count = 0

# 3. Har stock ko check karna
for ticker in stocks:
    checked_count += 1
    
    # Progress Track Karne Ke Liye (Har 100 stocks baad terminal me batayega)
    if checked_count % 100 == 0:
        print(f"⏳ Progress: {checked_count} stocks checked... Found {saved_count} Breakouts so far.")

    try:
        # Faltu red warnings hatane ke liye show_errors=False
        data = yf.download(ticker, period="2y", interval="1d", progress=False, show_errors=False)
        
        if len(data) > 252:
            # THE SQUEEZE FIX: Yahoo ke naye format ko flat (1D) karne ka masterstroke
            close_data = data['Close'].squeeze()
            vol_data = data['Volume'].squeeze()
            high_data = data['High'].squeeze()

            # Ab calculations ekdum fast aur bina kisi DataFrame error ke hongi
            sma_200 = close_data.rolling(window=200).mean()
            sma_50 = close_data.rolling(window=50).mean()
            vol_sma_20 = vol_data.rolling(window=20).mean()
            turnover_data = close_data * vol_sma_20
            
            close_22_ago = close_data.shift(22)
            close_66_ago = close_data.shift(66)
            max_high_252 = high_data.shift(1).rolling(window=252).max()
            
            # Aakhri din ka data float (number) mein convert karna
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
                    
                    supabase.table('swing_stocks').insert({
                        "scan_date": today_date,
                        "stock_symbol": symbol_clean,
                        "close_price": round(close, 2),
                        "turnover_cr": round(turnover / 10000000, 2),
                        "condition_matched": condition_str
                    }).execute()
                    
                    saved_count += 1
    except Exception as e:
        pass

print(f"🎉 Full Market Scan complete! {checked_count} stocks check huye, aur Chartink ki tarah {saved_count} stocks Supabase mein save huye.")
