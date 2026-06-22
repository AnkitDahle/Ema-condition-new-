import os
import yfinance as yf
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import logging

# Faltu warnings ko mute karna
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
pd.options.mode.chained_assignment = None

# 1. Supabase Connection
url_sb = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url_sb, key)

today_date = datetime.now().strftime("%Y-%m-%d")

# 2. Zerodha API List + VIP Bouncer
def get_full_nse_list():
    try:
        print("Zerodha API se list download kar rahe hain...")
        # low_memory=False lagaya taaki DtypeWarning na aaye
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
            
        print(f"✅ Success: {len(clean_symbols)} pure stocks mil gaye!")
        return clean_symbols
    except Exception as e:
        return ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ZOMATO"]

stocks = [s + ".NS" for s in get_full_nse_list()]

print("Scanning started! (ACID TEST MODE: Easy Conditions for Testing)...")
saved_count = 0
checked_count = 0

# 3. Har stock ko check karna (Acid Test Logic)
for ticker in stocks:
    
    # 🛑 Dual Brake System
    if saved_count >= 5:
        print(f"\n🎯 Target Achieved: 5 stocks mil gaye! Code 100% OK hai.")
        break
    if checked_count >= 500:
        print(f"\n🛑 Safety Brake: 500 check huye. Agar yahan 0 hai, toh code check karna padega.")
        break
        
    checked_count += 1

    try:
        data = yf.download(ticker, period="2y", interval="1d", progress=False, show_errors=False)
        
        if len(data) > 252:
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['Vol_SMA_20'] = data['Volume'].rolling(window=20).mean()
            data['Turnover'] = data['Close'] * data['Vol_SMA_20']
            
            latest = data.iloc[-1]
            close = float(latest['Close'].iloc[0] if isinstance(latest['Close'], pd.Series) else latest['Close'])
            sma_200 = float(latest['SMA_200'].iloc[0] if isinstance(latest['SMA_200'], pd.Series) else latest['SMA_200'])
            turnover = float(latest['Turnover'].iloc[0] if isinstance(latest['Turnover'], pd.Series) else latest['Turnover'])
            
            # --- SUPER EASY CONDITIONS FOR TESTING ---
            # Condition: Stock price 50 rupaye se upar ho, 200 EMA ke upar ho, aur Turnover > 1 Crore (10000000) ho
            test_cond = (close > 50) and (close > sma_200) and (turnover > 10000000)
            
            if test_cond:
                symbol_clean = ticker.replace(".NS", "")
                
                supabase.table('swing_stocks').insert({
                    "scan_date": today_date,
                    "stock_symbol": symbol_clean,
                    "close_price": round(close, 2),
                    "turnover_cr": round(turnover / 10000000, 2), # In Crores
                    "condition_matched": "Test Pass (Above 200 EMA)"
                }).execute()
                
                print(f"🔥 Code is Working: {symbol_clean} Pass ho gaya!")
                saved_count += 1
    except:
        pass

print(f"🎉 Acid Test complete! {checked_count} stocks check huye, aur {saved_count} stocks save huye.")
