import yfinance as yf
import pandas as pd
import traceback

print("🩺 X-Ray Test Started: Checking 3 Giants...\n")
test_stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]

for ticker in test_stocks:
    print(f"👉 Checking {ticker}...")
    try:
        # Faltu error na dikhe isliye progress=False rakha hai
        data = yf.download(ticker, period="2y", interval="1d", progress=False)
        
        # Check 1: Kya data aaya?
        print(f"   📊 Rows downloaded: {len(data)}")
        
        if len(data) > 200:
            # Check 2: Calculations
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['Vol_SMA_20'] = data['Volume'].rolling(window=20).mean()
            data['Turnover'] = data['Close'] * data['Vol_SMA_20']
            
            latest = data.iloc[-1]
            
            # Yahan extract karne me hi sabse zyada error aata hai (Let's expose it)
            close = float(latest['Close'].iloc[0] if isinstance(latest['Close'], pd.Series) else latest['Close'])
            sma_200 = float(latest['SMA_200'].iloc[0] if isinstance(latest['SMA_200'], pd.Series) else latest['SMA_200'])
            turnover = float(latest['Turnover'].iloc[0] if isinstance(latest['Turnover'], pd.Series) else latest['Turnover'])
            
            print(f"   💰 Close: {close:.2f} | 200 EMA: {sma_200:.2f} | Turnover: {turnover/10000000:.2f} Cr")
            
            # Easy Condition Check
            if close > 50 and close > sma_200 and turnover > 10000000:
                print(f"   ✅ RESULT: {ticker} PASS HO GAYA!\n")
            else:
                print(f"   ❌ RESULT: {ticker} FAIL (Condition match nahi hui)\n")
        else:
            print(f"   ❌ Error: Pura data download nahi hua (Rows < 200)\n")
            
    except Exception as e:
        # Agar calculation ya format mein error aayega toh yahan pakda jayega
        print(f"   🚨 CODE CRASHED FOR {ticker}: {e}")
        traceback.print_exc()
        print("\n")

print("🎯 X-Ray Test Complete!")
