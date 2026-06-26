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

# 1. Page Configuration (Sidebar collapsed by default for full-width SaaS look)
st.set_page_config(page_title="AlphaSwing Pro", layout="wide", page_icon="📈", initial_sidebar_state="collapsed")

# --- 🎨 ADVANCED UI ENGINE (ANIMATED BG, CUSTOM HEADER, PREMIUM BUTTONS) ---
custom_css = """
<style>
    /* Global Font Size Increase */
    html, body, [class*="css"] {
        font-size: 1.05rem !important;
    }

    /* Animated Premium Gradient Background */
    .stApp {
        background: linear-gradient(-45deg, #09090b, #18181b, #0f172a, #171717);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        color: #f8fafc;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Top Padding Adjust */
    .block-container {
        padding-top: 1rem !important;
    }

    /* Custom Top Navigation Bar (Home & Login) */
    .top-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 20px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
    }
    
    /* Home Button Animation */
    .home-btn {
        font-size: 18px;
        font-weight: bold;
        color: #e2e8f0;
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        animation: pulseText 2s infinite;
    }
    @keyframes pulseText {
        0% { opacity: 0.8; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.02); text-shadow: 0 0 10px rgba(96, 165, 250, 0.5); }
        100% { opacity: 0.8; transform: scale(1); }
    }

    /* Login Menu Look */
    .login-menu {
        background: rgba(255, 255, 255, 0.1);
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: bold;
        cursor: pointer;
        transition: 0.3s;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .login-menu:hover {
        background: rgba(255, 255, 255, 0.2);
    }

    /* Premium Button Styling */
    div.stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 4px 12px; 
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        font-size: 14px !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5);
    }

    /* Secondary Download Buttons */
    div[data-testid="stDownloadButton"] > button {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255,255,255,0.2);
        color: #e2e8f0;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: #3b82f6;
    }

    /* Metric Adjustments (Smaller Font for Data) */
    div[data-testid="metric-container"] {
        background: rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 10px 15px;
        backdrop-filter: blur(5px);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.4rem !important; 
        color: #e2e8f0;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        color: #94a3b8;
    }

    /* Streamlit Tabs Styling */
    div[data-baseweb="tab-list"] {
        background: rgba(0,0,0,0.2);
        padding: 5px;
        border-radius: 10px;
        gap: 5px;
    }
    div[data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        color: #94a3b8;
    }
    div[data-baseweb="tab"][aria-selected="true"] {
        background: rgba(255, 255, 255, 0.1);
        color: #ffffff;
    }
    
    /* RESTORED: Journal Card Styling */
    .journal-card { 
        background: rgba(0,0,0,0.2); 
        border: 1px solid rgba(255,255,255,0.05); 
        padding: 20px; 
        border-radius: 12px; 
        margin-bottom: 20px; 
        backdrop-filter: blur(5px);
    }

    /* Hide standard header */
    header {visibility: hidden;}
    
    /* Notes Text Area Cleanup */
    .stTextArea textarea {
        background-color: rgba(0,0,0,0.2) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 2. Custom Top Navigation Bar (Home & Login)
st.markdown("""
<div class="top-navbar">
    <div class="home-btn">🏠 AlphaSwing Home</div>
    <div class="login-menu">👤 Login / Auth</div>
