import requests
import os
from datetime import datetime
from supabase import create_client

# Supabase Connection 
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def get_tv_count(filter_condition):
    tv_url = "https://scanner.tradingview.com/india/scan"
    
    # TV Backend Payload: NSE ke saare primary stocks ko scan karega
    payload = {
        "filter": [
            {"left": "type", "operation": "equal", "right": "stock"},
            {"left": "exchange", "operation": "equal", "right": "NSE"},
            {"left": "is_primary", "operation": "equal", "right": True},
            {"left": "active_symbol", "operation": "equal", "right": True},
            filter_condition
        ],
        "options": {"lang": "en"},
        "markets": ["india"],
        "symbols": {"query": {"types": []}},
        "columns": ["name"],
        "range": [0, 1] # Humein sirf Total Count chahiye, stocks ke naam nahi
    }
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        response = requests.post(tv_url, json=payload, headers=headers, timeout=10)
        data = response.json()
        return data.get('totalCount', 0)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return 0

def update_market_breadth():
    print("Fetching Market Breadth from TradingView...")
    
    # 1. Calculate counts using Simple Moving Averages (SMA)
    above_20 = get_tv_count({"left": "close", "operation": "greater", "right": "SMA20"})
    below_20 = get_tv_count({"left": "close", "operation": "less", "right": "SMA20"})
    
    above_50 = get_tv_count({"left": "close", "operation": "greater", "right": "SMA50"})
    below_50 = get_tv_count({"left": "close", "operation": "less", "right": "SMA50"})
    
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    data_to_insert = {
        "date": today_date,
        "above_20dma": above_20,
        "below_20dma": below_20,
        "above_50dma": above_50,
        "below_50dma": below_50
    }
    
    if above_20 > 0: # Ensure valid data before saving
        # Upsert function taaki agar din mein 2 baar chale toh nayi row banne ki jagah update ho
        supabase.table('market_breadth').upsert(data_to_insert).execute()
        print(f"✅ Market Breadth Saved for {today_date}: {data_to_insert}")
    else:
        print("⚠️ No data fetched. API might be down.")

if __name__ == "__main__":
    update_market_breadth()
