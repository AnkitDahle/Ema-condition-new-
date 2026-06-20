import os
import yfinance as yf
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import requests

# 1. Supabase Connection Set Karna
url_sb = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url_sb, key)

today_date = datetime.now().strftime("%Y-%m-%d")

# 2. Broker (Angel One) se Live Master List nikalna
def get_full_nse_list():
    try:
        print("Broker se master list download kar rahe hain...")
        url = "https://margincalculator.angelbroking.com/OpenAPI_Config/999/0.3/v1/Config/master_selection.json"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        df = pd.DataFrame(data)
        df_nse = df[(df['exch_seg'] == 'NSE') & (df['symbol'].str.endswith('-EQ'))]
        
        nse_symbols = [s.replace('-EQ', '') for s in df_nse['symbol'].tolist()]
        print(f"✅ Success: Market se {len(nse_symbols)} stocks mil gaye!")
        return nse_symbols
    except Exception as e:
        print(f"❌ Master list fail hui: {e}. Backup use kar rahe hain.")
        return ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ZOMATO"]

nse_stocks = get_full_nse_list()
stocks = [s + ".NS" for s in nse_stocks]

print(f"Scanning started for {len(stocks)} stocks...")
saved_count = 0

# 3. Har stock ko check karna
for ticker in stocks:
    try:
        data = yf.download(ticker, period="2y", interval="1d", progress=False)
        
        if len(data) > 252:
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            data['Vol_SMA_20'] = data['Volume'].rolling(window=20).mean()
            data['Turnover'] = data['Close'] * data['Vol_SMA_20']
            
            data['Close_22_ago'] = data['Close'].shift(22)
            data['Close_66_ago'] = data['Close'].shift(66)
            data['Max_High_252'] = data['High'].shift(1).rolling(window=252).max()
            
            latest = data.iloc[-1]
            
            close = float(latest['Close'].iloc[0] if isinstance(latest['Close'], pd.Series) else latest['Close'])
            close_22 = float(latest['Close_22_ago'].iloc[0] if isinstance(latest['Close_22_ago'], pd.Series) else latest['Close_22_ago'])
            close_66 = float(latest['Close_66_ago'].iloc[0] if isinstance(latest['Close_66_ago'], pd.Series) else latest['Close_66_ago'])
            sma_200 = float(latest['SMA_200'].iloc[0] if isinstance(latest['SMA_200'], pd.Series) else latest['SMA_200'])
            sma_50 = float(latest['SMA_50'].iloc[0] if isinstance(latest['SMA_50'], pd.Series) else latest['SMA_50'])
            turnover = float(latest['Turnover'].iloc[0] if isinstance(latest['Turnover'], pd.Series) else latest['Turnover'])
            max_high_252 = float(latest['Max_High_252'].iloc[0] if isinstance(latest['Max_High_252'], pd.Series) else latest['Max_High_252'])
            
            tech_cond1 = (close / close_22 > 1.2) and (turnover > 100000000) and (close > sma_200)
            tech_cond2 = (close / close_66 >= 1.3) and (close >= 1) and (turnover > 100000000) and (close > sma_200)
            tech_cond3 = (close > max_high_252 * 0.75) and (close > sma_50) and (close > sma_200) and (turnover > 100000000)
            
            if tech_cond1 or tech_cond2 or tech_cond3:
                try:
                    raw_mcap = yf.Ticker(ticker).info.get('marketCap', 15000000000)
                    mcap_cr = (raw_mcap / 10000000)
                except:
                    mcap_cr = 1500 
                
                cond1 = tech_cond1 and (mcap_cr > 1)
                cond2 = tech_cond2 and (mcap_cr > 0)
                cond3 = tech_cond3 and (mcap_cr >= 1000)
                
                if cond1 or cond2 or cond3:
                    match_type = []
                    if cond1: match_type.append("1M Momentum")
                    if cond2: match_type.append("3M Momentum")
                    if cond3: match_type.append("52W High Pullback")
                    
                    condition_str = " + ".join(match_type)
                    symbol_clean = ticker.replace(".NS", "")
                    
                    supabase.table('swing_stocks').insert({
                        "scan_date": today_date,
                        "stock_symbol": symbol_clean,
                        "close_price": round(close, 2),
                        "turnover_cr": round(turnover / 10000000, 2),
                        "condition_matched": condition_str
                    }).execute()
                    
                    print(f"🔥 Found Breakout: {symbol_clean} - {condition_str}")
                    saved_count += 1
    except:
        pass

print(f"🎉 Scan complete! Total {saved_count} stocks saved.")
