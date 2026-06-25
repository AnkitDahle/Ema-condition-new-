import os
import yfinance as yf
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import logging
import warnings
import time

# Faltu warnings ko mute karna
warnings.filterwarnings('ignore')
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# 1. Supabase Connection
url_sb = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url_sb, key)

today_date = datetime.now().strftime("%Y-%m-%d")

# --- 🚀 NEW: Supabase Error Logging System ---
error_logs_data = []

def log_error(symbol, category, detailed_reason):
    """Errors ko database ke liye list me jama karne ka function"""
    error_logs_data.append({
        "scan_date": today_date,
        "symbol": symbol,
        "error_type": category,
        "reason": detailed_reason
    })
    print(f"🚨 ERROR: {symbol} - {category}")

# 🚫 HARDCODED BLACKLIST (Kachra stocks ko silently hatane ke liye, inka log nahi banega)
KACHRA_STOCKS = [
    "SNXT50BE", "ITADD", "MOLOWV", "ARTEMISM", "SILVERADD", "NEXT50", "PVTBANKA", 
    "MOMENTUM", "GOLDADD", "SILVERAG", "NIFTYADD", "MONQ50", "MIDQ50ADD", "SILVERBET", 
    "MAKEINDIA", "PSUBANK", "SILVER", "MIDCAP", "MOMOMEI", "LOWVOL1", "LICNFNHG", 
    "MOQUALIT", "QGOLDHA", "QNIFTY", "SENSEXAD", "LOWVOL", "AXSENSEX", "GOLD1", 
    "HDFCMID", "HDFCNEXT", "GOLDBETA", "GSEC10YE", "BANKADD", "EQUAL50A", "NPBET", 
    "HDFCPVTE", "TECH", "MOHEALTI", "HDFCBSE5", "BANKNIFTY", "MASPTOP5", "HDFCSENS", 
    "HDFCLOW", "HDFCMON", "HDFCNIF1", "HEALTHY", "HDFCNIFT", "ICICIB22", "SILVER1", 
    "CONS", "ESG", "NIFTYBETA", "HDFCSML", "SENSEXBE", "BFSI", "MAHKTECI", "MOGSEC", 
    "NIFTYQLIT", "MOVALUE", "ALPHA", "ABSLNN50", "NV20", "GUJRAFFIA", "JSWDULUX"
]

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
            
            # CATEGORY 3 IGNORED: Kachra stocks silently bypass ho jayenge
            if '-SG' in s or '-SF' in s or '-SD' in s or '-GS' in s: continue
            if ' ' in s: continue
            if s.endswith("BEES") or "ETF" in s or "LIQUID" in s: continue
            if s in KACHRA_STOCKS: continue
            
            clean_symbols.append(s)
            
        print(f"✅ Master Filter Applied: Strictly {len(clean_symbols)} premium stocks mil gaye!")
        return clean_symbols
    except Exception as e:
        # CATEGORY 1: API Failure
        log_error("API_SYSTEM", "ZERODHA_API_FAIL", f"Zerodha se master list download nahi ho payi. Asli error: {e}")
        return ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ZOMATO"]

nse_stocks = get_full_nse_list()
stocks = [s + ".NS" for s in nse_stocks]

print(f"🚀 MASTERPLAN BATCH MODE: {len(stocks)} stocks process ho rahe hain...\n")

matched_stocks_data = [] 
saved_count = 0
chunk_size = 500  

