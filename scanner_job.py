import os
import yfinance as yf
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import logging
import warnings
import time
import requests

# Faltu warnings ko mute karna
warnings.filterwarnings('ignore')
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# 1. Supabase Connection
url_sb = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url_sb, key)

today_date = datetime.now().strftime("%Y-%m-%d")

# --- 🚀 TELEGRAM SYSTEM SETUP ---
def send_to_telegram(file_path):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("⚠️ Telegram credentials (Secrets) nahi mile. File send nahi hui.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    
    print("📤 Telegram par file bhej rahe hain...")
    try:
        with open(file_path, "rb") as file:
            payload = {"chat_id": chat_id, "caption": f"📊 Bhai, {today_date} ki Scanner List ready hai! Check karo."}
            response = requests.post(url, data=payload, files={"document": file})
            
        if response.status_code == 200:
            print("✅ File successfully aapke Telegram par bhej di gayi hai!")
        else:
            print(f"❌ Telegram Error: {response.text}")
    except Exception as e:
        print(f"❌ File bhejne me error aayi: {e}")

# --- 🚀 Supabase Error Logging System ---
error_logs_data = []

def log_error(symbol, category, detailed_reason):
    error_logs_data.append({
        "scan_date": today_date,
        "symbol": symbol,
        "error_type": category,
        "reason": detailed_reason
    })
    print(f"🚨 ERROR: {symbol} - {category}")

# 🚫 HARDCODED BLACKLIST (Added MSCI360 here)
KACHRA_STOCKS = [
    "SNXT50BE", "ITADD", "MOLOWV", "ARTEMISM", "SILVERADD", "NEXT50", "PVTBANKA", 
    "MOMENTUM", "GOLDADD", "SILVERAG", "NIFTYADD", "MONQ50", "MIDQ50ADD", "SILVERBET", 
    "MAKEINDIA", "PSUBANK", "SILVER", "MIDCAP", "MOMOMEI", "LOWVOL1", "LICNFNHG", 
    "MOQUALIT", "QGOLDHA", "QNIFTY", "SENSEXAD", "LOWVOL", "AXSENSEX", "GOLD1", 
    "HDFCMID", "HDFCNEXT", "GOLDBETA", "GSEC10YE", "BANKADD", "EQUAL50A", "NPBET", 
    "HDFCPVTE", "TECH", "MOHEALTI", "HDFCBSE5", "BANKNIFTY", "MASPTOP5", "HDFCSENS", 
    "HDFCLOW", "HDFCMON", "HDFCNIF1", "HEALTHY", "HDFCNIFT", "ICICIB22", "SILVER1", 
    "CONS", "ESG", "NIFTYBETA", "HDFCSML", "SENSEXBE", "BFSI", "MAHKTECI", "MOGSEC", 
    "NIFTYQLIT", "MOVALUE", "ALPHA", "ABSLNN50", "NV20", "GUJRAFFIA", "JSWDULUX",
    "MSCI360"
]

# 🚫 NSE SERIES BLACKLIST (Bonds, NCDs, Illiquid, etc.) - Updated with E1, Y3, Y4, Y5
BAD_SERIES = [
    "AK", "AL", "AM", "AN", "AU", "AV", "AW", "AX", "AY", "AZ", "BA", "BC", "BR", "BS", "BU", "BV", "BW", "BX", "BZ", "D1", "GB", "IV", 
    "E1", "E2", "E3", 
    "N0", "N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8", "N9", "NA", "NB", "NC", "ND", "NE", "NF", "NG", "NH", "NI", "NJ", "NK", "NL", "NM", "NN", "NO", "NP", "NQ", "NR", "NS", "NT", "NU", "NV", "NW", "NX", "NY", "NZ", 
    "P1", "RL", "RR", 
    "Y0", "Y1", "Y2", "Y3", "Y4", "Y5", "Y6", "Y7", "Y8", "Y9", "YA", "YB", "YC", "YD", "YG", "YH", "YI", "YJ", "YK", "YL", "YM", "YP", "YQ", "YR", "YS", "YT", "YU", "YV", "YW", "YX", "YY", "YZ", 
    "Z0", "Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7", "Z8", "Z9", "ZC", "ZF", "ZG", "ZH", "ZI", "ZJ", "ZK", "ZL", "ZM", "ZN", "ZO", "ZP", "ZQ", "ZR", "ZS", "ZT", "ZY", "ZZ", 
    "BE"
]
# Safety ke liye sabke aage hyphen laga diya taaki asli stocks delete na ho
BAD_SUFFIXES = tuple(f"-{s}" for s in BAD_SERIES)

# 2. Zerodha API se Master List nikalna
def get_full_nse_list():
    try:
        print("Zerodha API se list download kar rahe hain...")
        df = pd.read_csv("https://api.kite.trade/instruments", low_memory=False) 
        
        df_nse = df[
            (df['exchange'] == 'NSE') & 
            (df['instrument_type'] == 'EQ') & 
            (df['lot_size'] == 1)
        ]
        
        nse_symbols = df_nse['tradingsymbol'].tolist()
        
        clean_symbols = []
        for s in nse_symbols:
            s = str(s)
            
            # Puraane aur Naye Filters
            if s.endswith(BAD_SUFFIXES): continue
            if s.endswith("NAV") or s.endswith("INAV"): continue
            if '-SG' in s or '-SF' in s or '-SD' in s or '-GS' in s: continue
            if ' ' in s: continue
            if s.endswith("BEES") or "ETF" in s or "LIQUID" in s: continue
            if s in KACHRA_STOCKS: continue
            
            clean_symbols.append(s)
            
        print(f"✅ Master Filter Applied: Strictly {len(clean_symbols)} pure equity stocks mil gaye!")
        return clean_symbols
    except Exception as e:
        log_error("API_SYSTEM", "ZERODHA_API_FAIL", f"Zerodha list download nahi ho payi. Error: {e}")
        return ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ZOMATO"]

nse_stocks = get_full_nse_list()
stocks = [s + ".NS" for s in nse_stocks]

print(f"🚀 MASTERPLAN BATCH MODE: {len(stocks)} stocks process ho rahe hain...\n")

matched_stocks_data = [] 
saved_count = 0
chunk_size = 50  

# 3. Batch Calculation
for i in range(0, len(stocks), chunk_size):
    batch = stocks[i : i + chunk_size]
    print(f"📦 Downloading Batch {i//chunk_size + 1} ({len(batch)} stocks)...")
    
    time.sleep(2)  
    
    try:
        batch_data = yf.download(batch, period="2y", interval="1d", threads=True, progress=False)

        if isinstance(batch_data.columns, pd.MultiIndex):
            close_df = batch_data['Close']
            high_df = batch_data['High']
            vol_df = batch_data['Volume']  
        else:
            log_error(f"BATCH_NO_{i//chunk_size + 1}", "FORMAT_MISMATCH", "Yahoo data MultiIndex format me nahi tha. Batch skip hua.")
            continue

        for ticker in batch:
            try:
                if ticker not in close_df.columns:
                    log_error(ticker, "DATA_MISSING", "Yahoo par is symbol ka daily chart data nahi mila.")
                    continue

                close_data = close_df[ticker].dropna()
                high_data = high_df[ticker].dropna()
                vol_data = vol_df[ticker].dropna()  

                if len(close_data) < 22:
                    log_error(ticker, "INSUFFICIENT_HISTORY", f"Sirf {len(close_data)} din ka data hai. Min 22 days zaroori hain.")
                    continue
                
                # Math & Moving Averages
                sma_50 = close_data.rolling(window=50, min_periods=1).mean()
                vol_sma_20 = vol_data.rolling(window=20, min_periods=1).mean()  
                turnover_data = close_data * vol_sma_20  
                
                close_22_ago = close_data.shift(22)
                close_66_ago = close_data.shift(66)
                max_high_252 = high_data.shift(1).rolling(window=252, min_periods=1).max()
                
                close = float(close_data.iloc[-1])
                sma_50_val = float(sma_50.iloc[-1])
                max_high = float(max_high_252.iloc[-1])
                turnover = float(turnover_data.iloc[-1])  
                
                close_22 = float(close_22_ago.iloc[-1]) if pd.notna(close_22_ago.iloc[-1]) else 999999.0
                close_66 = float(close_66_ago.iloc[-1]) if pd.notna(close_66_ago.iloc[-1]) else 999999.0
                
                # 🚀 TURNOVER CONDITION ADDED (> 10 Crore)
                tech_cond1 = (close / close_22 > 1.2) and (turnover > 100000000)
                tech_cond2 = (close / close_66 >= 1.3) and (close >= 1) and (turnover > 100000000)
                tech_cond3 = (close > max_high * 0.75) and (close > sma_50_val) and (turnover > 100000000)
                
                weekly_cond_pass = False
                weekly_close = close_data.resample('W-FRI').last()
                
                if len(weekly_close) >= 4:
                    weekly_ema10 = weekly_close.ewm(span=10, adjust=False).mean()
                    weekly_ema30 = weekly_close.ewm(span=30, adjust=False).mean()
                    
                    w1 = (weekly_close.iloc[-2] > weekly_ema10.iloc[-2]) and (weekly_close.iloc[-2] > weekly_ema30.iloc[-2])
                    w2 = (weekly_close.iloc[-3] > weekly_ema10.iloc[-3]) and (weekly_close.iloc[-3] > weekly_ema30.iloc[-3])
                    w3 = (weekly_close.iloc[-4] > weekly_ema10.iloc[-4]) and (weekly_close.iloc[-4] > weekly_ema30.iloc[-4])
                    
                    if w1 and w2 and w3:
                        weekly_cond_pass = True

                if (tech_cond1 or tech_cond2 or tech_cond3) and weekly_cond_pass:
                    try:
                        time.sleep(0.5) 
                        stock_info = yf.Ticker(ticker).info
                        
                        if not stock_info or 'sector' not in stock_info:
                            time.sleep(2)
                            stock_info = yf.Ticker(ticker).info
                        
                        sector_name = stock_info.get('sector', 'Unknown')
                        proxy_name = stock_info.get('industry', 'Unknown')
                        
                        if not sector_name or sector_name.strip() == "": sector_name = 'Unknown'
                        if not proxy_name or proxy_name.strip() == "": proxy_name = 'Unknown'
                        
                    except Exception as info_e:
                        sector_name = 'Unknown'
                        proxy_name = 'Unknown'
                        log_error(ticker, "INFO_FETCH_FAIL", f"Sector/Industry info fail hui. Error: {info_e}")
                    
                    symbol_clean = ticker.replace(".NS", "")
                    
                    matched_stocks_data.append({
                        "scan_date": today_date,
                        "stock_symbol": symbol_clean,
                        "close_price": round(close, 2),
                        "turnover_cr": round(turnover / 10000000, 2),  
                        "sector": sector_name,
                        "industry_proxy": proxy_name
                    })
                    print(f"🔥 Breakout: {symbol_clean} | {sector_name} | {proxy_name} | TO: {round(turnover / 10000000, 2)}Cr")
                    saved_count += 1

            except Exception as inner_e:
                log_error(ticker, "CALCULATION_ERROR", f"Code crash error: {inner_e}")
                
    except Exception as batch_e:
        log_error(f"BATCH_NO_{i//chunk_size + 1}", "YAHOO_BATCH_TIMEOUT", f"Batch connection drop error: {batch_e}")

# --- BULK INSERT: MATCHED STOCKS ---
if matched_stocks_data:
    print(f"\n💾 Saving {len(matched_stocks_data)} stocks to Database in one go...")
    try:
        supabase.table('swing_stocks').insert(matched_stocks_data).execute()
        print(f"🎉 Scan complete! {saved_count} stocks saved.")
    except Exception as e:
        print(f"❌ DATABASE ERROR: Stocks save nahi ho paye!")
        log_error("DB_SYSTEM", "SUPABASE_INSERT_FAIL", f"Breakout stocks save error: {e}")

    # --- 🚀 NEW: TELEGRAM NOTIFICATION & EXCEL EXPORT ---
    try:
        csv_filename = f"Breakout_Stocks_{today_date}.csv"
        df_export = pd.DataFrame(matched_stocks_data)
        
        # DataFrame ko CSV mein save karna
        df_export.to_csv(csv_filename, index=False)
        
        # Telegram par send karna
        send_to_telegram(csv_filename)
    except Exception as e:
        print(f"❌ Telegram CSV creation/send fail: {e}")

# --- BULK INSERT: ERROR LOGS ---
if error_logs_data:
    print(f"\n⚠️ Sending {len(error_logs_data)} error logs to Database...")
    try:
        supabase.table('error_logs').insert(error_logs_data).execute()
        print("✅ Error logs successfully saved!")
    except Exception as e:
        print(f"❌ Error logs save failure: {e}")
