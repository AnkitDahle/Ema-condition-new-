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

# 1. Page Configuration (Sidebar collapsed for full-width view)
st.set_page_config(page_title="AlphaSwing Pro", layout="wide", page_icon="📈", initial_sidebar_state="collapsed")

# Initialize Session State for Navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

# --- 🎨 UI ENGINE: ANIMATED BG (LOCKED) + EXACT IMAGE NAVBAR STYLES ---
custom_css = """
<style>
    /* Global Font Size Increase */
    html, body, [class*="css"] {
        font-size: 1.05rem !important;
    }

    /* 🔒 LOCKED: Animated Premium Gradient Background (DO NOT TOUCH) */
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

    /* Hide standard header */
    header {visibility: hidden;}

    /* 🌟 BASE NAVBAR STYLING (INACTIVE TABS) */
    button[kind="secondary"] {
        background: transparent !important;
        border: none !important;
        color: #7b8fa3 !important; /* Muted blue-grey color just like 'Atlas' or 'Charts' */
        box-shadow: none !important;
        font-weight: 500 !important; /* Normal font weight for inactive */
        font-size: 19px !important;  
        letter-spacing: 0.5px !important;
        transition: color 0.2s ease;
    }
    button[kind="secondary"]:hover {
        color: #cdd6e0 !important; /* Slight glow on hover */
        background: transparent !important;
    }

    /* Action Button (Cyan 'Get Started' Style) */
    button[kind="primary"] {
        background-color: #00e5ff !important;
        color: #000000 !important;
        border-radius: 6px !important;
        font-weight: 900 !important;
        border: none !important;
        padding: 6px 24px !important;
        box-shadow: none !important;
    }
    button[kind="primary"]:hover {
        background-color: #00bfff !important;
    }

    /* Smaller Run Scan Button */
    .btn-run-scan button {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: white !important;
        border-radius: 6px !important;
        padding: 4px 12px !important;
        font-size: 14px !important;
    }

    /* Metric Adjustments */
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

    /* Journal & Notes Cards */
    .journal-card { 
        background: rgba(0,0,0,0.2); 
        border: 1px solid rgba(255,255,255,0.05); 
        padding: 20px; 
        border-radius: 12px; 
        margin-bottom: 20px; 
        backdrop-filter: blur(5px);
    }
    .stTextArea textarea {
        background-color: rgba(0,0,0,0.2) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
    }
    
    /* Page Headings Styling */
    .page-heading {
        font-size: 28px;
        font-weight: 800;
        color: #ffffff;
        margin-top: -10px;
        margin-bottom: 20px;
        border-bottom: 2px solid rgba(255,255,255,0.1);
        padding-bottom: 10px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 2. 🌟 TOP NAVIGATION BAR
col_logo, nav1, nav2, nav3, nav4, nav5, space, col_login = st.columns([3, 1, 1, 1, 1, 1, 0.5, 1.5])

with col_logo:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-top: 2px;">
        <div style="background-color: #00bfff; width: 30px; height: 30px; border-radius: 6px; display: flex; align-items: center; justify-content: center;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L22 20H2L12 2Z" fill="white"/>
            </svg>
        </div>
        <a href="/" target="_self" style="font-size: 22px; font-weight: 800; color: white; letter-spacing: 0.5px; text-decoration: none;">AlphaSwing</a>
    </div>
    """, unsafe_allow_html=True)

# 🌟 NEW: EXACT HIGHLIGHT FOR ACTIVE PAGE (LIKE "SCREENS" IN YOUR IMAGE)
pages = ['Home', 'Scanner', 'Catalyst', 'IPOs', 'Journal']
active_index = pages.index(st.session_state.current_page) + 2 # +2 because Logo is col 1
st.markdown(f"""
    <style>
    /* 🔥 ACTIVE TAB: Pure White and Extra Bold 🔥 */
    div[data-testid="column"]:nth-child({active_index}) button {{
        color: #ffffff !important;
        font-weight: 800 !important;
        background: transparent !important; /* No box background */
    }}
    </style>
""", unsafe_allow_html=True)

