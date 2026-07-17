import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
from streamlit_cookies_manager import EncryptedCookieManager 

# --- Custom Modules Imports ---
import constants
import ui_styles
import backend
from views.home_view import show_home_page
from views.scanner_view import show_scanner_page
from views.results_view import show_results_page
from views.ipos_view import show_ipos_page
from views.journal_view import show_journal_page
from views.breadth_view import show_breadth_page

# ==========================================
# 1. PAGE CONFIGURATION & COOKIES
# ==========================================
# 'auto' ka matlab: Desktop par sidebar open rahega, Mobile par hamburger ban jayega
st.set_page_config(page_title="AlphaSwing Pro", layout="wide", page_icon="📈", initial_sidebar_state="auto")

cookies = EncryptedCookieManager(prefix="aswing", password=st.secrets.get("COOKIE_PASSWORD", "alphaswing_super_secret_key_2026"))
if not cookies.ready():
    st.stop()

if 'logged_in' not in st.session_state:
    if 'auth_role' in cookies:
        st.session_state.logged_in = True
        st.session_state.role = cookies['auth_role']
    else:
        st.session_state.logged_in = False
        st.session_state.role = None

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

# Active tab index for dynamic styling
active_index = constants.PAGES_LIST.index(st.session_state.current_page) + 2 if st.session_state.current_page in constants.PAGES_LIST else 2

# ==========================================
# 2. APPLY CSS & FETCH GLOBAL DATA
# ==========================================
st.markdown(ui_styles.get_custom_css(active_index), unsafe_allow_html=True)
supabase = backend.init_supabase()
raw_data = backend.fetch_swing_stocks()
raw_ipo_data = backend.fetch_ipo_data()
master_symbol_list = backend.get_master_symbol_list(raw_data)
is_admin = (st.session_state.role == 'admin')

# ==========================================
# 3. SECURE AUTHENTICATION
# ==========================================
if not st.session_state.logged_in and st.session_state.current_page != "Home":
    _, col_login_box, _ = st.columns([1, 1, 1])
    with col_login_box:
        st.markdown("<div class='login-container'><h1 style='color:#00e5ff; margin-bottom: 0px;'>AlphaSwing Pro</h1><p style='color:#94a3b8; margin-bottom: 30px;'>Secure Gateway</p></div>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")
            remember_me = st.checkbox("Keep me logged in")
            if st.form_submit_button("Access Dashboard", type="primary", use_container_width=True):
                if username == st.secrets.get("ADMIN_USERNAME", "ankitdahle") and password == st.secrets.get("ADMIN_PASSWORD", "dahleankit"):
                    st.session_state.logged_in = True; st.session_state.role = "admin"
                    if remember_me: cookies['auth_role'] = "admin"; cookies.save()
                    st.rerun()
                elif username == st.secrets.get("GUEST_USERNAME", "guest") and password == st.secrets.get("GUEST_PASSWORD", "viewonly"):
                    st.session_state.logged_in = True; st.session_state.role = "viewer"
                    if remember_me: cookies['auth_role'] = "viewer"; cookies.save()
                    st.rerun()
                else: st.error("❌ Invalid Credentials.")
    st.stop() 

# ==========================================
# 4. SIDEBAR NAVIGATION (Hamburger Menu)
# ==========================================
with st.sidebar:
    st.markdown("""<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 25px;">
    <div style="background-color: #00bfff; width: 30px; height: 30px; border-radius: 6px; display: flex; align-items: center; justify-content: center;">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L22 20H2L12 2Z" fill="white"/></svg></div>
    <h2 style="margin:0; font-size: 22px; font-weight: 800; color: white;">AlphaSwing</h2></div>""", unsafe_allow_html=True)

    for page_name in constants.PAGES_LIST:
        # Highlight active page with an arrow 👉
        btn_label = f"👉 {page_name}" if st.session_state.current_page == page_name else page_name
        if st.button(btn_label, use_container_width=True): 
            st.session_state.current_page = page_name
            st.rerun()

    st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    
    if st.session_state.logged_in:
        if st.button("Logout 🚪", type="primary", use_container_width=True):
            st.session_state.logged_in = False; st.session_state.role = None; st.session_state.current_page = "Home"
            if 'auth_role' in cookies: del cookies['auth_role']; cookies.save()
            st.rerun()
    else:
        if st.button("Login 🔐", type="primary", use_container_width=True): 
            st.session_state.current_page = "Scanner"; st.rerun()

# 📈 LIVE MARKET TICKER
if st.session_state.current_page in ["Home", "Scanner", "Fresh", "Results"]:
    ticker_html = """
    <div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
      { "symbols": [{ "proName": "NSE:NIFTY", "title": "NIFTY 50" }, { "proName": "NSE:BANKNIFTY", "title": "BANK NIFTY" }, { "proName": "NSE:CNXMIDCAP", "title": "MIDCAP 100" }, { "proName": "NSE:CNXSMALLCAP", "title": "SMALLCAP 100" }], "showSymbolLogo": true, "isTransparent": true, "displayMode": "adaptive", "colorTheme": "dark", "locale": "in" }
      </script>
    </div>
    """
    components.html(ticker_html, height=50)

# ==========================================
# 5. PAGE ROUTING (The Magic)
# ==========================================
if st.session_state.current_page == "Home":
    show_home_page()
elif st.session_state.current_page == "Scanner":
    show_scanner_page(raw_data, is_admin)
elif st.session_state.current_page == "Results":
    show_results_page(supabase)
