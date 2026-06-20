import streamlit as st
from supabase import create_client, Client
import requests

st.set_page_config(page_title="Momentum Swing Scanner", layout="wide")
st.title("📈 Daily Momentum Swing Scanner")

# --- SIDEBAR: REMOTE CONTROL BUTTON ---
st.sidebar.subheader("⚡ Live Market Scan")
st.sidebar.write("Market hours mein naye stocks scan karein.")

if st.sidebar.button("🚀 Run Live Scan Now"):
    try:
        # Streamlit secrets se GitHub chabiyan nikalna
        token = st.secrets["GITHUB_TOKEN"]
        repo = st.secrets["GITHUB_REPO"]
        
        # DHYAN DEIN: Agar aapki action file ka naam kuch aur hai, toh yahan change karein
        workflow_file = "daily_scan.yml" 
        
        url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_file}/dispatches"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {"ref": "main"}
        
        # GitHub ko signal bhejna
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 204:
            st.sidebar.success("✅ Scan shuru ho gaya hai! Kripya 10-12 minute baad page refresh karein.")
        else:
            st.sidebar.error(f"❌ Error aaya: {response.text}")
    except Exception as e:
        st.sidebar.error(f"❌ Button Error: Kripya Streamlit Secrets check karein. ({e})")

st.sidebar.markdown("---")

# --- MAIN PAGE: SUPABASE DATA FETCH ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

try:
    response = supabase.table('swing_stocks').select("*").order('scan_date', desc=True).execute()
    data = response.data
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

if not data:
    st.info("Database mein abhi koi data nahi hai. Ek baar GitHub par Actions run hone dijiye.")
else:
    import pandas as pd
    df = pd.DataFrame(data)
    df = df[['scan_date', 'stock_symbol', 'close_price', 'turnover_cr', 'condition_matched']]
    df.columns = ['Scan Date', 'Stock Symbol', 'Close Price', 'Turnover (Cr)', 'Condition Matched']
    st.dataframe(df, use_container_width=True)
