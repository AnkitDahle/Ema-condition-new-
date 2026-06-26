import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import requests
import pandas as pd
import time
import datetime
import cloudinary
import cloudinary.uploader
import json

# 1. Page Configuration (Sidebar collapsed for full-width screener look)
st.set_page_config(page_title="AlphaSwing Pro", layout="wide", page_icon="📈", initial_sidebar_state="collapsed")

# Initialize Session State for Navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# --- 🎨 CHARTINK STYLE UI ENGINE (FUNCTIONAL, SOLID, DATA-DENSE) ---
custom_css = """
<style>
    /* Base App Styling - Solid Dark Theme like Chartink Dark Mode */
    .stApp {
        background-color: #121419;
        color: #d1d4dc;
    }

    /* Top Padding Adjust */
    .block-container {
        padding-top: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* Hide standard header */
    header {visibility: hidden;}

    /* Custom Top Navigation Bar (Chartink Style) */
    .top-navbar-container {
        background-color: #1a1e25;
        border-bottom: 2px solid #2962ff;
        padding: 10px 20px;
        margin: -4rem -1rem 20px -1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .brand-logo {
        font-size: 20px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 0.5px;
    }
    .brand-logo span {
        color: #2962ff;
    }

    /* Functional Button Styling (Square, Solid Colors) */
    div.stButton > button {
        background-color: #2962ff;
        color: white;
        border-radius: 3px;
        font-weight: 600;
        border: none;
        padding: 4px 15px; 
        transition: 0.2s ease;
        font-size: 14px !important;
        box-shadow: none !important;
    }
    div.stButton > button:hover {
        background-color: #1e4bd8;
        border: none;
        color: white;
    }

    /* Specific Green Button for "Run Scan" */
    .btn-run-scan button {
        background-color: #00c853 !important;
    }
    .btn-run-scan button:hover {
        background-color: #00e676 !important;
    }

    /* Secondary Download Buttons */
    div[data-testid="stDownloadButton"] > button {
        background-color: #2a2e39;
        border: 1px solid #363c4e;
        color: #d1d4dc;
        border-radius: 3px;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #363c4e;
        border-color: #2962ff;
        color: white;
    }

    /* Metric Adjustments (Clean Data Boxes) */
    div[data-testid="metric-container"] {
        background-color: #1a1e25;
        border: 1px solid #2a2e39;
        border-radius: 4px;
        padding: 12px 15px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important; 
        color: #ffffff;
        font-weight: 700;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        color: #8a93a6;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Streamlit Tabs Styling (Functional Web Tabs) */
    div[data-baseweb="tab-list"] {
        background-color: transparent;
        border-bottom: 1px solid #2a2e39;
        gap: 0;
        padding: 0;
    }
    div[data-baseweb="tab"] {
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        color: #8a93a6;
        background-color: #1a1e25;
        border: 1px solid transparent;
        margin-right: 5px;
    }
    div[data-baseweb="tab"][aria-selected="true"] {
        background-color: #2962ff;
        color: #ffffff;
        border-color: #2962ff;
        font-weight: bold;
    }
    
    /* Journal Card Styling */
    .journal-card { 
        background-color: #1a1e25; 
        border: 1px solid #2a2e39; 
        padding: 20px; 
        border-radius: 4px; 
        margin-bottom: 15px; 
    }

    /* Input Fields & Text Areas */
    .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #1a1e25 !important;
        color: white !important;
        border: 1px solid #363c4e !important;
        border-radius: 3px !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 2. TOP NAVIGATION BAR (Chartink Style)
st.markdown("""
<div class="top-navbar-container">
    <div class="brand-logo">AlphaSwing <span>Pro</span></div>
    <div style='font-size: 14px; font-weight: 500; color: #8a93a6;'>User: Ankit Dahle | Account: Premium</div>
</div>
""", unsafe_allow_html=True)

nav_c1, nav_c2, nav_c3 = st.columns([1.5, 1.5, 7])
with nav_c1:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.current_page = "Home"
        st.rerun()
with nav_c2:
    if st.button("📊 Screener", use_container_width=True):
        st.session_state.current_page = "Dashboard"
        st.rerun()
with nav_c3:
    pass # Empty space for alignment

st.markdown("<hr style='margin-top: 5px; border-color: #2a2e39;'>", unsafe_allow_html=True)

# ==========================================
# 🏠 PAGE 1: HOME PAGE
# ==========================================
if st.session_state.current_page == "Home":
    st.markdown("""
        <div style='text-align: center; padding: 100px 0;'>
            <h1 style='font-size: 40px; color: #ffffff;'>Welcome to <span style='color: #2962ff;'>AlphaSwing Pro</span></h1>
            <p style='color: #8a93a6; font-size: 18px;'>Your advanced momentum scanning and trading journal platform.</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #50586e;'>Home page is currently empty. Click 'Screener' to view the dashboard.</p>", unsafe_allow_html=True)