# 3. Batch Calculation
for i in range(0, len(stocks), chunk_size):
    batch = stocks[i : i + chunk_size]
    print(f"📦 Downloading Batch {i//chunk_size + 1} ({len(batch)} stocks)...")
    
    try:
        batch_data = yf.download(batch, period="2y", interval="1d", threads=True, progress=False)

        if isinstance(batch_data.columns, pd.MultiIndex):
            close_df = batch_data['Close']
            high_df = batch_data['High']
        else:
            # CATEGORY 1: Format Mismatch
            log_error(f"BATCH_NO_{i//chunk_size + 1}", "FORMAT_MISMATCH", "Yahoo ne data fetch kiya par MultiIndex format me nahi tha. Poora batch skip hua.")
            continue

        for ticker in batch:
            try:
                # CATEGORY 2: Data Missing
                if ticker not in close_df.columns:
                    log_error(ticker, "DATA_MISSING", "Yahoo Finance par is symbol ka koi daily chart data nahi mila (delist ya symbol change).")
                    continue

                close_data = close_df[ticker].dropna()
                high_data = high_df[ticker].dropna()

                # CATEGORY 2: Insufficient History
                if len(close_data) < 22:
                    log_error(ticker, "INSUFFICIENT_HISTORY", f"Sirf {len(close_data)} din ka data hai. Breakout check ke liye min 22 days zaroori hain (Naya IPO ho sakta hai).")
                    continue
                
                # Calculation Block
                sma_200 = close_data.rolling(window=200, min_periods=1).mean()
                sma_50 = close_data.rolling(window=50, min_periods=1).mean()
                
                close_22_ago = close_data.shift(22)
                close_66_ago = close_data.shift(66)
                max_high_252 = high_data.shift(1).rolling(window=252, min_periods=1).max()
                
                close = float(close_data.iloc[-1])
                sma_200_val = float(sma_200.iloc[-1])
                sma_50_val = float(sma_50.iloc[-1])
                max_high = float(max_high_252.iloc[-1])
                
                close_22 = float(close_22_ago.iloc[-1]) if pd.notna(close_22_ago.iloc[-1]) else 999999.0
                close_66 = float(close_66_ago.iloc[-1]) if pd.notna(close_66_ago.iloc[-1]) else 999999.0
                
                tech_cond1 = (close / close_22 > 1.2) and (close > sma_200_val)
                tech_cond2 = (close / close_66 >= 1.3) and (close >= 1) and (close > sma_200_val)
                tech_cond3 = (close > max_high * 0.75) and (close > sma_50_val) and (close > sma_200_val)
                
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
                        # CATEGORY 2: Sector Info Fail
                        log_error(ticker, "INFO_FETCH_FAIL", f"Stock select ho gaya, par Yahoo API ne uski Sector/Industry info block kar di. Error: {info_e}")
                    
                    symbol_clean = ticker.replace(".NS", "")
                    
                    matched_stocks_data.append({
                        "scan_date": today_date,
                        "stock_symbol": symbol_clean,
                        "close_price": round(close, 2),
                        "turnover_cr": 0.0,
                        "sector": sector_name,
                        "industry_proxy": proxy_name
                    })
                    print(f"🔥 Breakout: {symbol_clean} | {sector_name} | {proxy_name}")
                    saved_count += 1

            except Exception as inner_e:
                # CATEGORY 4: Calculation Error
                log_error(ticker, "CALCULATION_ERROR", f"Stock ka data fetch hua par math calculate karte waqt code crash ho gaya. Error: {inner_e}")
                
    except Exception as batch_e:
        # CATEGORY 1: Batch Timeout
        log_error(f"BATCH_NO_{i//chunk_size + 1}", "YAHOO_BATCH_TIMEOUT", f"Ek sath data fetch karte time Yahoo server connection drop ho gaya. Error: {batch_e}")

# --- BULK INSERT: MATCHED STOCKS ---
if matched_stocks_data:
    print(f"\n💾 Saving {len(matched_stocks_data)} stocks to Database in one go...")
    try:
        supabase.table('swing_stocks').insert(matched_stocks_data).execute()
        print(f"🎉 Scan complete! {saved_count} stocks saved.")
    except Exception as e:
        print(f"❌ DATABASE ERROR: Stocks save nahi ho paye!")
        # CATEGORY 5: Database Issue (Stocks)
        log_error("DB_SYSTEM", "SUPABASE_INSERT_FAIL", f"Breakout stocks mile par Supabase ki 'swing_stocks' table me save nahi huye. Error: {e}")

# --- BULK INSERT: ERROR LOGS ---
if error_logs_data:
    print(f"\n⚠️ Sending {len(error_logs_data)} error logs to Database...")
    try:
        supabase.table('error_logs').insert(error_logs_data).execute()
        print("✅ Error logs successfully saved!")
    except Exception as e:
        print(f"❌ Error logs ko Supabase me save karte time failure: {e}")
