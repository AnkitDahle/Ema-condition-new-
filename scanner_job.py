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

# 2. Zerodha API se Master List nikalna + Advance VIP Bouncer
def get_full_nse_list():
    try:
        print("Zerodha API se list download kar rahe hain...")
        # low_memory=False se Dtype warning nahi aayegi
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
        print(f"❌ Zerodha list fail hui: {e}. Backup use kar rahe hain.")
        return ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ZOMATO"]

nse_stocks = get_full_nse_list()
stocks = [s + ".NS" for s in nse_stocks]

print("Scanning started! (Looking for EXACTLY 5 Real Breakout Stocks)...")
saved_count = 0
checked_count = 0

# 3. Har stock ko check karna (Chartink Logic)
for ticker in stocks:
    
    # 🛑 SMART DUAL BRAKE SYSTEM
    if saved_count >= 5:
        print(f"\n🎯 Target Achieved: 5 Breakout stocks mil gaye! Scan yahin rok rahe hain.")
        break
    if checked_count >= 1000: # Limit badha di taaki 5 real stocks dhoondhne ka time mile
        print(f"\n🛑 Safety Brake: 1000 stocks check kar liye. Ab aage nahi jayenge.")
        break
        
    checked_count += 1

    try:
        # THE MAGIC FIX: yf.Ticker().history() use kiya bajaye download() ke
        stock_obj = yf.Ticker(ticker)
        data = stock_obj.history(period="2y", interval="1d")
        
        if len(data) > 252:
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            data['Vol_SMA_20'] = data['Volume'].rolling(window=20).mean()
            data['Turnover'] = data['Close'] * data['Vol_SMA_20']
            
            data['Close_22_ago'] = data['Close'].shift(22)
            data['Close_66_ago'] = data['Close'].shift(66)
            data['Max_High_252'] = data['High'].shift(1).rolling(window=252).max()
            
            latest = data.iloc[-1]
            
            # Format clean hone se ab calculations bhi choti aur error-free ho gayi
            close = float(latest['Close'])
            close_22 = float(latest['Close_22_ago'])
            close_66 = float(latest['Close_66_ago'])
            sma_200 = float(latest['SMA_200'])
            sma_50 = float(latest['SMA_50'])
            turnover = float(latest['Turnover'])
            max_high_252 = float(latest['Max_High_252'])
            
            tech_cond1 = (close / close_22 > 1.2) and (turnover > 100000000) and (close > sma_200)
            tech_cond2 = (close / close_66 >= 1.3) and (close >= 1) and (turnover > 100000000) and (close > sma_200)
            tech_cond3 = (close > max_high_252 * 0.75) and (close > sma_50) and (close > sma_200) and (turnover > 100000000)
            
            if tech_cond1 or tech_cond2 or tech_cond3:
                try:
                    # Ticker object already bana hua hai
                    raw_mcap = stock_obj.info.get('marketCap', 15000000000)
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
                    
                    print(f"🔥 Found Breakout: {symbol_clean} - {condition_str}")
                    saved_count += 1
    except Exception as e:
        pass

print(f"🎉 Scan complete! {checked_count} stocks check huye, aur {saved_count} stocks Supabase mein save huye.")