</div>
""", unsafe_allow_html=True)

# 3. Databases & APIs Setup
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

# Global Data Fetch
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

# 4. Tabs Setup
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Scanner", "⚙️ Rules", "🔥 Catalyst", "🏢 IPOs", "📓 Journal", "⚠️ Logs"])

# --- TAB 1: MAIN SCANNER ---
with tab1:
    col_run, col_empty = st.columns([1, 5])
    with col_run:
        if st.button("🚀 Run Scan", use_container_width=True):
            with st.spinner("Scanning..."):
                try:
                    token = st.secrets["GITHUB_TOKEN"]
                    repo = st.secrets["GITHUB_REPO"]
                    url = f"https://api.github.com/repos/{repo}/actions/workflows/daily_scan.yml/dispatches"
                    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
                    requests.post(url, headers=headers, json={"ref": "main"})
                    time.sleep(2)
                    st.success("✅ Initiated!")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    st.markdown("<br>", unsafe_allow_html=True)
        
    if raw_data:
        df = pd.DataFrame(raw_data)
        cols_to_keep = ['scan_date', 'stock_symbol', 'close_price', 'turnover_cr', 'sector', 'industry_proxy']
        df = df[[c for c in cols_to_keep if c in df.columns]]
        df.rename(columns={'scan_date': 'Scan Date', 'stock_symbol': 'Stock Symbol', 'close_price': 'Close Price (₹)', 'turnover_cr': 'Turnover (Cr)', 'sector': 'Sector', 'industry_proxy': 'Proxy / Industry'}, inplace=True)
        df = df.drop_duplicates(subset=['Scan Date', 'Stock Symbol'], keep='first')
        
        latest_date = df['Scan Date'].max()
        total_stocks = len(df[df['Scan Date'] == latest_date])
        
        m1, m2, m3 = st.columns([1, 1, 2])
        with m1: st.metric("📅 Last Scan Date", str(latest_date))
        with m2: st.metric("🎯 Breakout Count", f"{total_stocks}")
        
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
            st.download_button("📥 Watchlist (.txt)", data=tv_text, file_name=f"AlphaSwing_{selected_date}.txt", mime="text/plain", use_container_width=True)

        st.dataframe(df_filtered, use_container_width=True, height=350, hide_index=True)
    else:
        st.info("Database is empty.")

# --- TAB 2: Strategy Rules ---
with tab2:
    st.header("⚙️ Scanner Rules")
    st.write("• 1-Month, 3-Month & 52-Week High Breakouts.")
    st.write("• Heavy volume bursts (Turnover > 10Cr).")
    st.write("• Uptrend (Price sustained above key EMAs).")

# --- TAB 3: CATALYST PROMPT ---
with tab3:
    default_idx = master_symbol_list.index("RELIANCE") if "RELIANCE" in master_symbol_list else 0
    user_ticker = st.selectbox("🔤 Select Stock Symbol:", master_symbol_list, index=default_idx)
    
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
        <button id="copyPromptBtn" style="background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%; font-family: sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">📋 Copy Full Prompt</button>
        <script>
        document.getElementById('copyPromptBtn').addEventListener('click', function() {{
            navigator.clipboard.writeText({escaped_prompt_json}).then(function() {{
                const btn = document.getElementById('copyPromptBtn');
                btn.style.background = '#10b981';
                btn.innerText = '✅ Prompt Copied!';
                setTimeout(() => {{
                    btn.style.background = 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)';
                    btn.innerText = '📋 Copy Full Prompt';
                }}, 2000);
            }});
        }});
        </script>
    """, height=50)

# --- TAB 4: IPO TRACKER ---
with tab4:
    if raw_ipo_data:
        df_ipo = pd.DataFrame(raw_ipo_data)
        if 'listing_date' in df_ipo.columns:
            df_ipo['calc_date'] = pd.to_datetime(df_ipo['listing_date'], errors='coerce')
            df_ipo['Month'] = df_ipo['calc_date'].dt.strftime('%B')
            today = pd.to_datetime('today').date()
            today_listed = len(df_ipo[df_ipo['calc_date'].dt.date == today])
            this_month = len(df_ipo[(df_ipo['calc_date'].dt.month == today.month) & (df_ipo['calc_date'].dt.year == today.year)])
            
            m1, m2, m3 = st.columns([1, 1, 2])
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
            st.download_button("📥 Watchlist (.txt)", data=tv_ipo_text, file_name=f"IPO_{selected_year}.txt", mime="text/plain", use_container_width=True)
            
        st.dataframe(display_ipo, use_container_width=True, hide_index=True, height=350)

