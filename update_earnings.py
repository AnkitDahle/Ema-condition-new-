import requests
import pandas as pd
from datetime import datetime, timedelta
import os
from supabase import create_client

# 1. Supabase Connection 
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def get_tradingview_earnings(symbol_list):
    print(f"Fetching earnings for {len(symbol_list)} stocks from TradingView API...")
    
    tv_url = "https://scanner.tradingview.com/india/scan"
    tv_tickers = [f"NSE:{sym}" for sym in symbol_list]
    
    payload = {
        "symbols": {"tickers": tv_tickers},
        "columns": ["name", "earnings_release_next_date"]
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json"
    }
    
    upcoming_earnings = []
    today = datetime.now().date()
    next_30_days = today + timedelta(days=30)
    
    try:
        response = requests.post(tv_url, json=payload, headers=headers)
        data = response.json()
        
        for item in data.get('data', []):
            stock_name = item['d'][0]
            earnings_ts = item['d'][1] 
            
            if earnings_ts:
                actual_result_date = datetime.fromtimestamp(earnings_ts).date()
                
                # 🌟 LOGIC SHIFT: Agar result aaj se 30 din ke andar hai
                if today <= actual_result_date <= next_30_days:
                    upcoming_earnings.append({
                        'stock_symbol': stock_name,
                        # 🌟 SMART HACK: Asli result date ki jagah Aaj ki Scan Date save kar rahe hain
                        'result_date': str(today) 
                    })
        return upcoming_earnings
    except Exception as e:
        print(f"TradingView API Error: {e}")
        return []

def update_earnings():
    print("Fetching your unique stocks from AlphaSwing database...")
    try:
        res = supabase.table('swing_stocks').select('stock_symbol').execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            my_stocks = df['stock_symbol'].unique().tolist()
        else:
            my_stocks = ["RELIANCE", "TCS", "INFY", "ZOMATO"]
    except Exception as e:
        print(f"Database error: {e}")
        my_stocks = ["RELIANCE", "TCS", "INFY", "ZOMATO"]

    upcoming_earnings = get_tradingview_earnings(my_stocks)
    
    if upcoming_earnings:
        unique_earnings = {v['stock_symbol']: v for v in upcoming_earnings}.values()
        final_list = list(unique_earnings)

        today_str = str(datetime.now().date())

        print(f"✅ Found {len(final_list)} stocks with results in the next 30 days!")
        
        # 🌟 LOGIC SHIFT: Sirf aaj ki scan date wala data delete hoga (Purana data safe rahega)
        print("Clearing today's previous scans (Historical data remains safe)...")
        supabase.table('earnings_calendar').delete().eq('result_date', today_str).execute()
        
        print("Pushing fresh data to AlphaSwing with Time Machine support...")
        for i in range(0, len(final_list), 500):
            chunk = final_list[i:i+500]
            supabase.table('earnings_calendar').insert(chunk).execute()
            
        print("🎉 Earnings Calendar Updated Successfully!")
    else:
        print("⚠️ No upcoming earnings found for your stocks in the next 30 days.")

if __name__ == "__main__":
    update_earnings()
