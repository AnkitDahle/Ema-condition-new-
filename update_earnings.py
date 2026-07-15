import requests
import pandas as pd
from datetime import datetime
import os
from supabase import create_client
import time

# 1. Supabase Connection 
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def get_tradingview_earnings(symbol_list):
    print(f"Fetching earnings for {len(symbol_list)} stocks from TradingView API...")
    
    # TradingView ka hidden scanner API
    tv_url = "https://scanner.tradingview.com/india/scan"
    
    # Symbols ko TradingView format (NSE:SYMBOL) mein convert karna
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
    
    try:
        response = requests.post(tv_url, json=payload, headers=headers)
        data = response.json()
        
        for item in data.get('data', []):
            stock_name = item['d'][0]
            earnings_ts = item['d'][1] # TradingView UNIX timestamp bhejta hai
            
            if earnings_ts:
                # Timestamp ko proper Date mein badalna
                result_date = datetime.fromtimestamp(earnings_ts).date()
                
                # Sirf future (aane wali) dates ko list mein rakhna
                if result_date >= today:
                    upcoming_earnings.append({
                        'stock_symbol': stock_name,
                        'result_date': str(result_date)
                    })
        return upcoming_earnings
    except Exception as e:
        print(f"TradingView API Error: {e}")
        return []

def update_earnings():
    print("Fetching your unique stocks from AlphaSwing database...")
    try:
        # Aapke unhi stocks ko filter karega jo aapne scan kiye hain
        res = supabase.table('swing_stocks').select('stock_symbol').execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            my_stocks = df['stock_symbol'].unique().tolist()
        else:
            # Agar scanner khali ho toh Nifty 50 default
            my_stocks = ["RELIANCE", "TCS", "INFY", "ZOMATO", "HDFCBANK", "ICICIBANK", "SBIN"]
    except Exception as e:
        print(f"Database error: {e}")
        my_stocks = ["RELIANCE", "TCS", "INFY", "ZOMATO"]

    # TradingView se dates nikalna
    upcoming_earnings = get_tradingview_earnings(my_stocks)
    
    if upcoming_earnings:
        # Duplicates hatana
        unique_earnings = {v['stock_symbol']: v for v in upcoming_earnings}.values()
        final_list = list(unique_earnings)

        print(f"✅ Found {len(final_list)} upcoming earnings from TradingView!")
        
        print("Clearing old calendar data in Supabase...")
        supabase.table('earnings_calendar').delete().gt('id', -1).execute()
        
        print("Pushing fresh data to AlphaSwing...")
        for i in range(0, len(final_list), 500):
            chunk = final_list[i:i+500]
            supabase.table('earnings_calendar').insert(chunk).execute()
            
        print("🎉 Earnings Calendar 100% Fully Automated via TradingView!")
    else:
        print("⚠️ No upcoming earnings found for your stocks in the next few days.")

if __name__ == "__main__":
    update_earnings()
