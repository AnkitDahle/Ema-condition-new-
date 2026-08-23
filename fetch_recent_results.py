import os
import requests
import pandas as pd
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

def get_recent_results_from_tv():
    today = datetime.now().date()
    
    # 🌟 50 Din ka naya filter (Updated from 10)
    fifty_days_ago = today - timedelta(days=50)
    today_str = str(today)
    
    print(f"🔍 Fetching TODAY's ({today_str}) scanned stocks from 'swing_stocks' table...")
    try:
        # 🌟 Sirf aaj ke scan_date wale stocks uthana
        res = supabase.table('swing_stocks').select('stock_symbol').eq('scan_date', today_str).execute()
        df = pd.DataFrame(res.data)
        
        if df.empty:
            print(f"⚠️ Aaj ({today_str}) ke liye database me koi stock save nahi hai. (Pehle scanner script run karein).")
            return
            
        my_stocks = df['stock_symbol'].unique().tolist()
        print(f"✅ Aaj scan hue {len(my_stocks)} stocks database se successfully fetch ho gaye!")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return

    # ==========================================
    # 2. TradingView API Logic
    # ==========================================
    print(f"\n🌐 TradingView API par in {len(my_stocks)} stocks ka data (Last 50 Days) check kar rahe hain...")
    
    tv_url = "https://scanner.tradingview.com/india/scan"
    
    # Symbols ko TradingView format (NSE:SYMBOL) me convert karna
    tv_tickers = [f"NSE:{sym}" for sym in my_stocks]
    
    # 'earnings_release_date' = Pichla/Current Result Date
    payload = {
        "symbols": {"tickers": tv_tickers},
        "columns": ["name", "earnings_release_date"]
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json"
    }
    
    recent_results = []
    
    try:
        response = requests.post(tv_url, json=payload, headers=headers)
        data = response.json()
        
        for item in data.get('data', []):
            stock_name = item['d'][0]
            earnings_ts = item['d'][1] # Timestamp
            
            if earnings_ts:
                # UNIX Timestamp ko readable Date me convert karna
                res_date = datetime.fromtimestamp(earnings_ts).date()
                
                # 🔥 Asli Jadoo Yahan Hai: Agar result pichle 50 din me (ya aaj) aaya hai
                if fifty_days_ago <= res_date <= today:
                    recent_results.append({
                        'scan_date': today_str,
                        'stock_symbol': stock_name,
                        'result_date': str(res_date)
                    })
                    print(f"🎯 MATCH FOUND: {stock_name} | Result Date: {res_date}")
                    
    except Exception as e:
        print(f"❌ TradingView API Error: {e}")
        return

    # ==========================================
    # 3. Database Save (Time Machine Logic)
    # ==========================================
    if recent_results:
        print(f"\n🧹 Clearing today's old result logs to prevent duplicates...")
        supabase.table('recent_results_log').delete().eq('scan_date', today_str).execute()
        
        print(f"💾 Saving {len(recent_results)} records to Supabase...")
        for i in range(0, len(recent_results), 500):
            chunk = recent_results[i:i+500]
            supabase.table('recent_results_log').insert(chunk).execute()
            
        print("🎉 SUCCESS! Recent results saved Date-Wise in database.")
    else:
        print("\n⚠️ Pichle 50 din me inme se kisi bhi stock ka result announce nahi hua hai.")

if __name__ == "__main__":
    get_recent_results_from_tv()
