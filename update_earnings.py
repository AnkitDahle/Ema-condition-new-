import os
import pandas as pd
import yfinance as yf
from supabase import create_client
from datetime import datetime, timedelta

# 1. Supabase Connection 
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def update_earnings():
    print("Fetching ALL symbols from Supabase (Bypassing Limits)...")
    
    master_symbols = ["TCS", "RELIANCE", "INFY", "HDFCBANK", "ICICIBANK", "ZOMATO", "HAL", "BHEL"] 
    
    # 🔥 Pagination Loop (Taaki 1000 limit cross karke saara data aaye)
    limit = 1000
    offset = 0
    while True:
        try:
            response = supabase.table('swing_stocks').select('stock_symbol').range(offset, offset + limit - 1).execute()
            if not response.data:
                break
            master_symbols.extend([row['stock_symbol'] for row in response.data])
            if len(response.data) < limit:
                break
            offset += limit
        except Exception as e:
            print(f"Warning: Chunk fetch error at {offset} - {e}")
            break
            
    unique_symbols = list(set(master_symbols))
    upcoming_earnings = []
    
    today = datetime.now().date()
    next_45_days = today + timedelta(days=45)

    print(f"Total Unique Stocks Found: {len(unique_symbols)}")
    print("Checking earnings for all stocks via Yahoo Finance...")
    
    for sym in unique_symbols:
        try:
            ticker = yf.Ticker(f"{sym}.NS")
            dates = ticker.get_earnings_dates(limit=2)
            
            if dates is not None and not dates.empty:
                for index, row in dates.iterrows():
                    earning_date = index.date()
                    if today <= earning_date <= next_45_days:
                        upcoming_earnings.append({
                            'stock_symbol': sym,
                            'result_date': str(earning_date)
                        })
                        print(f"✅ Upcoming Result: {sym} -> {earning_date}")
                        break 
        except Exception as e:
            pass 

    if upcoming_earnings:
        print("Clearing old calendar data...")
        supabase.table('earnings_calendar').delete().gt('id', -1).execute()
        
        print(f"Inserting {len(upcoming_earnings)} new upcoming results...")
        supabase.table('earnings_calendar').insert(upcoming_earnings).execute()
        print("🎉 Earnings Calendar 100% Updated Successfully!")
    else:
        print("No upcoming earnings found.")

if __name__ == "__main__":
    update_earnings()
