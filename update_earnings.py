import os
import pandas as pd
import yfinance as yf
from supabase import create_client
from datetime import datetime, timedelta

# 1. Supabase Connection (GitHub Secrets se details aayengi)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def update_earnings():
    print("Fetching symbols from Supabase...")
    
    # 2. Database se Scanner wale stocks uthana (taki faltu stocks ka time waste na ho)
    master_symbols = ["TCS", "RELIANCE", "INFY", "HDFCBANK", "ICICIBANK", "ZOMATO", "HAL", "BHEL"] 
    try:
        response = supabase.table('swing_stocks').select('stock_symbol').execute()
        if response.data:
            master_symbols.extend([row['stock_symbol'] for row in response.data])
    except Exception as e:
        print("Warning: swing_stocks table se data nahi aaya.")
        
    unique_symbols = list(set(master_symbols))
    upcoming_earnings = []
    
    today = datetime.now().date()
    next_45_days = today + timedelta(days=45)

    print(f"Checking earnings for {len(unique_symbols)} stocks via Yahoo Finance...")
    
    # 3. Har stock ki upcoming result date check karna
    for sym in unique_symbols:
        try:
            # Indian stocks ke liye .NS lagana zaroori hai
            ticker = yf.Ticker(f"{sym}.NS")
            dates = ticker.get_earnings_dates(limit=2)
            
            if dates is not None and not dates.empty:
                for index, row in dates.iterrows():
                    # Yahoo finance index return karta hai timezone format mein
                    earning_date = index.date()
                    if today <= earning_date <= next_45_days:
                        upcoming_earnings.append({
                            'stock_symbol': sym,
                            'result_date': str(earning_date)
                        })
                        print(f"✅ Found Upcoming Result: {sym} -> {earning_date}")
                        break # Ek bar future date mil gayi, toh next stock par badhein
        except Exception as e:
            pass # Agar Yahoo par data nahi mila toh chupchap skip kar dega

    # 4. Supabase mein Table Update Karna
    if upcoming_earnings:
        print("Clearing old calendar data...")
        # Purana sara data delete karega (taaki duplicacy na ho)
        supabase.table('earnings_calendar').delete().gt('id', -1).execute()
        
        print(f"Inserting {len(upcoming_earnings)} new upcoming results...")
        supabase.table('earnings_calendar').insert(upcoming_earnings).execute()
        print("🎉 Earnings Calendar 100% Updated Successfully!")
    else:
        print("No upcoming earnings found in the next 45 days.")

if __name__ == "__main__":
    update_earnings()
