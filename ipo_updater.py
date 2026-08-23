import os
import pandas as pd
from supabase import create_client, Client
import requests
import io
from datetime import datetime, timedelta
import yfinance as yf
import warnings

warnings.filterwarnings('ignore')

# ==========================================
# 1. Supabase Connection
# ==========================================
url_sb = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url_sb or not key:
    print("⚠️ Supabase Credentials missing!")
    exit()

supabase: Client = create_client(url_sb, key)

def daily_ipo_tracker():
    print("🌐 Checking NSE for recently listed stocks (Last 7 Days)...")
    url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text))
        df.columns = df.columns.str.strip()
        df = df[df['SERIES'] == 'EQ']
        
        # 🌟 LOGIC: Aaj se pichle 7 din ka window
        today = datetime.now().date()
        seven_days_ago = today - timedelta(days=7)
        
        recent_listings = []
        for index, row in df.iterrows():
            try:
                list_date_str = str(row['DATE OF LISTING']).strip()
                date_obj = datetime.strptime(list_date_str, '%d-%b-%Y').date()
                
                # Agar listing date pichle 7 din me hai, toh isko check list me dalo
                if seven_days_ago <= date_obj <= today:
                    recent_listings.append({
                        "stock_symbol": str(row['SYMBOL']).strip(),
                        "company_name": str(row['NAME OF COMPANY']).strip(),
                        "nse_date": date_obj
                    })
            except:
                continue
                
        if not recent_listings:
            print("💤 Pichle 7 din me NSE par koi naya stock list nahi hua. All good!")
            return
            
        print(f"🔍 NSE ne {len(recent_listings)} naye stocks bataye. Ab YFinance se migration check kar rahe hain...\n")
        
        genuine_ipos = []
        
        for item in recent_listings:
            sym = item['stock_symbol']
            nse_official_date = item['nse_date']
            
            print(f"⚡ Verifying: {sym}...")
            
            # Ek-ek karke BSE (.BO) aur NSE (.NS) ka historical data check karo
            ns_data = yf.download(f"{sym}.NS", period="max", progress=False)
            bo_data = yf.download(f"{sym}.BO", period="max", progress=False)
            
            yf_dates = []
            if not ns_data.empty and ns_data.first_valid_index() is not None:
                yf_dates.append(ns_data.first_valid_index().date())
            if not bo_data.empty and bo_data.first_valid_index() is not None:
                yf_dates.append(bo_data.first_valid_index().date())
                
            is_migrated = False
            if yf_dates:
                oldest_date = min(yf_dates)
                
                # Agar 30 din se purani history nikli, matlab ye BSE ya SME se migrate hua hai
                if (nse_official_date - oldest_date).days > 30:
                    is_migrated = True
                    print(f"   🚫 REJECTED: {sym} (Migrated Stock! Original start: {oldest_date})")
            
            if not is_migrated:
                print(f"   ✅ ACCEPTED: {sym} is a 100% Genuine New IPO!")
                genuine_ipos.append({
                    "stock_symbol": sym,
                    "company_name": item['company_name'],
                    "listing_date": nse_official_date.strftime('%Y-%m-%d'),
                    "listing_year": nse_official_date.year
                })
                
        # ==========================================
        # 3. Database Save
        # ==========================================
        if genuine_ipos:
            print(f"\n💾 Saving {len(genuine_ipos)} GENUINE IPO(s) to Supabase Database...")
            supabase.table('ipo_master').upsert(genuine_ipos).execute()
            print("🎉 Daily Tracker Run Successful! System Updated.")
        else:
            print("\n⚠️ Jo bhi stocks recent the, wo sab kachra (migrated) nikle. Database remains unchanged.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    daily_ipo_tracker()
