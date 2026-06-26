import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import requests
import pandas as pd
import time
import datetime
import cloudinary
import cloudinary.uploader

# 1. Page Configuration
st.set_page_config(page_title="AlphaSwing Pro | Momentum Scanner", layout="wide", page_icon="📈")

# Custom Styling for Buttons & Journal Cards
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    .btn-green button { background-color: #4CAF50; color: white; border-radius: 6px; font-weight: bold; padding: 8px; width: 100%; border: none;}
    .btn-green button:hover { background-color: #45a049; }
    .btn-red button { background-color: #D32F2F; color: white; border-radius: 6px; font-weight: bold; padding: 8px; width: 100%; border: none;}
    .btn-red button:hover { background-color: #b71c1c; }
    .journal-card { border: 1px solid #333; padding: 15px; border-radius: 8px; background-color: #1e1e1e; margin-bottom: 15px;}
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
            strings: ['Swing Trading.', 'Live Market Scans.', 'Technical Analysis.', 'Pro Trading Journal.'],
            typeSpeed: 60, backSpeed: 40, backDelay: 1500, loop: true, showCursor: true, cursorChar: '|'
        });
    </script>
    """,
    height=120,
)
st.markdown("---")

# 4. Databases & APIs Setup
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Cloudinary Setup
cloudinary.config(
    cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key=st.secrets["CLOUDINARY_API_KEY"],
    api_secret=st.secrets["CLOUDINARY_API_SECRET"]
)

# Fetch Scan Data
try:
    response = supabase.table('swing_stocks').select("*").order('scan_date', desc=True).execute()
    raw_data = response.data
except Exception as e:
    st.error(f"Database Error: {e}")
    raw_data = None

# 5. Tabs Setup
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Combined Scanner", "⚙️ Strategy Rules", "💡 Trading Guide", "🏢 IPO Tracker", "📓 Trading Journal", "⚠️ Error Logs"])

# --- TAB 1: MAIN SCANNER ---
with tab1:
    st.markdown("##### ⚡ Live Scanner Dashboard Controls")
    colA, colB, colC = st.columns([1.2, 1.2, 2.5])
    
    with colA:
        st.markdown("<div class='btn-green'>", unsafe_allow_html=True)
        if st.button("🚀 Run Scan Now", use_container_width=True):
            with st.spinner("Wait..."):
                try:
                    token = st.secrets["GITHUB_TOKEN"]
                    repo = st.secrets["GITHUB_REPO"]
                    url = f"https://api.github.com/repos/{repo}/actions/workflows/daily_scan.yml/dispatches"
                    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
                    requests.post(url, headers=headers, json={"ref": "main"})
                    time.sleep(2)
                    st.success("✅ Scan Shuru!")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown("<div class='btn-red'>", unsafe_allow_html=True)
        if st.button("🛑 Stop Scan", use_container_width=True):
            with st.spinner("Stopping..."):
                try:
                    token = st.secrets["GITHUB_TOKEN"]
                    repo = st.secrets["GITHUB_REPO"]
                    url_get = f"https://api.github.com/repos/{repo}/actions/runs?status=in_progress"
                    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
                    res = requests.get(url_get, headers=headers)
                    runs = res.json().get("workflow_runs", [])
                    if runs:
                        for run in runs:
                            requests.post(f"https://api.github.com/repos/{repo}/actions/runs/{run['id']}/cancel", headers=headers)
                        st.success("🛑 Scan Roka Gaya!")
                except Exception as e:
                    st.error(f"Error: {e}")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with colC:
        live_tracking = st.toggle("🔄 Enable Live Auto-Refresh (15s)")
        if live_tracking:
            time.sleep(15)
            st.rerun()

    st.markdown("---")
        
    if raw_data:
        df = pd.DataFrame(raw_data)
        cols_to_keep = ['scan_date', 'stock_symbol', 'close_price', 'turnover_cr', 'sector', 'industry_proxy']
        existing_cols = [c for c in cols_to_keep if c in df.columns]
        df = df[existing_cols]
        
        rename_dict = {'scan_date': 'Scan Date', 'stock_symbol': 'Stock Symbol', 'close_price': 'Close Price (₹)', 'turnover_cr': 'Turnover (Cr)', 'sector': 'Sector', 'industry_proxy': 'Proxy / Industry'}
        df.rename(columns=rename_dict, inplace=True)
        
        # 🚀 YAHAN PAR DUPLICATES HATAYE GAYE HAIN
        df = df.drop_duplicates(subset=['Scan Date', 'Stock Symbol'], keep='first')
        
        latest_date = df['Scan Date'].max()
        total_stocks = len(df[df['Scan Date'] == latest_date])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📅 Last Scan Date", str(latest_date))
        col2.metric("🎯 Latest Breakout Count", f"{total_stocks} Stocks")
        col3.metric("🏢 Market Covered", "NSE 2300+ Stocks")
        
        st.markdown("---")
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1: selected_date = st.selectbox("📅 Select Scan Date", sorted(df['Scan Date'].unique(), reverse=True))
        df_filtered = df[df['Scan Date'] == selected_date]
        
        with f_col2:
            if 'Sector' in df.columns:
                sector_list = ["All Sectors"] + list(df['Sector'].dropna().unique())
                selected_sector = st.selectbox("🎯 Filter by Sector", sector_list)
            else: selected_sector = "All Sectors"
                
        with f_col3: search_symbol = st.text_input("🔤 Search Stock", "").upper()

        if selected_sector != "All Sectors": df_filtered = df_filtered[df_filtered['Sector'] == selected_sector]
        if search_symbol: df_filtered = df_filtered[df_filtered['Stock Symbol'].str.contains(search_symbol)]

        st.dataframe(df_filtered, use_container_width=True, height=400, hide_index=True)
        
        if not df_filtered.empty:
            tv_text = ""
            sorted_df = df_filtered.sort_values(by=['Sector', 'Proxy / Industry'])
            grouped = sorted_df.groupby(['Sector', 'Proxy / Industry'])
            for (sector, proxy), group in grouped:
                tv_text += f"### {sector} / {proxy}\n"
                for symbol in group['Stock Symbol']: tv_text += f"NSE:{symbol}\n"
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_d1, col_d2, col_d3 = st.columns([1, 2, 1])
            with col_d2:
                st.download_button("📥 Download TradingView Watchlist (.txt)", data=tv_text, file_name=f"AlphaSwing_{selected_date}.txt", mime="text/plain", use_container_width=True)
    else:
        st.info("Database mein abhi koi data nahi hai.")

# --- TAB 2 & 3: Strategy Rules and Guide ---
with tab2:
    st.header("⚙️ Scanner Rules")
    st.write("📈 **Pure Momentum & Breakout Setup:**")
    st.write("• 1-Month, 3-Month aur 52-Week High Breakouts par strong focus.")
    st.write("• High Relative Strength aur heavy volume bursts (Turnover > 10Cr) wale stocks.")
    st.write("• Strong uptrend (Price apne key EMAs ke upar sustain kar raha ho).")
with tab3:
    st.header("💡 Trading Guide")
    st.write("Hamesha 2-3% ka Stoploss use karein aur 1:2 Risk Reward ratio follow karein.")

# --- TAB 4: IPO TRACKER ---
with tab4:
    st.header("🏢 IPO & New Listings Tracker (2020 - Present)")
    try:
        ipo_res = supabase.table('ipo_master').select("*").execute()
        if ipo_res.data:
            df_ipo = pd.DataFrame(ipo_res.data)
            
            # --- 🚀 UPDATED: 2 CLEAN METRICS (Today, This Month) ---
            if 'listing_date' in df_ipo.columns:
                df_ipo['calc_date'] = pd.to_datetime(df_ipo['listing_date'], errors='coerce')
                
                today = pd.to_datetime('today').date()
                
                # Calculations
                today_listed_count = len(df_ipo[df_ipo['calc_date'].dt.date == today])
                this_month_count = len(df_ipo[(df_ipo['calc_date'].dt.month == today.month) & (df_ipo['calc_date'].dt.year == today.year)])
                
                # Metrics UI Display (2 Columns)
                st.markdown("### 📊 IPO Market Overview")
                m1, m2 = st.columns(2)
                with m1:
                    st.metric(label="Today Listed", value=today_listed_count)
                with m2:
                    st.metric(label="This Month", value=this_month_count)
                
                st.divider()
            # ----------------------------------------------------

            col_y1, col_y2, col_y3 = st.columns([1.5, 1.5, 3])
            with col_y1:
                years = sorted(df_ipo['listing_year'].dropna().unique(), reverse=True)
                selected_year = st.selectbox("📅 Select IPO Year:", years)
            
            filtered_ipo = df_ipo[df_ipo['listing_year'] == selected_year]
            display_ipo = filtered_ipo[['stock_symbol', 'company_name', 'listing_date']]
            display_ipo.columns = ['Symbol', 'Company Name', 'Listing Date']
            display_ipo = display_ipo.sort_values(by='Listing Date', ascending=False)
            
            with col_y2: st.metric(label=f"Total IPOs ({selected_year})", value=len(display_ipo))
            st.dataframe(display_ipo, use_container_width=True, hide_index=True, height=400)
            
            if not display_ipo.empty:
                tv_ipo_text = ""
                for symbol in display_ipo['Symbol']: tv_ipo_text += f"NSE:{symbol}\n"
                col_i1, col_i2, col_i3 = st.columns([1, 2, 1])
                with col_i2: st.download_button(f"📥 Download {selected_year} IPO Watchlist (.txt)", data=tv_ipo_text, file_name=f"IPO_Watchlist_{selected_year}.txt", mime="text/plain", use_container_width=True)
    except Exception as e:
        st.error(f"Database Error: {e}")

# --- TAB 5: TRADING JOURNAL (PRO RISK MANAGEMENT) ---
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
                st.info("No active trades found. Pehle 'New Trade Entry' mein jakar trade add karein.")
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

# --- TAB 6: ERROR LOGS (Text Format) ---
with tab6:
    st.header("⚠️ System Error Logs")
    st.markdown("Yahan wo stocks dikhenge jinka data fetch ya calculate karne mein backend par error aayi thi.")
    
    col_clear, col_space = st.columns([1, 5])
    with col_clear:
        if st.button("🗑️ Clear All Logs", use_container_width=True):
            try:
                supabase.table('error_logs').delete().neq('id', 0).execute()
                st.success("Saare logs clear ho gaye!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error("Log delete karne mein error aayi.")

    try:
        log_res = supabase.table('error_logs').select("*").order('created_at', desc=True).limit(100).execute()
        
        if log_res.data:
            st.markdown("---")
            for log in log_res.data:
                sym = log.get('symbol', 'UNKNOWN')
                date_str = log.get('scan_date', 'Unknown Date')
                err_type = log.get('error_type', 'Error')
                reason = log.get('reason', 'No reason provided.')
                
                st.markdown(f"🚨 **SYMBOL: {sym}** `[{date_str}]`")
                st.markdown(f"**Error Type:** {err_type}")
                st.markdown(f"> *{reason}*")
                st.markdown("---")
        else:
            st.success("✅ Sab badhiya hai! Database me koi error logs nahi hain.")
            
    except Exception as e:
        st.error(f"Error fetching logs: {e}")

# --- 📝 GLOBAL TRADER'S SCRATCHPAD (At the very bottom of the page) ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.subheader("📝 Trader's Personal Scratchpad / Sticky Notes")
st.markdown("*Yahan aap jo bhi likhenge, wo hamesha safe rahega jab tak aap khud manually erase karke save nahi karte.*")

try:
    note_res = supabase.table('global_notes').select('note_text').eq('id', 1).execute()
    if note_res.data:
        saved_text = note_res.data[0]['note_text']
    else:
        saved_text = ""
except Exception as note_err:
    saved_text = ""
    st.error(f"Notes load karne mein dikkat aayi: {note_err}")

with st.form("global_scratchpad_form"):
    user_notes = st.text_area(
        label="Apne Daily Market Observations, Rules ya Watchlist yahan likhein:",
        value=saved_text,
        height=300,
        placeholder="Type your notes here..."
    )
    
    col_save_btn, col_empty = st.columns([1.5, 4])
    with col_save_btn:
        save_note_btn = st.form_submit_button("💾 Save My Notes", use_container_width=True)

    if save_note_btn:
        try:
            with st.spinner("Notes ko cloud par safe kar rahe hain..."):
                supabase.table('global_notes').upsert({"id": 1, "note_text": user_notes}).execute()
                st.toast("✅ Notes safely locked in Supabase!", icon="💾")
                time.sleep(0.5)
                st.rerun()
        except Exception as save_err:
            st.error(f"Notes save nahi ho paye: {save_err}")