elif st.session_state.current_page == "IPOs":
    show_ipos_page(raw_ipo_data)
elif st.session_state.current_page == "Breadth":
    show_breadth_page(supabase)
elif st.session_state.current_page == "Journal":
    show_journal_page(supabase, is_admin)
    
# --- Smaller Inline Views ---
elif st.session_state.current_page == "Fresh":
    st.markdown("<div class='page-heading'>🆕 Fresh Breakouts</div>", unsafe_allow_html=True)
    if raw_data:
        df = pd.DataFrame(raw_data)
        if 'scan_date' in df.columns:
            all_dates = sorted(df['scan_date'].unique(), reverse=True)
            if len(all_dates) >= 2:
                available_dates = all_dates[:7]
                col1, col2, col3 = st.columns([1.5, 1.5, 2])
                with col1: base_date = st.selectbox("📅 Base Date (Target):", available_dates, index=0)
                with col2:
                    default_compare_index = available_dates.index(base_date) + 1 if available_dates.index(base_date) + 1 < len(available_dates) else 0
                    compare_date = st.selectbox("🗓️ Compare Date (Past):", available_dates, index=default_compare_index)
                
                if base_date != compare_date:
                    base_stocks = set(df[df['scan_date'] == base_date]['stock_symbol'].unique())
                    compare_stocks = set(df[df['scan_date'] == compare_date]['stock_symbol'].unique())
                    new_stocks = base_stocks - compare_stocks
                    
                    st.markdown(f"""<div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 15px; border-radius: 4px; margin-top: 10px; margin-bottom: 25px;"><h3 style="color: #10b981; margin: 0px;">🚀 {len(new_stocks)} New Stocks Found!</h3><p style="color: #e2e8f0; margin: 5px 0px 0px 0px; font-size: 15px;">Total <b>{len(base_stocks)}</b> stocks from {base_date} vs <b>{len(compare_stocks)}</b> stocks from {compare_date}.</p></div>""", unsafe_allow_html=True)
                    if new_stocks:
                        new_df = pd.DataFrame({'Stock Symbol': sorted(list(new_stocks))})
                        new_df['TV Chart'] = "https://in.tradingview.com/chart/?symbol=NSE:" + new_df['Stock Symbol']
                        st.markdown(ui_styles.render_html_table(new_df, max_height="400px"), unsafe_allow_html=True)
                    else: st.info("Koi naya stock nahi aaya.")
                else: st.error("⚠️ Dono dates same hain!")

elif st.session_state.current_page == "Catalyst":
    st.markdown("<div class='page-heading'>🔥 Catalyst Prompt Generator</div>", unsafe_allow_html=True)
    user_ticker = st.selectbox("🔤 Search Ticker Symbol:", master_symbol_list, index=None, placeholder="Type symbol...")
    if user_ticker:
        prompt = f"Please analyze {user_ticker} for me and provide the following concisely:\n1. Explain what the company does like I'm 12.\n2. Professional summary (moat, unique product).\n3. Table of catalysts/themes.\n4. Recent news last 3 months.\n5. Institutional filings.\n6. Peer comparison."
        st.code(prompt, language="text")
        escaped_prompt = json.dumps(prompt)
        components.html(f"""<button id="btn" style="background-color: #00e5ff; color: #000; border: none; padding: 10px; border-radius: 6px; font-weight: 800; cursor: pointer; width: 100%;">📋 Copy Prompt</button><script>document.getElementById('btn').addEventListener('click', function() {{ navigator.clipboard.writeText({escaped_prompt}); this.innerText='✅ Copied!'; }});</script>""", height=50)

elif st.session_state.current_page == "Calculator":
    st.markdown("<div class='page-heading'>🧮 Risk & Position Sizing</div>", unsafe_allow_html=True)
    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
    with col_c2:
        st.markdown("<div style='background: rgba(0,0,0,0.4); padding: 30px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            calc_cap = st.number_input("Total Capital (₹)", value=100000, step=10000)
            calc_risk = st.number_input("Risk Per Trade (%)", value=1.0, step=0.5)
        with r_col2:
            calc_entry = st.number_input("Entry Price (₹)", value=0.0, step=1.0)
            calc_sl = st.number_input("Stoploss Price (₹)", value=0.0, step=1.0)
        
        if calc_entry > 0 and calc_sl > 0 and calc_entry > calc_sl:
            risk_per_share = calc_entry - calc_sl
            total_risk = calc_cap * (calc_risk / 100)
            qty = int(total_risk / risk_per_share)
            st.markdown(f"""<div style='background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; padding: 20px; border-radius: 10px; margin-top: 20px; text-align: center;'><h2 style='color: #10b981; margin-top: 0px;'>🎯 Target Qty: {qty} Shares</h2><p style='color: #e2e8f0;'>💸 <b>Max Loss:</b> ₹{int(total_risk)}</p></div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 6. GLOBAL STICKY NOTES
# ==========================================
if st.session_state.current_page != "Home":
    st.markdown("<br><br>### 📝 Sticky Notes", unsafe_allow_html=True)
    try: saved_text = supabase.table('global_notes').select('note_text').eq('id', 1).execute().data[0]['note_text']
    except: saved_text = ""
    with st.form("global_scratchpad_form"):
        user_notes = st.text_area(" ", value=saved_text, height=150, label_visibility="collapsed", disabled=not is_admin)
        if is_admin and st.form_submit_button("💾 Save Notes"):
            supabase.table('global_notes').upsert({"id": 1, "note_text": user_notes}).execute(); st.rerun()
