import os
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

def get_results_from_yahoo():
    print("🔍 Fetching your scanned stocks from 'swing_stocks' table...")
    try:
        res = supabase.table('swing_stocks').select('stock_symbol').execute()
        df = pd.DataFrame(res.data)
        if df.empty:
            print("⚠️ Database me koi stock save nahi hai.")
            return
        my_stocks = df['stock_symbol'].unique().tolist()
    except Exception as e:
        print(f"❌ Database error: {e}")
        return

    today = datetime.now().date()
    three_days_ago = today - timedelta(days=3)
    today_str = str(today)
    
    recent_results = []
    
    print(f"🌐 Yahoo Finance par {len(my_stocks)} stocks ka data check kar rahe hain. Please wait...")
    
    for sym in my_stocks:
        try:
            # NSE ke liye symbol ke aage .NS lagana padta hai
            ticker = yf.Ticker(f"{sym}.NS")
            earnings_dates = ticker.earnings_dates
            
            if earnings_dates is not None and not earnings_dates.empty:
                for timestamp in earnings_dates.index:
                    res_date = timestamp.date()
                    
                    # Agar result pichle 3 din (ya aaj) me aaya hai
                    if three_days_ago <= res_date <= today:
                        recent_results.append({
                            'scan_date': today_str,
                            'stock_symbol': sym,
                            'result_date': str(res_date)
                        })
                        print(f"🎯 MATCH FOUND: {sym} | Result: {res_date}")
                        break # Ek match mila toh aage badho
        except Exception:
            pass # Yahoo par data missing hone par error skip karega

    # ==========================================
    # 2. Database Save (Time Machine Logic)
    # ==========================================
    if recent_results:
        print(f"\n🧹 Clearing today's old scans to prevent duplicates...")
        supabase.table('recent_results_log').delete().eq('scan_date', today_str).execute()
        
        print(f"💾 Saving {len(recent_results)} records to Supabase...")
        for i in range(0, len(recent_results), 500):
            chunk = recent_results[i:i+500]
            supabase.table('recent_results_log').insert(chunk).execute()
            
        print("🎉 SUCCESS! Recent results saved Date-Wise in database.")
    else:
        print("\n⚠️ Pichle 3 din me kisi bhi scanned stock ka result nahi aaya.")

if __name__ == "__main__":
    get_results_from_yahoo()
