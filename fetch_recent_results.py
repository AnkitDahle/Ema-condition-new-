import os
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from supabase import create_client

# ==========================================
# 1. Supabase Connection
# ==========================================
url_sb = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url_sb or not key:
    print("⚠️ Supabase Credentials (URL ya KEY) nahi mile!")
    exit()

supabase = create_client(url_sb, key)

def get_hybrid_recent_results():
    today = datetime.now().date()
    ten_days_ago = today - timedelta(days=10)
    today_str = str(today)
    
    print(f"🔍 Fetching TODAY's ({today_str}) scanned stocks from 'swing_stocks' table...")
    try:
        res = supabase.table('swing_stocks').select('stock_symbol').eq('scan_date', today_str).execute()
        df = pd.DataFrame(res.data)
        
        if df.empty:
            print(f"⚠️ Aaj ({today_str}) ke liye database me koi stock save nahi hai.")
            return
            
        my_stocks = df['stock_symbol'].unique().tolist()
    except Exception as e:
        print(f"❌ Database error: {e}")
        return

    # ==========================================
    # 2. PHASE 1: TradingView (Fast Filter)
    # ==========================================
    print(f"\n⚡ PHASE 1: TradingView API par {len(my_stocks)} stocks fast-scan kar rahe hain...")
    
    tv_url = "https://scanner.tradingview.com/india/scan"
    tv_tickers = [f"NSE:{sym}" for sym in my_stocks]
    
    payload = {
        "symbols": {"tickers": tv_tickers},
        "columns": ["name", "earnings_release_date"]
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }
    
    tv_suspects = []
    
    try:
        response = requests.post(tv_url, json=payload, headers=headers)
        data = response.json()
        
        for item in data.get('data', []):
            stock_name = item['d'][0]
            earnings_ts = item['d'][1] 
            
            if earnings_ts:
                res_date = datetime.fromtimestamp(earnings_ts).date()
                if ten_days_ago <= res_date <= today:
                    tv_suspects.append(stock_name) # Is list me JGCHEM jaise fake stocks bhi honge
                    
    except Exception as e:
        print(f"❌ TradingView API Error: {e}")
        return

    # ==========================================
    # 3. PHASE 2: Yahoo Finance (The Truth Detector)
    # ==========================================
    recent_results = []
    
    if tv_suspects:
        print(f"\n🕵️‍♂️ PHASE 2: TV ne {len(tv_suspects)} stocks bataye. Ab Yfinance se jhooth pakad rahe hain...")
        
        for sym in tv_suspects:
            try:
                ticker = yf.Ticker(f"{sym}.NS")
                earnings_dates = ticker.earnings_dates
                
                is_real = False
                if earnings_dates is not None and not earnings_dates.empty:
                    for timestamp in earnings_dates.index:
                        yf_res_date = timestamp.date()
                        
                        # Agar Yfinance bhi confirm kare ki last 10 days me result aaya hai
                        if ten_days_ago <= yf_res_date <= today:
                            recent_results.append({
                                'scan_date': today_str,
                                'stock_symbol': sym,
                                'result_date': str(yf_res_date)
                            })
                            print(f"✅ 100% REAL: {sym} | Result Date: {yf_res_date}")
                            is_real = True
                            break 
                
                if not is_real:
                    print(f"🚫 FAKE REJECTED: {sym} (TV ne galat date di thi)")
            except Exception:
                print(f"🚫 ERROR/REJECTED: {sym} (YF par data nahi mila)")
    else:
        print("\n⚠️ TradingView ko hi koi recent result nahi mila.")

    # ==========================================
    # 4. Database Save 
    # ==========================================
    if recent_results:
        print(f"\n🧹 Clearing today's old result logs to prevent duplicates...")
        supabase.table('recent_results_log').delete().eq('scan_date', today_str).execute()
        
        print(f"💾 Saving {len(recent_results)} REAL records to Supabase...")
        for i in range(0, len(recent_results), 500):
            chunk = recent_results[i:i+500]
            supabase.table('recent_results_log').insert(chunk).execute()
            
        print("🎉 SUCCESS! 100% accurate results saved.")
    else:
        print("\n⚠️ Cross-verification ke baad koi bhi stock asli result wala nahi nikla.")

if __name__ == "__main__":
    get_hybrid_recent_results()