with nav1:
    if st.button("Home", use_container_width=True): st.session_state.current_page = "Home"; st.rerun()
with nav2:
    if st.button("Scanner", use_container_width=True): st.session_state.current_page = "Scanner"; st.rerun()
with nav3:
    if st.button("Catalyst", use_container_width=True): st.session_state.current_page = "Catalyst"; st.rerun()
with nav4:
    if st.button("IPOs", use_container_width=True): st.session_state.current_page = "IPOs"; st.rerun()
with nav5:
    if st.button("Journal", use_container_width=True): st.session_state.current_page = "Journal"; st.rerun()
with col_login:
    st.button("Get Started", type="primary", use_container_width=True)

st.markdown("<hr style='margin-top: 5px; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)

# 3. Databases & Global Data Fetch
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()
cloudinary.config(cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"], api_key=st.secrets["CLOUDINARY_API_KEY"], api_secret=st.secrets["CLOUDINARY_API_SECRET"])

try:
    response = supabase.table('swing_stocks').select("*").order('scan_date', desc=True).execute()
    raw_data = response.data
except Exception as e:
    raw_data = None

try:
    ipo_res = supabase.table('ipo_master').select("*").execute()
    raw_ipo_data = ipo_res.data
except Exception as e:
    raw_ipo_data = None

master_symbol_list = ["RELIANCE", "TCS", "INFY", "ZOMATO", "SBIN"]
if raw_data: master_symbol_list.extend([str(x).upper() for x in pd.DataFrame(raw_data)['stock_symbol'].dropna().unique()])
if raw_ipo_data: master_symbol_list.extend([str(x).upper() for x in pd.DataFrame(raw_ipo_data)['stock_symbol'].dropna().unique()])
master_symbol_list = sorted(list(set(master_symbol_list)))


# ==========================================
# 🏠 PAGE ROUTING CONTENT
# ==========================================

if st.session_state.current_page == "Home":
    components.html(
        """
        <script src="https://cdn.jsdelivr.net/npm/typed.js@2.0.12"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@700&display=swap');
            body { font-family: 'Inter', sans-serif; text-align: center; background-color: transparent; margin: 0; padding-top: 100px; color: #f8fafc; }
            .main-text { font-size: 50px; font-weight: 800; letter-spacing: -1px; }
            .highlight { color: #00e5ff; text-shadow: 0 0 20px rgba(0, 229, 255, 0.5);}
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
        height=300,
    )

elif st.session_state.current_page == "Scanner":
    st.markdown("<div class='page-heading'>📊 Scanner</div>", unsafe_allow_html=True)
    
    col_run, col_empty = st.columns([1.2, 6])
    with col_run:
        st.markdown("<div class='btn-run-scan'>", unsafe_allow_html=True)
        if st.button("🚀 Run Scan", use_container_width=True):
            with st.spinner("Scanning..."):
                try:
                    token = st.secrets["GITHUB_TOKEN"]
                    repo = st.secrets["GITHUB_REPO"]
                    requests.post(f"https://api.github.com/repos/{repo}/actions/workflows/daily_scan.yml/dispatches", headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}, json={"ref": "main"})
                    time.sleep(2)
                    st.success("✅ Initiated!")
                except Exception as e: st.error(f"❌ Error: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    if raw_data:
        df = pd.DataFrame(raw_data)
        cols_to_keep = ['scan_date', 'stock_symbol', 'close_price', 'turnover_cr', 'sector', 'industry_proxy']
        df = df[[c for c in cols_to_keep if c in df.columns]]
        df.rename(columns={'scan_date': 'Scan Date', 'stock_symbol': 'Stock Symbol', 'close_price': 'Close Price (₹)', 'turnover_cr': 'Turnover (Cr)', 'sector': 'Sector', 'industry_proxy': 'Proxy / Industry'}, inplace=True)
        df = df.drop_duplicates(subset=['Scan Date', 'Stock Symbol'], keep='first')
        
        latest_date = df['Scan Date'].max()
        total_stocks = len(df[df['Scan Date'] == latest_date])
        
        m1, m2, m3 = st.columns([1, 1, 3])
        with m1: st.metric("📅 Last Scan Date", str(latest_date))
        with m2: st.metric("🎯 Breakout Count", f"{total_stocks}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        f_col1, f_col2, f_col3, f_col4 = st.columns([1.5, 1.5, 1.5, 1.2])
        with f_col1: selected_date = st.selectbox("📅 Scan Date", sorted(df['Scan Date'].unique(), reverse=True))
        df_filtered = df[df['Scan Date'] == selected_date]
        
        with f_col2: selected_sector = st.selectbox("🎯 Sector", ["All Sectors"] + list(df['Sector'].dropna().unique()) if 'Sector' in df.columns else ["All Sectors"])
        with f_col3: selected_stock = st.selectbox("🔤 Search Stock", ["All Stocks"] + sorted(list(df_filtered['Stock Symbol'].dropna().unique())))

        if selected_sector != "All Sectors": df_filtered = df_filtered[df_filtered['Sector'] == selected_sector]
        if selected_stock != "All Stocks": df_filtered = df_filtered[df_filtered['Stock Symbol'] == selected_stock]

        tv_text = ""
        if not df_filtered.empty:
            for (sec, proxy), group in df_filtered.sort_values(by=['Sector', 'Proxy / Industry']).groupby(['Sector', 'Proxy / Industry']):
                tv_text += f"### {sec} / {proxy}\n"
                for sym in group['Stock Symbol']: tv_text += f"NSE:{sym}\n"
        
        with f_col4:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            st.download_button("📥 Watchlist (.txt)", data=tv_text, file_name=f"AlphaSwing_{selected_date}.txt", mime="text/plain", use_container_width=True)

        st.dataframe(df_filtered, use_container_width=True, height=400, hide_index=True)
        
        with st.expander("⚙️ View Active Scanner Rules"):
            st.write("• 1-Month, 3-Month & 52-Week High Breakouts. | • Heavy volume bursts (Turnover > 10Cr). | • Uptrend (Price sustained above key EMAs).")

elif st.session_state.current_page == "Catalyst":
    st.markdown("<div class='page-heading'>🔥 Catalyst</div>", unsafe_allow_html=True)
    
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
        <button id="copyPromptBtn" style="background-color: #00e5ff; color: #000000; border: none; padding: 10px 20px; border-radius: 6px; font-weight: 800; cursor: pointer; width: 100%; font-family: sans-serif;">📋 Copy Full Prompt</button>
        <script>
        document.getElementById('copyPromptBtn').addEventListener('click', function() {{
            navigator.clipboard.writeText({escaped_prompt_json}).then(function() {{
                const btn = document.getElementById('copyPromptBtn');
                btn.style.backgroundColor = '#10b981'; btn.style.color = 'white';
                btn.innerText = '✅ Prompt Copied!';
                setTimeout(() => {{
                    btn.style.backgroundColor = '#00e5ff'; btn.style.color = '#000000';
                    btn.innerText = '📋 Copy Full Prompt';
                }}, 2000);
            }});
        }});
        </script>
    """, height=50)

elif st.session_state.current_page == "IPOs":
    st.markdown("<div class='page-heading'>🏢 IPOs</div>", unsafe_allow_html=True)
    
    if raw_ipo_data:
        df_ipo = pd.DataFrame(raw_ipo_data)
        if 'listing_date' in df_ipo.columns:
            df_ipo['calc_date'] = pd.to_datetime(df_ipo['listing_date'], errors='coerce')
            df_ipo['Month'] = df_ipo['calc_date'].dt.strftime('%B')
            today = pd.to_datetime('today').date()
            
            m1, m2, m3 = st.columns([1, 1, 3])
            with m1: st.metric("Today Listed", len(df_ipo[df_ipo['calc_date'].dt.date == today]))
            with m2: st.metric("This Month", len(df_ipo[(df_ipo['calc_date'].dt.month == today.month) & (df_ipo['calc_date'].dt.year == today.year)]))
            st.markdown("<br>", unsafe_allow_html=True)

        col_y1, col_m1, col_search, col_dl = st.columns([1.2, 1.2, 1.5, 1.2])
        with col_y1: selected_year = st.selectbox("📅 IPO Year:", sorted(df_ipo['listing_year'].dropna().unique(), reverse=True))
        with col_m1: selected_month = st.selectbox("🗓️ Month:", ["All Months", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
        
        fil = df_ipo[df_ipo['listing_year'] == selected_year]
        if selected_month != "All Months": fil = fil[fil['Month'] == selected_month]
        
        with col_search: selected_ipo_stock = st.selectbox("🔤 Search IPO:", ["All IPOs"] + sorted(list(fil['stock_symbol'].dropna().unique())))
        if selected_ipo_stock != "All IPOs": fil = fil[fil['stock_symbol'] == selected_ipo_stock]
        
        display_ipo = fil[['stock_symbol', 'company_name', 'listing_date']].sort_values(by='listing_date', ascending=False)
        display_ipo.columns = ['Symbol', 'Company Name', 'Listing Date']
        
        tv_ipo_text = ""
        for sym in display_ipo['Symbol']: tv_ipo_text += f"NSE:{sym}\n"
        
        with col_dl:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            st.download_button("📥 Watchlist (.txt)", data=tv_ipo_text, file_name=f"IPO_{selected_year}.txt", mime="text/plain", use_container_width=True)
            
        st.dataframe(display_ipo, use_container_width=True, hide_index=True, height=400)

elif st.session_state.current_page == "Journal":
    st.markdown("<div class='page-heading'>📓 Journal</div>", unsafe_allow_html=True)
    
    j_tab1, j_tab2, j_tab3 = st.tabs(["➕ New Trade Entry", "🔄 Update Exits", "📚 Journal Gallery"])
    
    with j_tab1:
        with st.form("new_trade_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                symbol = st.text_input("Stock Symbol").upper()
                quantity = st.number_input("Total Quantity", min_value=1, step=1)
            with c2:
                buying_date = st.date_input("Buying Date", datetime.date.today())
                buying_price = st.number_input("Buying Price (₹)", min_value=0.0, step=0.1, format="%.2f")
            with c3:
                initial_sl = st.number_input("Initial Stoploss (₹)", min_value=0.0, step=0.1, format="%.2f")
            
            trade_logic = st.text_area("Trade Logic")
            image_file = st.file_uploader("Upload Chart (Optional)", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("💾 Save Trade", use_container_width=True) and symbol and quantity > 0 and buying_price > 0:
                with st.spinner("Saving trade..."):
                    img_url = None
                    if image_file is not None:
                        img_url = cloudinary.uploader.upload(image_file, folder="trading_journal").get("secure_url")
                    
                    try:
                        supabase.table('trading_journal').insert({"symbol": symbol, "total_quantity": quantity, "buying_date": str(buying_date), "buying_price": float(buying_price), "initial_sl": float(initial_sl), "trade_logic": trade_logic, "image_url": img_url}).execute()
                        st.success(f"✅ Trade {symbol} saved successfully!")
                    except Exception as e: st.error(f"Error: {e}")

    with j_tab2:
        try:
            active_res = supabase.table('trading_journal').select("*").is_("sold_30_date", "null").execute()
            active_trades = active_res.data
            if active_trades:
                trade_options = {f"{t['symbol']} (Bought: {t['buying_date']} @ ₹{t['buying_price']})": t for t in active_trades}
                selected_trade_label = st.selectbox("🎯 Select Active Trade", list(trade_options.keys()))
                t = trade_options[selected_trade_label]
                
                with st.form("update_trade_form"):
                    st.markdown("### 1️⃣ 20% Qty Booking")
                    c1, c2, c3 = st.columns(3)
                    with c1: s20_date = st.date_input("20% Sold Date", value=None)
                    with c2: s20_price = st.number_input("20% Sold Price", value=float(t['sold_20_price'] or 0.0))
                    with c3: sl_20 = st.number_input("New SL (0 for BE)", value=float(t['sl_after_20'] or 0.0))
                        
                    st.markdown("### 2️⃣ 50% Qty Booking")
                    c4, c5, c6 = st.columns(3)
                    with c4: s50_date = st.date_input("50% Sold Date", value=None)
                    with c5: s50_price = st.number_input("50% Sold Price", value=float(t['sold_50_price'] or 0.0))
                    with c6: sl_50 = st.number_input("New TSL", value=float(t['sl_after_50'] or 0.0))
                    
                    st.markdown("### 3️⃣ Final 30% Booking")
                    c7, c8 = st.columns(2)
                    with c7: s30_date = st.date_input("30% Sold Date", value=None)
                    with c8: s30_price = st.number_input("30% Sold Price", value=float(t['sold_30_price'] or 0.0))

                    if st.form_submit_button("🔄 Update Exits"):
                        supabase.table('trading_journal').update({
                            "sold_20_date": str(s20_date) if s20_price > 0 else None, "sold_20_price": s20_price if s20_price > 0 else None, "sl_after_20": float(t['buying_price']) if (s20_price > 0 and sl_20 == 0) else sl_20,
                            "sold_50_date": str(s50_date) if s50_price > 0 else None, "sold_50_price": s50_price if s50_price > 0 else None, "sl_after_50": sl_50 if sl_50 > 0 else None,
                            "sold_30_date": str(s30_date) if s30_price > 0 else None, "sold_30_price": s30_price if s30_price > 0 else None,
                        }).eq('id', t['id']).execute()
                        st.success("Trade updated!")
                        time.sleep(1); st.rerun()
            else:
                st.info("No active trades found.")
        except Exception as e: pass

    with j_tab3:
        all_trades = supabase.table('trading_journal').select("*").order('buying_date', desc=True).execute().data
        if all_trades:
            for tr in all_trades:
                st.markdown("<div class='journal-card'>", unsafe_allow_html=True)
                g1, g2 = st.columns([1, 2])
                with g1:
                    if tr.get('image_url'): st.image(tr['image_url'], use_container_width=True)
                    else: st.info("No chart")
                with g2:
                    st.subheader(f"🚀 {tr['symbol']}")
                    st.write(f"**Date:** {tr['buying_date']} | **Buy Price:** ₹{tr['buying_price']} | **Qty:** {tr['total_quantity']}")
                    st.write(f"**Logic:** {tr['trade_logic']}")
                    if tr.get('sold_20_price'): st.success(f"**20% Booked @ ₹{tr['sold_20_price']}**")
                    if tr.get('sold_50_price'): st.success(f"**50% Booked @ ₹{tr['sold_50_price']}**")
                    if tr.get('sold_30_price'): st.success(f"**30% Final Booked @ ₹{tr['sold_30_price']}**")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Journal is empty.")
            
    with st.expander("⚠️ System Error Logs"):
        if st.button("Clear Logs"): st.success("Cleared!")

# ==========================================
# 📝 GLOBAL NOTES (Always visible at bottom)
# ==========================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("### Notes")

try:
    saved_text = supabase.table('global_notes').select('note_text').eq('id', 1).execute().data[0]['note_text']
except: saved_text = ""

with st.form("global_scratchpad_form"):
    user_notes = st.text_area(" ", value=saved_text, height=200, label_visibility="collapsed")
    col_save, col_spacer = st.columns([1, 5])
    with col_save:
        if st.form_submit_button("💾 Save Notes", use_container_width=True):
            supabase.table('global_notes').upsert({"id": 1, "note_text": user_notes}).execute()
            st.toast("✅ Saved!"); time.sleep(0.5); st.rerun()
