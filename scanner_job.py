import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import requests
import pandas as pd
import time

# 1. Page Configuration
st.set_page_config(page_title="AlphaSwing Pro | Momentum Scanner", layout="wide", page_icon="📈")

# Custom Styling for Button
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    .stButton>button { background-color: #1E88E5; color: white; border-radius: 6px; font-weight: bold; padding: 10px; }
    .stButton>button:hover { background-color: #1565C0; color: white; }
    </style>
""", unsafe_allow_html=True)

# 2. Sidebar (Sirf Info ke liye, Button yahan se hata diya hai)
st.sidebar.image("https://img.icons8.com/fluent/96/000000/chart-line.png", width=80)
st.sidebar.title("AlphaSwing Pro")
st.sidebar.markdown("*Advanced Momentum Scanner*")
st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Swing trading mein hamesha 2% ka Stoploss zaroor lagayein.")

# 3. Main Dashboard Animation (Chartink Style)
components.html(
    """
    <script src="https://cdn.jsdelivr.net/npm/typed.js@2.0.12"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@700&display=swap');
        body { font-family: 'Inter', sans-serif; text-align: center; background-color: transparent; margin: 0; padding-top: 10px; color: #E2E8F0; }
        .main-text { font-size: 40px; font-weight: 700; letter-spacing: -0.5px; }
        .highlight { color: #1E88E5; }
    </style>
    <div class="main-text">
        AlphaSwing Pro: Best tool for <br><span id="typed" class="highlight"></span>
    </div>
    <script>
        var typed = new Typed('#typed', {
            strings: ['Swing Trading.', 'Momentum Scans.', 'Technical Analysis.', 'Finding Breakouts.'],
            typeSpeed: 60, backSpeed: 40, backDelay: 1500, loop: true, showCursor: true, cursorChar: '|'
        });
    </script>
    """,
    height=120,
)
st.markdown("<p style='text-align: center; color: gray; font-size: 18px;'>Automated EOD Scanner jo pure market se high-momentum stocks filter karta hai.</p>", unsafe_allow_html=True)
st.markdown("---")

# 4. Supabase Connection
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
    response = supabase.table('swing_stocks').select("*").order('scan_date', desc=True).execute()
    raw_data = response.data
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

# 5. Tabs Setup
tab1, tab2, tab3 = st.tabs(["📊 Combined Scanner", "⚙️ Strategy Rules", "💡 Trading Guide"])

# --- TAB 1: MAIN SCANNER & BUTTON ---
with tab1:
    # A. Data Display
    if raw_data:
        df = pd.DataFrame(raw_data)
        df = df[['scan_date', 'stock_symbol', 'close_price', 'turnover_cr', 'condition_matched']]
        df.columns = ['Scan Date', 'Stock Symbol', 'Close Price', 'Turnover (Cr)', 'Strategy Matched']
        
        latest_date = df['Scan Date'].max()
        total_stocks = len(df[df['Scan Date'] == latest_date])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📅 Last Scan Date", str(latest_date))
        col2.metric("🎯 Latest Breakout Count", f"{total_stocks} Stocks")
        col3.metric("🏢 Market Covered", "NSE 2300+ Stocks")
        
        st.markdown("---")
        
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            selected_date = st.selectbox("📅 Select Scan Date", sorted(df['Scan Date'].unique(), reverse=True))
        df_filtered = df[df['Scan Date'] == selected_date]
        with f_col2:
            selected_strategy = st.selectbox("🎯 Filter by Strategy", ["All Strategies"] + list(df['Strategy Matched'].unique()))
        with f_col3:
            search_symbol = st.text_input("🔤 Search Stock", "").upper()

        if selected_strategy != "All Strategies":
            df_filtered = df_filtered[df_filtered['Strategy Matched'] == selected_strategy]
        if search_symbol:
            df_filtered = df_filtered[df_filtered['Stock Symbol'].str.contains(search_symbol)]

        st.dataframe(df_filtered, use_container_width=True, height=400)
    else:
        st.info("Database mein abhi koi data nahi hai. Niche diye gaye button se live scan shuru karein.")

    st.markdown("---")
    
    # B. The Scan Button & Animation Section (Table ke theek niche)
    st.subheader("⚡ Run Live Combined Scan")
    st.write("Market hours mein poore NSE market (2300+ stocks) ko check karne ke liye click karein.")
    
    if st.button("🚀 Run Live Scan Now", use_container_width=True):
        with st.status("GitHub Servers ko jagaya jaa raha hai...", expanded=True) as status:
            st.write("📡 Signal bheja jaa raha hai...")
            try:
                token = st.secrets["GITHUB_TOKEN"]
                repo = st.secrets["GITHUB_REPO"]
                workflow_file = "daily_scan.yml" 
                
                url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_file}/dispatches"
                headers = {
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                data = {"ref": "main"}
                
                response = requests.post(url, headers=headers, json=data)
                time.sleep(2)
                
                if response.status_code == 204:
                    status.update(label="✅ Scan Command Sent Successfully!", state="complete", expanded=False)
                    
                    # Beautiful Radar/Loading Animation
                    st.markdown(
                        """
                        <div style="text-align: center; background-color: #1E1E1E; padding: 25px; border-radius: 12px; margin-top: 15px; border: 1px solid #333;">
                            <img src="https://i.gifer.com/ZKZg.gif" width="70px" style="margin-bottom: 15px;">
                            <h3 style="color: #4CAF50; margin: 0;">🚀 Scanning 2300+ Stocks...</h3>
                            <p style="color: #AAA; font-size: 15px; margin-top: 10px;">
                                GitHub background mein kaam kar raha hai. Is process mein <b>30 se 40 minute</b> lagenge.<br>
                                <i>Aap is window ko band kar sakte hain, data automatically update ho jayega!</i>
                            </p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                else:
                    status.update(label=f"❌ GitHub Error: {response.text}", state="error")
            except Exception as e:
                status.update(label=f"❌ Setup Error: {e}", state="error")

# --- TAB 2 & 3: Strategy Rules and Guide ---
with tab2:
    st.header("⚙️ Scanner Rules")
    st.write("1-Month, 3-Month aur 52-Week High pullback ke saare technical rules yahan apply hote hain.")
with tab3:
    st.header("💡 Trading Guide")
    st.write("Hamesha 2-3% ka Stoploss use karein aur 1:2 Risk Reward ratio follow karein.")
