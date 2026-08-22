import os
import pandas as pd
from supabase import create_client, Client
import requests
import io
from datetime import datetime
import yfinance as yf
import warnings

warnings.filterwarnings('ignore')

url_sb = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url_sb or not key:
    print("⚠️ Supabase Credentials (URL ya KEY) nahi mile!")
    exit()

supabase: Client = create_client(url_sb, key)

def update_ipo_master_bulk():
    print("🌐 NSE Official Server se Data fetch kar rahe hain...")
    url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
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
                # 🌟 BULK FILTER: 2020 se aaj tak ke saare stocks
                if date_obj.year >= 2020:
                    suspect_ipos.append({
                        "stock_symbol": symbol,
                        "company_name": name,
                        "nse_date": date_obj
                    })
            except:
                continue 
                
        print(f"📊 NSE ne bataye {len(suspect_ipos)} stocks (2020+). Ab verify kar rahe hain...\n")
        
        ns_tickers = [f"{item['stock_symbol']}.NS" for item in suspect_ipos]
        bo_tickers = [f"{item['stock_symbol']}.BO" for item in suspect_ipos]
        all_tickers = ns_tickers + bo_tickers
        
        print(f"⚡ History check kar rahe hain (It takes ~15-20 seconds)...")
        data = yf.download(all_tickers, period="max", threads=True, progress=False)
        
        close_df = data['Close'] if isinstance(data.columns, pd.MultiIndex) else data
            
        genuine_ipos = []
        rejected_count = 0
        
        for item in suspect_ipos:
            sym = item['stock_symbol']
            nse_official_date = item['nse_date'].date()
            
            ns_sym = f"{sym}.NS"
            bo_sym = f"{sym}.BO"
            
            first_ns = close_df[ns_sym].first_valid_index() if ns_sym in close_df.columns else None
            first_bo = close_df[bo_sym].first_valid_index() if bo_sym in close_df.columns else None
            
            yf_dates = []
            if first_ns: yf_dates.append(pd.to_datetime(first_ns).date())
            if first_bo: yf_dates.append(pd.to_datetime(first_bo).date())
            
            is_migrated = False
            if yf_dates:
                oldest_yf_date = min(yf_dates)
                
                # 30-Day Rule (BSE/SME se migrate hue stocks ko nikalne ke liye)
                if (nse_official_date - oldest_yf_date).days > 30:
                    is_migrated = True
                if oldest_yf_date.year < 2020:
                    is_migrated = True
            
            if is_migrated:
                rejected_count += 1
                continue
                
            genuine_ipos.append({
                "stock_symbol": sym,
                "company_name": item['company_name'],
                "listing_date": nse_official_date.strftime('%Y-%m-%d'),
                "listing_year": nse_official_date.year
            })
            
        print(f"\n✅ Filter Result: {rejected_count} Migrated/Fake IPOs reject kar diye!")
        print(f"💾 Total {len(genuine_ipos)} GENUINE IPOs Database me save kar rahe hain...")
        
        if genuine_ipos:
            chunk_size = 500
            for i in range(0, len(genuine_ipos), chunk_size):
                batch = genuine_ipos[i : i+chunk_size]
                supabase.table('ipo_master').upsert(batch).execute()
            print("🎉 BULK UPDATE SUCCESSFUL! Aapka Supabase 2020 se aaj tak ready hai.")
        else:
            print("⚠️ Koi naya data nahi mila.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_ipo_master_bulk()
