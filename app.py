import streamlit as st
from supabase import create_client, Client
import pandas as pd

# Website Design
st.set_page_config(page_title="Pro Momentum Scanner", layout="wide")
st.title("🚀 Advanced Swing & Momentum Scanner")
st.write("⚡ Data fetched instantly from Cloud Database (Top 2000+ NSE Stocks)")

# Database se connect karne ka function
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
    
    st.info("Fetching latest scan results...")
    # Database se data mangwana (Latest date sabse upar)
    response = supabase.table("swing_stocks").select("*").order("scan_date", desc=True).limit(200).execute()
    
    data = response.data
    
    if data:
        df = pd.DataFrame(data)
        
        # Columns ko sundar banana
        df = df[['scan_date', 'stock_symbol', 'close_price', 'turnover_cr', 'condition_matched']]
        df.columns = ['Date', 'Stock', 'Close (₹)', 'Turnover (Cr)', 'Condition Matched']
        
        # Date filter lagana (Sirf latest din ka data dikhane ke liye)
        latest_date = df['Date'].iloc[0]
        st.success(f"✅ Latest Scan Results for: **{latest_date}**")
        
        # Sirf aaj ka/latest din ka data filter karna
        latest_df = df[df['Date'] == latest_date]
        
        st.dataframe(latest_df, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Database mein abhi koi data nahi hai. Ek baar GitHub par Actions run hone dijiye.")
        
except Exception as e:
    st.error("Connection Error. Kripya Streamlit Secrets check karein.")

# --- REMOTE CONTROL BUTTON ---
import requests

st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Live Market Scan")
st.sidebar.write("Market hours mein naye stocks scan karein.")

if st.sidebar.button("🚀 Run Live Scan Now"):
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    workflow_file = "daily_scan.yml"  # Aapki github actions file ka exact naam
    
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_file}/dispatches"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"ref": "main"}
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 204:
        st.sidebar.success("✅ Scan shuru ho gaya hai! Kripya 10-12 minute baad page refresh karein.")
    else:
        st.sidebar.error(f"❌ Error aaya: {response.text}")
