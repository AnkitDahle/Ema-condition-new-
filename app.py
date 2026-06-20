import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Momentum Swing Scanner", layout="wide")
st.title("📈 Daily Momentum Swing Scanner")

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

try:
    response = supabase.table('swing_stocks').select("*").order('scan_date', descending=True).execute()
    data = response.data
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

if not data:
    st.info("Database mein abhi koi data nahi hai.")
else:
    import pandas as pd
    df = pd.DataFrame(data)
    df = df[['scan_date', 'stock_symbol', 'close_price', 'turnover_cr', 'condition_matched']]
    df.columns = ['Scan Date', 'Stock Symbol', 'Close Price', 'Turnover (Cr)', 'Condition Matched']
    st.dataframe(df, use_container_width=True)
