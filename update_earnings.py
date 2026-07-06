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

def get_nse_earnings():
    # Chrome Browser jaisi identity
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    session = requests.Session()
    session.headers.update(headers)

    try:
        print("Bypassing NSE Security (Fetching cookies)...")
        session.get("https://www.nseindia.com", timeout=15)
        time.sleep(2) 
        
        print("Extracting live Board Meetings data from NSE...")
        api_url = "https://www.nseindia.com/api/corporate-board-meetings"
        response = session.get(api_url, timeout=15)
        raw_data = response.json()

        # 🔥 THE FIX: NSE data ko ek 'data' naam ki dictionary key mein pack karke bhejta hai
        meeting_list = raw_data.get("data", []) if isinstance(raw_data, dict) else raw_data

        upcoming_earnings = []
        today = datetime.now().date()
        
        print(f"Filtering {len(meeting_list)} Financial Results...")
        for item in meeting_list:
            # Extra safety check
            if isinstance(item, dict):
                purpose = str(item.get('purpose', '')).lower()
                # 'result' ya 'financial' keyword ko dhundhna
                if 'result' in purpose or 'financial' in purpose:
                    symbol = item.get('symbol')
                    date_str = item.get('bm_date') 
                    try:
                        if date_str:
                            meeting_date = datetime.strptime(date_str, "%d-%b-%Y").date()
                            if meeting_date >= today:
                                upcoming_earnings.append({
                                    'stock_symbol': symbol,
                                    'result_date': str(meeting_date)
                                })
                    except Exception as e:
                        pass
        
        return upcoming_earnings
    except Exception as e:
        print(f"Error Fetching from NSE: {e}")
        return []

def update_earnings():
    upcoming_earnings = get_nse_earnings()
    
    if upcoming_earnings:
        # Duplicates hatana (Agar ek hi company ki meeting 2 baar list hui ho)
        unique_earnings = {v['stock_symbol']: v for v in upcoming_earnings}.values()
        final_list = list(unique_earnings)

        print(f"✅ Found {len(final_list)} upcoming earnings strictly from NSE!")
        
        print("Clearing old calendar data in Supabase...")
        supabase.table('earnings_calendar').delete().gt('id', -1).execute()
        
        print("Pushing fresh data to AlphaSwing...")
        for i in range(0, len(final_list), 500):
            chunk = final_list[i:i+500]
            supabase.table('earnings_calendar').insert(chunk).execute()
            
        print("🎉 Earnings Calendar 100% Fully Automated via NSE India!")
    else:
        print("⚠️ No earnings data fetched. Might be weekend or no upcoming results.")

if __name__ == "__main__":
    update_earnings()