# ==========================================
# 📈 PAGE 2: DASHBOARD (SCANNER & TOOLS)
# ==========================================
elif st.session_state.current_page == "Dashboard":

    # --- Databases & APIs Setup ---
    @st.cache_resource
    def init_supabase():
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)

    supabase = init_supabase()

    cloudinary.config(
        cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key=st.secrets["CLOUDINARY_API_KEY"],
        api_secret=st.secrets["CLOUDINARY_API_SECRET"]
    )

    # --- Global Data Fetch ---
    try:
        response = supabase.table('swing_stocks').select("*").order('scan_date', desc=True).execute()
        raw_data = response.data
    except Exception as e:
        st.error(f"Database Error: {e}")
        raw_data = None

    try:
        ipo_res = supabase.table('ipo_master').select("*").execute()
        raw_ipo_data = ipo_res.data
    except Exception as e:
        st.error(f"Database Error: {e}")
        raw_ipo_data = None

    master_symbol_list = ["RELIANCE", "TCS", "INFY", "ZOMATO", "SBIN"]
    if raw_data:
        master_symbol_list.extend([str(x).upper() for x in pd.DataFrame(raw_data)['stock_symbol'].dropna().unique()])
    if raw_ipo_data:
        master_symbol_list.extend([str(x).upper() for x in pd.DataFrame(raw_ipo_data)['stock_symbol'].dropna().unique()])
    master_symbol_list = sorted(list(set(master_symbol_list)))

    # --- 📌 TABS ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Screener Results", "⚙️ Scan Conditions", "🔥 Catalyst Research", "🏢 IPOs", "📓 Trades", "⚠️ Logs"])

    # --- TAB 1: MAIN SCANNER ---
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        col_run, col_empty = st.columns([1.5, 6])
        with col_run:
            st.markdown("<div class='btn-run-scan'>", unsafe_allow_html=True)
            if st.button("▶ Run Scanner", use_container_width=True):
                with st.spinner("Executing Scan..."):
                    try:
                        token = st.secrets["GITHUB_TOKEN"]
                        repo = st.secrets["GITHUB_REPO"]
                        url = f"https://api.github.com/repos/{repo}/actions/workflows/daily_scan.yml/dispatches"
                        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
                        requests.post(url, headers=headers, json={"ref": "main"})
                        time.sleep(2)
                        st.success("✅ Scan Initiated!")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
            
        if raw_data:
            df = pd.DataFrame(raw_data)
            cols_to_keep = ['scan_date', 'stock_symbol', 'close_price', 'turnover_cr', 'sector', 'industry_proxy']
            df = df[[c for c in cols_to_keep if c in df.columns]]
            df.rename(columns={'scan_date': 'Scan Date', 'stock_symbol': 'Stock Symbol', 'close_price': 'Close Price (₹)', 'turnover_cr': 'Turnover (Cr)', 'sector': 'Sector', 'industry_proxy': 'Proxy / Industry'}, inplace=True)
            df = df.drop_duplicates(subset=['Scan Date', 'Stock Symbol'], keep='first')
            
            latest_date = df['Scan Date'].max()
            total_stocks = len(df[df['Scan Date'] == latest_date])
            
            m1, m2, m3 = st.columns([1.5, 1.5, 4])
            with m1: st.metric("📅 Last Scan Date", str(latest_date))
            with m2: st.metric("🎯 Total Breakouts", f"{total_stocks}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            f_col1, f_col2, f_col3, f_col4 = st.columns([1.5, 1.5, 1.5, 1.2])
            with f_col1: selected_date = st.selectbox("📅 Scan Date", sorted(df['Scan Date'].unique(), reverse=True))
            df_filtered = df[df['Scan Date'] == selected_date]
            
            with f_col2:
                sector_list = ["All Sectors"] + list(df['Sector'].dropna().unique()) if 'Sector' in df.columns else ["All Sectors"]
                selected_sector = st.selectbox("🎯 Sector", sector_list)
                    
            with f_col3: 
                scanner_symbols = ["All Stocks"] + sorted(list(df_filtered['Stock Symbol'].dropna().unique()))
                selected_stock = st.selectbox("🔤 Search Stock", scanner_symbols)

            if selected_sector != "All Sectors": df_filtered = df_filtered[df_filtered['Sector'] == selected_sector]
            if selected_stock != "All Stocks": df_filtered = df_filtered[df_filtered['Stock Symbol'] == selected_stock]

            tv_text = ""
            if not df_filtered.empty:
                sorted_df = df_filtered.sort_values(by=['Sector', 'Proxy / Industry'])
                for (sec, proxy), group in sorted_df.groupby(['Sector', 'Proxy / Industry']):
                    tv_text += f"### {sec} / {proxy}\n"
                    for sym in group['Stock Symbol']: tv_text += f"NSE:{sym}\n"
            
            with f_col4:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                st.download_button("📥 Export (.txt)", data=tv_text, file_name=f"AlphaSwing_{selected_date}.txt", mime="text/plain", use_container_width=True)

            st.dataframe(df_filtered, use_container_width=True, height=400, hide_index=True)
        else:
            st.info("Database is empty.")

    # --- TAB 2: Strategy Rules ---
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Active Scan Conditions")
        st.code("""
        # Momentum Breakout Setup
        Condition 1: Close Price > 1-Month High
        Condition 2: Close Price > 3-Month High
        Condition 3: Close Price > 52-Week High
        Condition 4: Daily Volume Turnover > 10 Crores
        Condition 5: Close Price > 20 EMA > 50 EMA > 200 EMA
        """, language="text")

    # --- TAB 3: CATALYST PROMPT ---
    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        default_idx = master_symbol_list.index("RELIANCE") if "RELIANCE" in master_symbol_list else 0
        user_ticker = st.selectbox("🔤 Select Stock Symbol for Analysis:", master_symbol_list, index=default_idx)
        
        catalyst_prompt = f"""Please analyze {user_ticker} for me and provide the following, concise and clearly organized:
1. Explain what the company does like I'm 12 years old.
2. Professional summary (industry, peers, moat).
3. Table: Hot themes, Catalysts, Significant fundamentals.
4. Main news/events for the last 3 months.
5. Recent insider buys/sells.
6. Stock movement vs competitors.
7. Upcoming catalysts in next 30 days.
8. Analyst price target changes."""

        st.code(catalyst_prompt, language="text")
        escaped_prompt_json = json.dumps(catalyst_prompt)
        
        components.html(f"""
            <button id="copyPromptBtn" style="background-color: #2962ff; color: white; border: none; padding: 10px 20px; border-radius: 3px; font-weight: bold; cursor: pointer; width: 100%; font-family: sans-serif; font-size: 14px;">📋 Copy Full Prompt</button>
            <script>
            document.getElementById('copyPromptBtn').addEventListener('click', function() {{
                navigator.clipboard.writeText({escaped_prompt_json}).then(function() {{
                    const btn = document.getElementById('copyPromptBtn');
                    btn.style.backgroundColor = '#00c853';
                    btn.innerText = '✅ Prompt Copied!';
                    setTimeout(() => {{
                        btn.style.backgroundColor = '#2962ff';
                        btn.innerText = '📋 Copy Full Prompt';
                    }}, 2000);
                }});
            }});
            </script>
        """, height=50)

    # --- TAB 4: IPO TRACKER ---
    with tab4:
        st.markdown("<br>", unsafe_allow_html=True)
        if raw_ipo_data:
            df_ipo = pd.DataFrame(raw_ipo_data)
            if 'listing_date' in df_ipo.columns:
                df_ipo['calc_date'] = pd.to_datetime(df_ipo['listing_date'], errors='coerce')
                df_ipo['Month'] = df_ipo['calc_date'].dt.strftime('%B')
                today = pd.to_datetime('today').date()
                today_listed = len(df_ipo[df_ipo['calc_date'].dt.date == today])
                this_month = len(df_ipo[(df_ipo['calc_date'].dt.month == today.month) & (df_ipo['calc_date'].dt.year == today.year)])
                
                m1, m2, m3 = st.columns([1.5, 1.5, 4])
                with m1: st.metric("Today Listed", today_listed)
                with m2: st.metric("This Month", this_month)
                
                st.markdown("<br>", unsafe_allow_html=True)

            col_y1, col_m1, col_search, col_dl = st.columns([1.2, 1.2, 1.5, 1.2])
            
            with col_y1: selected_year = st.selectbox("📅 IPO Year:", sorted(df_ipo['listing_year'].dropna().unique(), reverse=True))
            with col_m1: selected_month = st.selectbox("🗓️ Month:", ["All Months", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
            
            fil = df_ipo[df_ipo['listing_year'] == selected_year]
            if selected_month != "All Months": fil = fil[fil['Month'] == selected_month]
            
            with col_search: selected_ipo_stock = st.selectbox("🔤 Search IPO:", ["All IPOs"] + sorted(list(fil['stock_symbol'].dropna().unique())))
            
            filtered_ipo = fil
            if selected_ipo_stock != "All IPOs": filtered_ipo = filtered_ipo[filtered_ipo['stock_symbol'] == selected_ipo_stock]
            
            display_ipo = filtered_ipo[['stock_symbol', 'company_name', 'listing_date']].sort_values(by='listing_date', ascending=False)
            display_ipo.columns = ['Symbol', 'Company Name', 'Listing Date']
            
            tv_ipo_text = ""
            for sym in display_ipo['Symbol']: tv_ipo_text += f"NSE:{sym}\n"
            
            with col_dl:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                st.download_button("📥 Export (.txt)", data=tv_ipo_text, file_name=f"IPO_{selected_year}.txt", mime="text/plain", use_container_width=True)
                
            st.dataframe(display_ipo, use_container_width=True, hide_index=True, height=400)

    # --- TAB 5: TRADING JOURNAL ---
    with tab5:
        st.markdown("<br>", unsafe_allow_html=True)
        j_tab1, j_tab2, j_tab3 = st.tabs(["➕ New Trade", "🔄 Update Exits", "📚 Journal Data"])
        
        with j_tab1:
            with st.form("new_trade_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    symbol = st.text_input("Stock Symbol (e.g., RELIANCE)").upper()
                    quantity = st.number_input("Total Quantity", min_value=1, step=1)
                with c2:
                    buying_date = st.date_input("Buying Date", datetime.date.today())
                    buying_price = st.number_input("Buying Price (₹)", min_value=0.0, step=0.1, format="%.2f")
                with c3:
                    initial_sl = st.number_input("Initial Stoploss (₹)", min_value=0.0, step=0.1, format="%.2f")
                
                trade_logic = st.text_area("Trade Logic")
                image_file = st.file_uploader("Upload Chart Screenshot (Optional)", type=['png', 'jpg', 'jpeg'])
                
                if st.form_submit_button("💾 Save Trade", use_container_width=True) and symbol and quantity > 0 and buying_price > 0:
                    with st.spinner("Saving trade..."):
                        img_url = None
                        if image_file is not None:
                            res = cloudinary.uploader.upload(image_file, folder="trading_journal")
                            img_url = res.get("secure_url")
                        
                        data = {
                            "symbol": symbol, "total_quantity": quantity, "buying_date": str(buying_date),
                            "buying_price": float(buying_price), "initial_sl": float(initial_sl),
                            "trade_logic": trade_logic, "image_url": img_url
                        }
                        try:
                            supabase.table('trading_journal').insert(data).execute()
                            st.success(f"✅ Trade {symbol} saved successfully!")
                        except Exception as e:
                            st.error(f"Error saving data: {e}")

        with j_tab2:
            try:
                active_res = supabase.table('trading_journal').select("*").is_("sold_30_date", "null").execute()
                active_trades = active_res.data
                
                if active_trades:
                    trade_options = {f"{t['symbol']} (Bought: {t['buying_date']} @ ₹{t['buying_price']})": t for t in active_trades}
                    selected_trade_label = st.selectbox("🎯 Select Active Trade to Update", list(trade_options.keys()))
                    t = trade_options[selected_trade_label]
                    
                    st.markdown(f"**Qty:** {t['total_quantity']} | **Buy Price:** ₹{t['buying_price']}")
                    
                    with st.form("update_trade_form"):
                        c1, c2, c3 = st.columns(3)
                        with c1: s20_date = st.date_input("20% Sold Date", value=None)
                        with c2: s20_price = st.number_input("20% Sold Price", value=float(t['sold_20_price'] or 0.0))
                        with c3: sl_20 = st.number_input("New SL (0 for BE)", value=float(t['sl_after_20'] or 0.0))
                            
                        c4, c5, c6 = st.columns(3)
                        with c4: s50_date = st.date_input("50% Sold Date", value=None)
                        with c5: s50_price = st.number_input("50% Sold Price", value=float(t['sold_50_price'] or 0.0))
                        with c6: sl_50 = st.number_input("New TSL After 50%", value=float(t['sl_after_50'] or 0.0))
                        
                        c7, c8 = st.columns(2)
                        with c7: s30_date = st.date_input("30% Sold Date", value=None)
                        with c8: s30_price = st.number_input("30% Sold Price", value=float(t['sold_30_price'] or 0.0))

                        if st.form_submit_button("🔄 Update Exits & SL"):
                            final_sl_20 = sl_20
                            if s20_price > 0 and sl_20 == 0:
                                final_sl_20 = float(t['buying_price'])

                            update_data = {
                                "sold_20_date": str(s20_date) if s20_price > 0 else None, "sold_20_price": s20_price if s20_price > 0 else None, "sl_after_20": final_sl_20 if final_sl_20 > 0 else None,
                                "sold_50_date": str(s50_date) if s50_price > 0 else None, "sold_50_price": s50_price if s50_price > 0 else None, "sl_after_50": sl_50 if sl_50 > 0 else None,
                                "sold_30_date": str(s30_date) if s30_price > 0 else None, "sold_30_price": s30_price if s30_price > 0 else None,
                            }
                            supabase.table('trading_journal').update(update_data).eq('id', t['id']).execute()
                            st.success("Trade updated successfully!")
                            time.sleep(1)
                            st.rerun()
                else:
                    st.info("No active trades found.")
            except Exception as e:
                st.error(f"Error fetching active trades: {e}")

        with j_tab3:
            try:
                all_trades_res = supabase.table('trading_journal').select("*").order('buying_date', desc=True).execute()
                all_trades = all_trades_res.data
                
                if all_trades:
                    for tr in all_trades:
                        st.markdown("<div class='journal-card'>", unsafe_allow_html=True)
                        g1, g2 = st.columns([1, 3])
                        with g1:
                            if tr.get('image_url'):
                                st.image(tr['image_url'], use_container_width=True)
                            else:
                                st.info("No chart")
                        with g2:
                            st.subheader(f"🚀 {tr['symbol']}")
                            st.write(f"**Date:** {tr['buying_date']} | **Buy Price:** ₹{tr['buying_price']} | **Qty:** {tr['total_quantity']}")
                            st.write(f"**Logic:** {tr['trade_logic']}")
                            
                            if tr.get('sold_20_price'):
                                st.success(f"**20% Booked @ ₹{tr['sold_20_price']}**")
                            if tr.get('sold_50_price'):
                                st.success(f"**50% Booked @ ₹{tr['sold_50_price']}**")
                            if tr.get('sold_30_price'):
                                st.success(f"**30% Final Booked @ ₹{tr['sold_30_price']}**")
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info("Journal is empty.")
            except Exception as e:
                st.error(f"Error loading gallery: {e}")

    # --- TAB 6: LOGS ---
    with tab6:
        st.markdown("<br>", unsafe_allow_html=True)
        st.header("⚠️ Error Logs")
        if st.button("Clear Logs"): st.success("Cleared!")

    # --- 📝 GLOBAL NOTES (Chartink Style Bottom Panel) ---
    st.markdown("<br><hr style='border-color: #2a2e39;'><br>", unsafe_allow_html=True)
    st.markdown("### 📝 Sticky Notes")

    try:
        note_res = supabase.table('global_notes').select('note_text').eq('id', 1).execute()
        saved_text = note_res.data[0]['note_text'] if note_res.data else ""
    except:
        saved_text = ""

    with st.form("global_scratchpad_form"):
        user_notes = st.text_area(" ", value=saved_text, height=150, label_visibility="collapsed")
        
        col_save, col_spacer = st.columns([1.5, 6])
        with col_save:
            if st.form_submit_button("💾 Save Notes", use_container_width=True):
                supabase.table('global_notes').upsert({"id": 1, "note_text": user_notes}).execute()
                st.toast("✅ Notes Saved!")
                time.sleep(0.5)
                st.rerun()