# --- TAB 5: TRADING JOURNAL (RESTORED PRO VERSION) ---
with tab5:
    st.header("📓 Pro Trading Journal (20-50-30 Rule)")
    
    j_tab1, j_tab2, j_tab3 = st.tabs(["➕ New Trade Entry", "🔄 Update Exits & TSL", "📚 Journal Gallery"])
    
    # --- SUB-TAB 1: NEW TRADE ---
    with j_tab1:
        with st.form("new_trade_form", clear_on_submit=True):
            st.subheader("Enter New Trade Details")
            c1, c2, c3 = st.columns(3)
            with c1:
                symbol = st.text_input("Stock Symbol (e.g., RELIANCE)").upper()
                quantity = st.number_input("Total Quantity", min_value=1, step=1)
            with c2:
                buying_date = st.date_input("Buying Date", datetime.date.today())
                buying_price = st.number_input("Buying Price (₹)", min_value=0.0, step=0.1, format="%.2f")
            with c3:
                initial_sl = st.number_input("Initial Stoploss (₹)", min_value=0.0, step=0.1, format="%.2f")
            
            trade_logic = st.text_area("Trade Logic (Setup, EMA, Breakout, etc.)")
            image_file = st.file_uploader("Upload Chart Screenshot (Optional)", type=['png', 'jpg', 'jpeg'])
            
            submit_trade = st.form_submit_button("💾 Save Trade", use_container_width=True)
            
            if submit_trade and symbol and quantity > 0 and buying_price > 0:
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

    # --- SUB-TAB 2: UPDATE TRADE (Exits & TSL) ---
    with j_tab2:
        try:
            active_res = supabase.table('trading_journal').select("*").is_("sold_30_date", "null").execute()
            active_trades = active_res.data
            
            if active_trades:
                trade_options = {f"{t['symbol']} (Bought: {t['buying_date']} @ ₹{t['buying_price']})": t for t in active_trades}
                selected_trade_label = st.selectbox("🎯 Select Active Trade to Update", list(trade_options.keys()))
                t = trade_options[selected_trade_label]
                
                st.markdown(f"**Current Total Quantity:** {t['total_quantity']} | **Buy Price:** ₹{t['buying_price']}")
                
                with st.form("update_trade_form"):
                    st.markdown("### 1️⃣ 20% Quantity Booking")
                    c1, c2, c3 = st.columns(3)
                    with c1: s20_date = st.date_input("20% Sold Date", value=None)
                    with c2: s20_price = st.number_input("20% Sold Price", value=float(t['sold_20_price'] or 0.0))
                    with c3:
                        st.caption("💡 Leave 0 to auto-shift SL to Breakeven")
                        sl_20 = st.number_input("New SL After 20%", value=float(t['sl_after_20'] or 0.0))
                        
                    st.markdown("### 2️⃣ 50% Quantity Booking")
                    c4, c5, c6 = st.columns(3)
                    with c4: s50_date = st.date_input("50% Sold Date", value=None)
                    with c5: s50_price = st.number_input("50% Sold Price", value=float(t['sold_50_price'] or 0.0))
                    with c6: sl_50 = st.number_input("New TSL After 50%", value=float(t['sl_after_50'] or 0.0))
                    
                    st.markdown("### 3️⃣ Final 30% Quantity Booking")
                    c7, c8 = st.columns(2)
                    with c7: s30_date = st.date_input("30% Sold Date", value=None)
                    with c8: s30_price = st.number_input("30% Sold Price", value=float(t['sold_30_price'] or 0.0))

                    update_btn = st.form_submit_button("🔄 Update Exits & SL")
                    
                    if update_btn:
                        final_sl_20 = sl_20
                        if s20_price > 0 and sl_20 == 0:
                            final_sl_20 = float(t['buying_price'])
                            st.toast("Auto-shifted SL to Breakeven!")

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
                st.info("No active trades found. Add a trade first.")
        except Exception as e:
            st.error(f"Error fetching active trades: {e}")

    # --- SUB-TAB 3: JOURNAL GALLERY ---
    with j_tab3:
        try:
            all_trades_res = supabase.table('trading_journal').select("*").order('buying_date', desc=True).execute()
            all_trades = all_trades_res.data
            
            if all_trades:
                for tr in all_trades:
                    st.markdown("<div class='journal-card'>", unsafe_allow_html=True)
                    g1, g2 = st.columns([1, 2])
                    
                    with g1:
                        if tr.get('image_url'):
                            st.image(tr['image_url'], use_container_width=True)
                        else:
                            st.info("No chart uploaded.")
                    with g2:
                        st.subheader(f"🚀 {tr['symbol']}")
                        st.write(f"**Date:** {tr['buying_date']} | **Buy Price:** ₹{tr['buying_price']} | **Qty:** {tr['total_quantity']}")
                        st.write(f"**Logic:** {tr['trade_logic']}")
                        
                        if tr.get('sold_20_price'):
                            ret_20 = ((tr['sold_20_price'] - tr['buying_price']) / tr['buying_price']) * 100
                            st.success(f"**20% Booked @ ₹{tr['sold_20_price']} (Return: {ret_20:.2f}%)**")
                        if tr.get('sold_50_price'):
                            ret_50 = ((tr['sold_50_price'] - tr['buying_price']) / tr['buying_price']) * 100
                            st.success(f"**50% Booked @ ₹{tr['sold_50_price']} (Return: {ret_50:.2f}%)**")
                        if tr.get('sold_30_price'):
                            ret_30 = ((tr['sold_30_price'] - tr['buying_price']) / tr['buying_price']) * 100
                            st.success(f"**30% Final Booked @ ₹{tr['sold_30_price']} (Return: {ret_30:.2f}%)**")
                            
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Journal khali hai. Start trading!")
        except Exception as e:
            st.error(f"Error loading gallery: {e}")

# --- TAB 6: LOGS ---
with tab6:
    st.header("⚠️ Error Logs")
    if st.button("Clear Logs"): st.success("Cleared!")

# --- 📝 GLOBAL NOTES (Minimal Layout) ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Notes")

try:
    note_res = supabase.table('global_notes').select('note_text').eq('id', 1).execute()
    saved_text = note_res.data[0]['note_text'] if note_res.data else ""
except:
    saved_text = ""

with st.form("global_scratchpad_form"):
    user_notes = st.text_area(" ", value=saved_text, height=200, label_visibility="collapsed")
    
    col_save, col_spacer = st.columns([1, 5])
    with col_save:
        if st.form_submit_button("💾 Save Notes", use_container_width=True):
            supabase.table('global_notes').upsert({"id": 1, "note_text": user_notes}).execute()
            st.toast("✅ Saved!")
            time.sleep(0.5)
            st.rerun()
