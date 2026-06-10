import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Swing Scanner", layout="wide")
st.title("📈 Free Swing Trading Scanner")
st.write("Ye scanner check karta hai ki kya stock ka price 50 EMA ke upar hai.")

stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "TATASTEEL.NS", "ITC.NS"]

if st.button("Run Swing Scanner"):
    st.info("⏳ Market data fetch ho raha hai... (Please wait)")
    
    results = []
    for ticker in stocks:
        try:
            data = yf.download(ticker, period="100d", interval="1d", progress=False)
            if not data.empty:
                data['EMA_50'] = data['Close'].ewm(span=50, adjust=False).mean()
                
                latest_close = float(data['Close'].iloc[-1].iloc[0] if isinstance(data['Close'].iloc[-1], pd.Series) else data['Close'].iloc[-1])
                latest_ema = float(data['EMA_50'].iloc[-1].iloc[0] if isinstance(data['EMA_50'].iloc[-1], pd.Series) else data['EMA_50'].iloc[-1])
                
                if latest_close > latest_ema:
                    results.append({
                        "Stock": ticker.replace(".NS", ""),
                        "Close Price (₹)": round(latest_close, 2),
                        "50 EMA (₹)": round(latest_ema, 2),
                        "Signal": "🟢 Bullish"
                    })
        except Exception as e:
            pass 
            
    if results:
        df = pd.DataFrame(results)
        st.success("✅ Scan Complete! Ye rahe aapke stocks:")
        st.dataframe(df)
    else:
        st.warning("⚠️ Aaj koi bhi stock is condition ko match nahi kar raha hai.")
