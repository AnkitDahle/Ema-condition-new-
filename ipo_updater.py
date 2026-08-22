import os
import pandas as pd
from supabase import create_client, Client
import requests
import io
from datetime import datetime
import yfinance as yf
import warnings

# Faltu yfinance warnings ko chup karana
warnings.filterwarnings('ignore')

# Supabase Connection
url_sb = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url_sb or not key:
    print("⚠️ Supabase Credentials (URL ya KEY) nahi mile!")
    exit()

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
        
        suspect_ipos = []
        for index, row in df.iterrows():
            symbol = str(row['SYMBOL']).strip()
            name = str(row['NAME OF COMPANY']).strip()
            list_date_str = str(row['DATE OF LISTING']).strip()
            
            try:
                date_obj = datetime.strptime(list_date_str, '%d-%b-%Y')
                list_year = date_obj.year
                
                # Pehla Filter: Jo NSE ke hisaab se 2020+ hain
                if list_year >= 2020:
                    suspect_ipos.append({
                        "stock_symbol": symbol,
                        "company_name": name,
                        "nse_date": date_obj
                    })
            except:
                continue 
                
        print(f"📊 NSE ne bataye {len(suspect_ipos)} stocks (2020+). Ab inka kachra saaf karenge...\n")
        
        # ==========================================
        # 🕵️‍♂️ THE TRUTH DETECTOR (BSE & SME MIGRATION CHECK)
        # ==========================================
        ns_tickers = [f"{item['stock_symbol']}.NS" for item in suspect_ipos]
        bo_tickers = [f"{item['stock_symbol']}.BO" for item in suspect_ipos]
        all_tickers = ns_tickers + bo_tickers
        
        print(f"⚡ Yahoo Finance se history check kar rahe hain (It takes ~15 seconds)...")
        # Threads use karke bulk me sabka purana data nikalna
        data = yf.download(all_tickers, period="max", threads=True, progress=False)
        
        if isinstance(data.columns, pd.MultiIndex):
            close_df = data['Close']
        else:
            close_df = data
            
        genuine_ipos = []
        rejected_count = 0
        
        for item in suspect_ipos:
            sym = item['stock_symbol']
            ns_sym = f"{sym}.NS"
            bo_sym = f"{sym}.BO"
            
            # Pata lagao ki NSE aur BSE par inka sabse pehla trading din kaunsa tha
            first_ns = close_df[ns_sym].first_valid_index() if ns_sym in close_df.columns else None
            first_bo = close_df[bo_sym].first_valid_index() if bo_sym in close_df.columns else None
            
            earliest_dates = []
            if first_ns: earliest_dates.append(first_ns)
            if first_bo: earliest_dates.append(first_bo)
            
            if earliest_dates:
                # Stock ka asli janam din (True IPO Date)
                true_ipo_date = min(earliest_dates)
                
                # Agar uski asli history 2020 se purani hai, toh wo MIGRATED stock hai!
                if true_ipo_date.year < 2020:
                    # Print karke dekh lo kaunse dhokebaaz pakde gaye
                    print(f"🚫 REJECTED: {sym} (Asal me {true_ipo_date.year} me list hua tha)")
                    rejected_count += 1
                    continue
                else:
                    final_date = true_ipo_date.strftime('%Y-%m-%d')
                    final_year = true_ipo_date.year
            else:
                # Agar Yahoo par data na mile (bohot naya IPO ho), toh NSE wali date maan lo
                final_date = item['nse_date'].strftime('%Y-%m-%d')
                final_year = item['nse_date'].year
                
            # Filter pass karne wale Genuine IPOs
            genuine_ipos.append({
                "stock_symbol": sym,
                "company_name": item['company_name'],
                "listing_date": final_date,
                "listing_year": final_year
            })
            
        print(f"\n✅ Truth Detector Result: {rejected_count} Migrated/Fake IPOs bahar nikal diye gaye!")
        print(f"💾 Total {len(genuine_ipos)} GENUINE IPOs Database me save kar rahe hain...")
        
        # Database me clear entry ke liye purana data upsert karna
        if genuine_ipos:
            chunk_size = 500
            for i in range(0, len(genuine_ipos), chunk_size):
                batch = genuine_ipos[i : i+chunk_size]
                supabase.table('ipo_master').upsert(batch).execute()
                
            print("🎉 IPO Master Table (100% Genuine 2020+) successfully updated!")
        else:
            print("⚠️ Koi data save nahi hua.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_ipo_master()
