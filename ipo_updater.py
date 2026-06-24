import os
import pandas as pd
from supabase import create_client, Client
import requests
import io
from datetime import datetime

# Supabase Connection
url_sb = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url_sb, key)

def update_ipo_master():
    print("🌐 NSE Official Server se Data fetch kar rahe hain...")
    url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }
    
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text))
        df.columns = df.columns.str.strip()
        df = df[df['SERIES'] == 'EQ']
        
        ipo_data = []
        for index, row in df.iterrows():
            symbol = str(row['SYMBOL']).strip()
            name = str(row['NAME OF COMPANY']).strip()
            list_date_str = str(row['DATE OF LISTING']).strip()
            
            try:
                date_obj = datetime.strptime(list_date_str, '%d-%b-%Y')
                formatted_date = date_obj.strftime('%Y-%m-%d')
                list_year = date_obj.year
                
                # 🚀 KADAM 1: STRICT FILTER - Sirf 2020 ya uske baad ke IPOs chahiye
                if list_year < 2020:
                    continue
                    
            except:
                continue 
                
            ipo_data.append({
                "stock_symbol": symbol,
                "company_name": name,
                "listing_date": formatted_date,
                "listing_year": list_year
            })
            
        print(f"📊 Total {len(ipo_data)} Premium IPOs mile (2020-Present). Database me save kar rahe hain...")
        
        # Database me clear entry ke liye purana data delete karke naya upsert karna
        chunk_size = 500
        for i in range(0, len(ipo_data), chunk_size):
            batch = ipo_data[i : i+chunk_size]
            supabase.table('ipo_master').upsert(batch).execute()
            
        print("🎉 IPO Master Table (2020+) successfully updated!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_ipo_master()
