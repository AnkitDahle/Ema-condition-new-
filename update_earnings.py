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
    # Chrome Browser jaisi identity (Taki NSE block na kare)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    session = requests.Session()
    session.headers.update(headers)

    try:
        print("Bypassing NSE Security (Fetching cookies)...")
        # Pehle homepage hit karke asali user (cookie) banenge
        session.get("https://www.nseindia.com", timeout=15)
        time.sleep(2) # Thoda wait taki human jaisa lage
        
        print("Extracting live Board Meetings data from NSE...")
        # Direct API jahan result dates aati hain
        api_url = "https://www.nseindia.com/api/corporate-board-meetings"
        response = session.get(api_url, timeout=15)
        data = response.json()

        upcoming_earnings = []
        today = datetime.now().date()
        
        print("Filtering Financial Results...")
        for item in data:
            purpose = str(item.get('purpose', '')).lower()
            # Sirf wo meetings jinka purpose "Result" (Earnings) hai
            if 'result' in purpose:
                symbol = item.get('symbol')
                date_str = item.get('bm_date') # Format: 25-Jul-2026
                try:
                    # Date ko proper format (YYYY-MM-DD) mein convert karna
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
        # Duplicates hatane ke liye
        unique_earnings = {v['stock_symbol']: v for v in upcoming_earnings}.values()
        final_list = list(unique_earnings)

        print(f"✅ Found {len(final_list)} upcoming earnings strictly from NSE!")
        
        print("Clearing old calendar data in Supabase...")
        supabase.table('earnings_calendar').delete().gt('id', -1).execute()
        
        print("Pushing fresh data to AlphaSwing...")
        # Database mein daalne ka logic (Chunks mein taki overload na ho)
        for i in range(0, len(final_list), 500):
            chunk = final_list[i:i+500]
            supabase.table('earnings_calendar').insert(chunk).execute()
            
        print("🎉 Earnings Calendar 100% Fully Automated via NSE India!")
    else:
        print("⚠️ No earnings data fetched. Might be weekend or no upcoming results.")

if __name__ == "__main__":
    update_earnings()
