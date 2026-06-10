import streamlit as st
import yfinance as yf
import pandas as pd

# Website Design
st.set_page_config(page_title="Pro Momentum Scanner", layout="wide")
st.title("🚀 Advanced Swing & Momentum Scanner")
st.write("Fast Engine: Volume Turnover logic applied for high liquidity stocks.")

# Watchlist (Aap aage isme aur stocks add kar sakte ho)
stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "TATASTEEL.NS", "ITC.NS", "ZOMATO.NS", "SUZLON.NS"]

if st.button("Run Advanced Scanner"):
    st.info("⏳ Fast scan chal raha hai... (Please wait)")
    
    results = []
    for ticker in stocks:
        try:
            # 2 saal ka data download karna (Sirf price data, no fundamentals)
            data = yf.download(ticker, period="2y", interval="1d", progress=False)
            
            # Check agar enough data hai
            if len(data) > 252:
                # Indicators Calculate karna
                data['SMA_200'] = data['Close'].rolling(window=200).mean()
                data['SMA_50'] = data['Close'].rolling(window=50).mean()
                data['Vol_SMA_20'] = data['Volume'].rolling(window=20).mean()
                
                # Turnover (Daily close * SMA 20 Volume)
                data['Turnover'] = data['Close'] * data['Vol_SMA_20']
                
                # Past Prices (22 aur 66 din pehle ka)
                data['Close_22_ago'] = data['Close'].shift(22)
                data['Close_66_ago'] = data['Close'].shift(66)
                
                # 52 Week High (Pichle 252 din ka max high, 1 din chhod kar)
                data['Max_High_252'] = data['High'].shift(1).rolling(window=252).max()
                
                # Aaj ki (Latest) values nikalna
                latest = data.iloc[-1]
                
                # Safely extract single values
                close = float(latest['Close'].iloc[0] if isinstance(latest['Close'], pd.Series) else latest['Close'])
                close_22 = float(latest['Close_22_ago'].iloc[0] if isinstance(latest['Close_22_ago'], pd.Series) else latest['Close_22_ago'])
                close_66 = float(latest['Close_66_ago'].iloc[0] if isinstance(latest['Close_66_ago'], pd.Series) else latest['Close_66_ago'])
                sma_200 = float(latest['SMA_200'].iloc[0] if isinstance(latest['SMA_200'], pd.Series) else latest['SMA_200'])
                sma_50 = float(latest['SMA_50'].iloc[0] if isinstance(latest['SMA_50'], pd.Series) else latest['SMA_50'])
                turnover = float(latest['Turnover'].iloc[0] if isinstance(latest['Turnover'], pd.Series) else latest['Turnover'])
                max_high_252 = float(latest['Max_High_252'].iloc[0] if isinstance(latest['Max_High_252'], pd.Series) else latest['Max_High_252'])
                
                # --- FAST CONDITION LOGIC (Market Cap Hataya, Turnover Rakha) ---
                
                # Setup 1: 1 Month Momentum (20% up) + Turnover Filter
                cond1 = (close / close_22 > 1.2) and (turnover > 100000000) and (close > sma_200)
                
                # Setup 2: 3 Month Momentum (30% up) + Turnover Filter
                cond2 = (close / close_66 >= 1.3) and (close >= 1) and (turnover > 100000000) and (close > sma_200)
                
                # Setup 3: 52-Week High Proximity + Turnover Filter
                cond3 = (close > max_high_252 * 0.75) and (close > sma_50) and (close > sma_200) and (turnover > 100000000)
                
                # Agar teeno mein se ek bhi condition match hoti hai
                if cond1 or cond2 or cond3:
                    match_type = []
                    if cond1: match_type.append("1M Momentum")
                    if cond2: match_type.append("3M Momentum")
                    if cond3: match_type.append("52W High Pullback")
                    
                    results.append({
                        "Stock": ticker.replace(".NS", ""),
                        "Close (₹)": round(close, 2),
                        "Turnover (Cr)": round(turnover / 10000000, 2),
                        "Condition": " + ".join(match_type)
                    })
        except Exception as e:
            pass # Data error ko skip karo
            
    # Results Show Karna
    if results:
        df = pd.DataFrame(results)
        st.success("✅ Scan Complete! Ye stocks condition match kar rahe hain:")
        st.dataframe(df)
    else:
        st.warning("⚠️ Market check kiya, par aaj kisi bhi stock ne ye conditions match nahi ki.")
