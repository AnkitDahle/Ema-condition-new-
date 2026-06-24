import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import requests
import pandas as pd
import time

# 1. Page Configuration
st.set_page_config(page_title="AlphaSwing Pro | Momentum Scanner", layout="wide", page_icon="📈")

# Custom Styling for Buttons
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    .btn-green button { background-color: #4CAF50; color: white; border-radius: 6px; font-weight: bold; padding: 10px; width: 100%; border: none;}
    .btn-green button:hover { background-color: #45a049; }
    .btn-red button { background-color: #D32F2F; color: white; border-radius: 6px; font-weight: bold; padding: 10px; width: 100%; border: none;}
    .btn-red button:hover { background-color: #b71c1c; }
    </style>
""", unsafe_allow_html=True)

# 2. Sidebar
st.sidebar.image("https://img.icons8.com/fluent/96/000000/chart-line.png", width=80)
st.sidebar.title("AlphaSwing Pro")
st.sidebar.markdown("*Advanced Momentum Scanner*")
st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Swing trading mein hamesha 2% ka Stoploss zaroor lagayein.")

# 3. Main Dashboard Animation
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
            strings: ['Swing Trading.', 'Live Market Scans.', 'Technical Analysis.', 'Finding Breakouts.'],
            typeSpeed: 60, backSpeed: 40, backDelay: 1500, loop: true, showCursor: true, cursorChar: '|'
        });
    </script>
    """,
    height=120,
)
st.markdown("<p style='text-align: center; color: gray; font-size: 18px;'>Automated EOD & Live Scanner for High-Momentum Stocks.</p>", unsafe_allow_html=True)
st.markdown("---")

# 4. Supabase Connection
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# Fetch Fresh Data
try:
    response = supabase.table('swing_stocks').select("*").order('scan_date', desc=True).execute()
    raw_data = response.data
except Exception as e:
    st.error(f"Database Error: {e}")
    raw_data = None

# 5. Tabs Setup
tab1, tab2, tab3, tab4 = st.tabs(["📊 Combined Scanner", "⚙️ Strategy Rules", "💡 Trading Guide", "🏢 IPO Tracker"])

# --- TAB 1: MAIN SCANNER ---
with tab1:
    
    # 🔄 LIVE TRACKING TOGGLE
    live_tracking = st.toggle("🔄 Enable Live Tracking (Auto-refresh every 15s)")
    if live_tracking:
        st.info("📡 Live Tracking ON: Parde ke peeche naye stocks scan hote hi yahan apne aap aa jayenge...")
        time.sleep(15)
        st.rerun()
        
    if raw_data:
        df = pd.DataFrame(raw_data)
        
        # Columns filter karna
        cols_to_keep = ['scan_date', 'stock_symbol', 'close_price', 'turnover_cr', 'sector', 'industry_proxy']
        existing_cols = [c for c in cols_to_keep if c in df.columns]
        df = df[existing_cols]
        
        # Rename columns for clean display
        rename_dict = {
            'scan_date': 'Scan Date',
            'stock_symbol': 'Stock Symbol',
            'close_price': 'Close Price (₹)',
            'turnover_cr': 'Turnover (Cr)',
            'sector': 'Sector',
            'industry_proxy': 'Proxy / Industry'
        }
        df.rename(columns=rename_dict, inplace=True)
        
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
            if 'Sector' in df.columns:
                sector_list = ["All Sectors"] + list(df['Sector'].dropna().unique())
                selected_sector = st.selectbox("🎯 Filter by Sector", sector_list)
            else:
                selected_sector = "All Sectors"
                
        with f_col3:
            search_symbol = st.text_input("🔤 Search Stock", "").upper()

        if selected_sector != "All Sectors":
            df_filtered = df_filtered[df_filtered['Sector'] == selected_sector]
        if search_symbol:
            df_filtered = df_filtered[df_filtered['Stock Symbol'].str.contains(search_symbol)]

        # Scrollable & Compact Table Logic
        st.dataframe(df_filtered, use_container_width=True, height=400, hide_index=True)
        
        # --- 🚀 NEW: TRADINGVIEW WATCHLIST EXPORT (WITH SECTIONS) ---
        if not df_filtered.empty:
            tv_text = ""
            # Data ko Sector aur Proxy ke hisaab se sort karna
            sorted_df = df_filtered.sort_values(by=['Sector', 'Proxy / Industry'])
            
            # Group banana
            grouped = sorted_df.groupby(['Sector', 'Proxy / Industry'])
            
            for (sector, proxy), group in grouped:
                # TradingView me Section banane ka rule: '### Section Name'
                tv_text += f"### {sector} / {proxy}\n"
                
                for symbol in group['Stock Symbol']:
                    # TradingView me Indian stocks ke aage NSE: lagana zaroori hai
                    tv_text += f"NSE:{symbol}\n"
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_d1, col_d2, col_d3 = st.columns([1, 2, 1])
            with col_d2:
                st.download_button(
                    label="📥 Download TradingView Watchlist (.txt)",
                    data=tv_text,
                    file_name=f"AlphaSwing_{selected_date}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    help="TradingView me 'Import List' par click karke is file ko upload karein."
                )
    else:
        st.info("Database mein abhi koi data nahi hai. Niche diye gaye button se live scan shuru karein.")

    st.markdown("---")
    
    # ⚡ ACTION BUTTONS (Start & Stop)
    st.subheader("⚡ Live Scanner Controls")
    
    colA, colB = st.columns(2)
    
    # START BUTTON
    with colA:
        st.markdown("<div class='btn-green'>", unsafe_allow_html=True)
        if st.button("🚀 Run Live Scan Now", use_container_width=True):
            with st.spinner("Signal bheja jaa raha hai..."):
                try:
                    token = st.secrets["GITHUB_TOKEN"]
                    repo = st.secrets["GITHUB_REPO"]
                    url = f"https://api.github.com/repos/{repo}/actions/workflows/daily_scan.yml/dispatches"
                    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
                    
                    response = requests.post(url, headers=headers, json={"ref": "main"})
                    time.sleep(2)
                    
                    if response.status_code == 204:
                        st.success("✅ Scan Shuru Ho Gaya! Upar 'Live Tracking' toggle ko ON kar lein.")
                    else:
                        st.error("❌ GitHub Error: Token/Repo check karein.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    # STOP BUTTON
    with colB:
        st.markdown("<div class='btn-red'>", unsafe_allow_html=True)
        if st.button("🛑 Stop Active Scan", use_container_width=True):
            with st.spinner("Active scan ko roka jaa raha hai..."):
                try:
                    token = st.secrets["GITHUB_TOKEN"]
                    repo = st.secrets["GITHUB_REPO"]
                    
                    url_get = f"https://api.github.com/repos/{repo}/actions/runs?status=in_progress"
                    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
                    res = requests.get(url_get, headers=headers)
                    runs = res.json().get("workflow_runs", [])
                    
                    if runs:
                        for run in runs:
                            run_id = run["id"]
                            url_cancel = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/cancel"
                            requests.post(url_cancel, headers=headers)
                        st.success("🛑 Active scan successfully rok diya gaya hai!")
                    else:
                        st.info("Parde ke peeche abhi koi active scan nahi chal raha hai.")
                except Exception as e:
                    st.error(f"Error stopping scan: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2 & 3: Strategy Rules and Guide ---
with tab2:
    st.header("⚙️ Scanner Rules")
    st.write("1-Month, 3-Month aur 52-Week High pullback ke saare technical rules yahan apply hote hain.")
    st.write("Weekly 10 aur 30 EMA ka strong filter lagaya gaya hai.")
with tab3:
    st.header("💡 Trading Guide")
    st.write("Hamesha 2-3% ka Stoploss use karein aur 1:2 Risk Reward ratio follow karein.")

# --- TAB 4: IPO TRACKER ---
with tab4:
    st.header("🏢 IPO & New Listings Tracker (2020 - Present)")
    st.markdown("Yeh section NSE official data se recent listed stocks ko listing date ke hisab se dikhata hai.")
    
    try:
        # Supabase se IPO data lana
        ipo_res = supabase.table('ipo_master').select("*").execute()
        
        if ipo_res.data:
            df_ipo = pd.DataFrame(ipo_res.data)
            
            # Year select karne ka Dropdown
            years = sorted(df_ipo['listing_year'].unique(), reverse=True)
            selected_year = st.selectbox("📅 Select IPO Listing Year:", years)
            
            filtered_ipo = df_ipo[df_ipo['listing_year'] == selected_year]
            
            display_ipo = filtered_ipo[['stock_symbol', 'company_name', 'listing_date']]
            display_ipo.columns = ['Symbol', 'Company Name', 'Listing Date']
            
            # Listing wise sorting (Latest top par)
            display_ipo = display_ipo.sort_values(by='Listing Date', ascending=False)
            
            st.metric(label=f"Total Listings in {selected_year}", value=len(display_ipo))
            
            # Table Display
            st.dataframe(display_ipo, use_container_width=True, hide_index=True, height=400)
            
            # --- 🚀 NEW: TRADINGVIEW EXPORT FOR IPO (WITHOUT SECTIONS) ---
            if not display_ipo.empty:
                tv_ipo_text = ""
                # Har stock ke aage NSE: lagana bina kisi section divider ke
                for symbol in display_ipo['Symbol']:
                    tv_ipo_text += f"NSE:{symbol}\n"
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_i1, col_i2, col_i3 = st.columns([1, 2, 1])
                with col_i2:
                    st.download_button(
                        label=f"📥 Download {selected_year} IPO Watchlist (.txt)",
                        data=tv_ipo_text,
                        file_name=f"IPO_Watchlist_{selected_year}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        help="TradingView me 'Import List' par click karke is file ko upload karein."
                    )
                    
        else:
            st.info("⚠️ IPO data abhi database me nahi hai. Kripya GitHub Actions me jakar 'Daily IPO Tracker' ko ek baar manual run karein.")
    except Exception as e:
        st.error(f"Database Error: {e}")
