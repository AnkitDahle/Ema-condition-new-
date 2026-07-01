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
import plotly.express as px  
from streamlit_cookies_manager import EncryptedCookieManager 

# ==========================================
# 1. PAGE CONFIGURATION 
# ==========================================
st.set_page_config(page_title="AlphaSwing Pro", layout="wide", page_icon="📈", initial_sidebar_state="collapsed")

# ==========================================
# 🚀 2. COOKIE MANAGER & HTML TABLE ENGINE
# ==========================================
cookie_password = st.secrets.get("COOKIE_PASSWORD", "alphaswing_super_secret_key_2026")
cookies = EncryptedCookieManager(prefix="aswing", password=cookie_password)

if not cookies.ready():
    st.stop()

if 'active_sector_ui' not in st.session_state:
    st.session_state.active_sector_ui = None
if 'logged_in' not in st.session_state:
    if 'auth_role' in cookies:
        st.session_state.logged_in = True
        st.session_state.role = cookies['auth_role']
    else:
        st.session_state.logged_in = False
        st.session_state.role = None

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

# 🟢 UPDATE: Calculator is now an official page
pages = ['Home', 'Scanner', 'Catalyst', 'IPOs', 'Journal', 'Calculator']
active_index = pages.index(st.session_state.current_page) + 2 

# 🔥 SCROLLABLE HTML TABLE ENGINE
def render_html_table(df, max_height="350px"):
    html = f"<div style='overflow-x:auto; overflow-y:auto; max-height: {max_height}; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;'>"
    html += "<table style='width:100%; text-align:left; border-collapse: collapse; font-size: 14px;'>"
    html += "<thead><tr>"
    for col in df.columns:
        html += f"<th style='position: sticky; top: 0; background: #18181b; padding: 12px; color:#00e5ff; border-bottom: 1px solid rgba(255,255,255,0.1); white-space: nowrap; z-index: 1;'>{col}</th>"
    html += "</tr></thead><tbody>"
    for i, row in df.iterrows():
        bg = "background: rgba(0,0,0,0.2);" if i%2==0 else "background: rgba(255,255,255,0.02);"
        html += f"<tr style='{bg} border-bottom: 1px solid rgba(255,255,255,0.05);'>"
        for col in df.columns:
            val = row[col]
            if str(val).startswith("http"):
                html += f"<td style='padding: 10px;'><a href='{val}' target='_blank' style='background: #10b981; color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 12px; display: inline-block; white-space: nowrap;'>📈 Open Chart</a></td>"
            else:
                html += f"<td style='padding: 10px; color: #e2e8f0; white-space: nowrap;'>{val}</td>"
        html += "</tr>"
    html += "</tbody></table></div>"
    return html

# ==========================================
# 3. 🎨 UI ENGINE & CUSTOM CSS
# ==========================================
custom_css = f"""
<style>
    html, body, [class*="css"] {{ font-size: 1.05rem !important; }}
    .stApp {{
        background: linear-gradient(-45deg, #09090b, #18181b, #0f172a, #171717);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        color: #f8fafc;
    }}
    @keyframes gradientBG {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} 100% {{ background-position: 0% 50%; }} }}
    .block-container {{ padding-top: 1rem !important; }}
    header {{ visibility: hidden; }}

    .stButton > button[kind="secondary"], .stDownloadButton > button {{
        background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important; padding: 6px 12px !important; transition: all 0.2s ease !important;
        color: #e2e8f0 !important; font-weight: 500 !important; 
    }}
    .stButton > button[kind="secondary"]:hover, .stDownloadButton > button:hover {{
        border-color: #00e5ff !important; background: rgba(255, 255, 255, 0.1) !important; color: #ffffff !important;
    }}
    
    div[data-testid="stHorizontalBlock"]:first-of-type .stButton > button {{
        background: transparent !important; border: none !important; box-shadow: none !important;
    }}
    div[data-testid="stHorizontalBlock"]:first-of-type .stButton > button p {{
        color: #7b8fa3 !important; font-weight: 500 !important; font-size: 19px !important; letter-spacing: 0.5px;
        white-space: nowrap !important;
    }}
    div[data-testid="stHorizontalBlock"]:first-of-type .stButton > button:hover p {{ color: #cdd6e0 !important; }}
    div[data-testid="stHorizontalBlock"]:first-of-type div[data-testid="stColumn"]:nth-child({active_index}) .stButton > button p {{
        color: #ffffff !important; font-weight: 900 !important;    
    }}
    div[data-testid="stHorizontalBlock"]:first-of-type button[kind="primary"] {{
        background-color: #00e5ff !important; border-radius: 6px !important; border: none !important; white-space: nowrap !important;
    }}
    div[data-testid="stHorizontalBlock"]:first-of-type button[kind="primary"] p {{ color: #000000 !important; font-weight: 900 !important;}}

    @media (max-width: 768px) {{
        div[data-testid="stHorizontalBlock"]:first-of-type {{
            display: flex !important; flex-wrap: nowrap !important; overflow-x: auto !important; padding-bottom: 5px !important; 
        }}
        div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="stColumn"] {{
            min-width: max-content !important; flex: 0 0 auto !important; width: auto !important;
        }}
        div[data-testid="stHorizontalBlock"]:first-of-type::-webkit-scrollbar {{ display: none; }}
    }}

    div.stForm button[kind="primaryFormSubmit"] {{ background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important; border: none !important; border-radius: 8px !important; }}
    div.stForm button[kind="primaryFormSubmit"] p {{ font-weight: 700 !important; color: white !important; }}

    .page-heading {{ font-size: 28px; font-weight: 600; color: #ffffff; margin-top: -10px; margin-bottom: 20px; border-bottom: 2px solid rgba(255,255,255,0.1); padding-bottom: 10px; }}
    .journal-card {{ background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-bottom: 20px; backdrop-filter: blur(5px); }}
    .login-container {{ background: rgba(0,0,0,0.4); padding: 40px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(10px); max-width: 400px; margin: auto; margin-top: 5vh; text-align: center; }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# 🔐 4. SECURE AUTHENTICATION
# ==========================================
if not st.session_state.logged_in and st.session_state.current_page != "Home":
    _, col_login_box, _ = st.columns([1, 1, 1])
    with col_login_box:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("<h1 style='color:#00e5ff; margin-bottom: 0px;'>AlphaSwing Pro</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#94a3b8; margin-bottom: 30px;'>Secure Gateway</p>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")
            remember_me = st.checkbox("Keep me logged in (Remember me)")
            submit_btn = st.form_submit_button("Access Dashboard", type="primary", use_container_width=True)
            if submit_btn:
                if username == st.secrets.get("ADMIN_USERNAME", "ankitdahle") and password == st.secrets.get("ADMIN_PASSWORD", "dahleankit"):
                    st.session_state.logged_in = True; st.session_state.role = "admin"
                    if remember_me: cookies['auth_role'] = "admin"; cookies.save()
                    st.rerun()
                elif username == st.secrets.get("GUEST_USERNAME", "guest") and password == st.secrets.get("GUEST_PASSWORD", "viewonly"):
                    st.session_state.logged_in = True; st.session_state.role = "viewer"
                    if remember_me: cookies['auth_role'] = "viewer"; cookies.save()
                    st.rerun()
                else: st.error("❌ Invalid Credentials.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop() 

is_admin = (st.session_state.role == 'admin')

# ==========================================
# 5. TOP NAVIGATION BAR RENDERING (UPDATE)
# ==========================================
col_logo, nav1, nav2, nav3, nav4, nav5, nav6, space, col_login = st.columns([2.5, 1.1, 1.1, 1.1, 1.1, 1.1, 1.3, 0.2, 1.5])
with col_logo:
    st.markdown("""<div style="display: flex; align-items: center; gap: 10px; margin-top: 2px;"><div style="background-color: #00bfff; width: 30px; height: 30px; border-radius: 6px; display: flex; align-items: center; justify-content: center;"><svg width="14" height="14" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L22 20H2L12 2Z" fill="white"/></svg></div><a href="/" target="_self" style="font-size: 22px; font-weight: 800; color: white; text-decoration: none;">AlphaSwing</a></div>""", unsafe_allow_html=True)
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
with nav6:
    if st.button("Calculator", use_container_width=True): st.session_state.current_page = "Calculator"; st.rerun()
with col_login:
    if st.session_state.logged_in:
        if st.button("Logout 🚪", type="primary", use_container_width=True):
            st.session_state.logged_in = False; st.session_state.role = None; st.session_state.current_page = "Home"
            if 'auth_role' in cookies: del cookies['auth_role']; cookies.save()
            st.rerun()
    else:
        if st.button("Login 🔐", type="primary", use_container_width=True): st.session_state.current_page = "Scanner"; st.rerun()

st.markdown("<hr style='margin-top: 5px; margin-bottom: 0px; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)

# 📈 6. LIVE MARKET TICKER (FIXED SYMBOLS FOR INDIA)
if st.session_state.current_page in ["Home", "Scanner"]:
    ticker_html = """
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
      {
      "symbols": [
        { "proName": "BSE:NIFTY50", "title": "NIFTY 50" },
        { "proName": "BSE:NIFTYBANK", "title": "BANK NIFTY" },
        { "proName": "BSE:BSE_MIDCAP", "title": "MIDCAP" },
        { "proName": "BSE:BSE_SMLCAP", "title": "SMALLCAP" }
      ],
      "showSymbolLogo": true, "isTransparent": true, "displayMode": "adaptive", "colorTheme": "dark", "locale": "in"
    }
      </script>
    </div>
    """
    components.html(ticker_html, height=50)

# ==========================================
# 7. DATABASES & GLOBAL FETCH
# ==========================================
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()
try: raw_data = supabase.table('swing_stocks').select("*").order('scan_date', desc=True).execute().data
except: raw_data = None

try: raw_ipo_data = supabase.table('ipo_master').select("*").execute().data
except: raw_ipo_data = None

master_symbol_list = ["RELIANCE", "TCS", "INFY", "ZOMATO", "SBIN"]
if raw_data: master_symbol_list.extend([str(x).upper() for x in pd.DataFrame(raw_data)['stock_symbol'].dropna().unique()])
master_symbol_list = sorted(list(set(master_symbol_list)))

# ==========================================
# 8. MAIN ROUTING
# ==========================================
if st.session_state.current_page == "Home":
    components.html(
        """
        <script src="https://cdn.jsdelivr.net/npm/typed.js@2.0.12"></script>
        <style>
            body { font-family: 'Inter', sans-serif; text-align: center; background-color: transparent; margin: 0; padding-top: 80px; color: #f8fafc; }
            .main-text { font-size: 50px; font-weight: 800; letter-spacing: -1px; }
            .highlight { color: #00e5ff; text-shadow: 0 0 20px rgba(0, 229, 255, 0.5);}
        </style>
        <div class="main-text">AlphaSwing Pro: Best tool for <br><span id="typed" class="highlight"></span></div>
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
    role_badge = "👑 Admin" if is_admin else "👁️ Viewer"
    st.markdown(f"<div class='page-heading'>📊 Market Scanner <span style='font-size:14px; color:#94a3b8; float:right; padding-top:10px;'>{role_badge}</span></div>", unsafe_allow_html=True)
    
    if raw_data:
        df = pd.DataFrame(raw_data)
        cols_to_keep = ['scan_date', 'stock_symbol', 'close_price', 'turnover_cr', 'sector', 'industry_proxy']
        df = df[[c for c in cols_to_keep if c in df.columns]]
        df.rename(columns={'scan_date': 'Scan Date', 'stock_symbol': 'Stock Symbol', 'close_price': 'Close Price (₹)', 'turnover_cr': 'Turnover (Cr)', 'sector': 'Sector', 'industry_proxy': 'Proxy / Industry'}, inplace=True)
        df = df.drop_duplicates(subset=['Scan Date', 'Stock Symbol'], keep='first')
        
        f_col1, f_col2, f_col3, f_col_run, f_col_dl = st.columns([1.3, 1.3, 1.4, 1.0, 1.0])
        with f_col1: selected_date = st.selectbox("📅 Scan Date", sorted(df['Scan Date'].unique(), reverse=True))
        df_selected_date = df[df['Scan Date'] == selected_date]
        
        m1, m2, m3 = st.columns([1, 1, 3])
        with m1: st.metric("📅 Selected Scan Date", str(selected_date))
        with m2: st.metric("🎯 Total Breakouts", len(df_selected_date))
        st.markdown("<br>", unsafe_allow_html=True)

        with f_col2: selected_sector = st.selectbox("🎯 Main Filter", ["All Sectors"] + list(df_selected_date['Sector'].dropna().unique()) if 'Sector' in df_selected_date.columns else ["All Sectors"])
        with f_col3: selected_stock = st.selectbox("🔤 Search Stock", sorted(list(df_selected_date['Stock Symbol'].dropna().unique())), index=None, placeholder="Type symbol...")

        df_filtered = df_selected_date.copy()
        if selected_sector != "All Sectors": df_filtered = df_filtered[df_filtered['Sector'] == selected_sector]
        if selected_stock: df_filtered = df_filtered[df_filtered['Stock Symbol'] == selected_stock] 
        
        if 'Turnover (Cr)' in df_filtered.columns:
            df_filtered = df_filtered.sort_values(by='Turnover (Cr)', ascending=False)

        if is_admin:
            with f_col_run:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("🚀 Run Scan", use_container_width=True):
                    with st.spinner("Scanning..."):
                        requests.post(f"https://api.github.com/repos/{st.secrets['GITHUB_REPO']}/actions/workflows/daily_scan.yml/dispatches", headers={"Authorization": f"token {st.secrets['GITHUB_TOKEN']}", "Accept": "application/vnd.github.v3+json"}, json={"ref": "main"})
                        st.success("✅ Initiated!")

        with f_col_dl:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            tv_text = "".join([f"### {sec} / {proxy},\n" + "".join([f"NSE:{sym},\n" for sym in group['Stock Symbol']]) for (sec, proxy), group in df_filtered.groupby(['Sector', 'Proxy / Industry'])]) if not df_filtered.empty else ""
            st.download_button("📥 Watchlist (.txt)", data=tv_text, file_name=f"AlphaSwing_{selected_date}.txt", mime="text/plain", use_container_width=True)

        if not df_filtered.empty:
            display_df = df_filtered.copy()
            display_df['TV Chart'] = "https://in.tradingview.com/chart/?symbol=NSE:" + display_df['Stock Symbol']
            st.markdown(render_html_table(display_df, max_height="350px"), unsafe_allow_html=True)

        # 🔥 FIXED OVERLAPPING: Advanced Sector Explorer
        st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin-top: 30px;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #ffffff; margin-bottom: 20px;'>🍩 Advanced Sector Explorer</h3>", unsafe_allow_html=True)

        if not df_selected_date.empty:
            sector_counts = df_selected_date['Sector'].value_counts().reset_index()
            sector_counts.columns = ['Sector', 'Stock Count']
            sector_list = sorted(list(sector_counts['Sector']))
            total_sectors = sector_counts['Stock Count'].sum()
            sector_counts['Legend_Label'] = sector_counts.apply(lambda row: f"{row['Sector']} ({row['Stock Count']/total_sectors*100:.1f}%)", axis=1)
            
            fig_sector = px.pie(sector_counts, values='Stock Count', names='Legend_Label', hole=0.45, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_sector.update_traces(textposition='inside', textinfo='percent', hovertemplate="<b>%{label}</b><br>Stocks: %{value}<extra></extra>")
            # Pushed legend to the bottom and added margins
            fig_sector.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
                margin=dict(t=40, b=40, l=0, r=0), 
                legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
                title=dict(text="1️⃣ Overall Sector Distribution", font=dict(color="#00e5ff", size=16))
            )

            # Equal columns to prevent crunching
            c_chart1, c_chart2 = st.columns([1, 1])
            with c_chart1: st.plotly_chart(fig_sector, use_container_width=True)

            with c_chart2:
                st.markdown("<div style='margin-top: 10px;'></div><p style='color:#00e5ff; font-weight: 600;'>👇 Select Sector to Explore:</p>", unsafe_allow_html=True)
                active_sector = st.selectbox("Sector", sector_list, key="explorer_sec_box", label_visibility="collapsed")

                if active_sector:
                    sector_df = df_selected_date[df_selected_date['Sector'] == active_sector]
                    proxy_counts = sector_df['Proxy / Industry'].value_counts().reset_index()
                    proxy_counts.columns = ['Proxy', 'Stock Count']
                    total_proxies = proxy_counts['Stock Count'].sum()
                    proxy_counts['Legend_Label'] = proxy_counts.apply(lambda row: f"{row['Proxy']} ({row['Stock Count']/total_proxies*100:.1f}%)", axis=1)
                    
                    fig_proxy = px.pie(proxy_counts, values='Stock Count', names='Legend_Label', hole=0.45, color_discrete_sequence=px.colors.qualitative.Set3)
                    fig_proxy.update_traces(textposition='inside', textinfo='percent', hovertemplate="<b>%{label}</b><br>Stocks: %{value}<extra></extra>")
                    # Pushed legend to the bottom and added margins
                    fig_proxy.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
                        margin=dict(t=30, b=40, l=0, r=0), 
                        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
                        title=dict(text=f"2️⃣ Proxies in {active_sector}", font=dict(color="#10b981", size=16))
                    )
                    st.plotly_chart(fig_proxy, use_container_width=True)
                    
            if active_sector:
                st.markdown(f"<h4 style='color:#ffffff; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-top: 20px;'>📋 {active_sector} Breakout List</h4>", unsafe_allow_html=True)
                display_proxy_df = sector_df[['Proxy / Industry', 'Stock Symbol']].sort_values(by=['Proxy / Industry', 'Stock Symbol'])
                display_proxy_df.columns = ['Proxy Name', 'Stock Name'] 
                display_proxy_df['TV Chart'] = "https://in.tradingview.com/chart/?symbol=NSE:" + display_proxy_df['Stock Name']
                st.markdown(render_html_table(display_proxy_df, max_height="300px"), unsafe_allow_html=True)

elif st.session_state.current_page == "Calculator":
    st.markdown("<div class='page-heading'>🧮 Risk & Position Sizing Calculator</div>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; margin-bottom: 30px;'>Apne capital aur risk ke hisab se exact quantity calculate karein.</p>", unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
    with col_c2:
        st.markdown("<div style='background: rgba(0,0,0,0.4); padding: 30px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            calc_cap = st.number_input("Total Trading Capital (₹)", value=100000, step=10000)
            calc_risk = st.number_input("Risk Per Trade (%)", value=1.0, step=0.5)
        with r_col2:
            calc_entry = st.number_input("Entry Price (₹)", value=0.0, step=1.0)
            calc_sl = st.number_input("Stoploss Price (₹)", value=0.0, step=1.0)
        
        if calc_entry > 0 and calc_sl > 0:
            if calc_entry > calc_sl:
                risk_per_share = calc_entry - calc_sl
                total_risk = calc_cap * (calc_risk / 100)
                qty = int(total_risk / risk_per_share)
                
                st.markdown(f"""
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; padding: 20px; border-radius: 10px; margin-top: 20px; text-align: center;">
                    <h2 style="color: #10b981; margin-top: 0px; font-size: 28px;">🎯 Target Quantity: {qty} Shares</h2>
                    <p style="color: #e2e8f0; font-size: 16px; margin: 0px;">💸 <b>Maximum Allowed Loss:</b> ₹{int(total_risk)}</p>
                    <p style="color: #94a3b8; font-size: 14px; margin-top: 5px; margin-bottom: 0px;"><i>Total Position Size Required: ₹{int(qty * calc_entry):,}</i></p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("⚠️ Stoploss must be strictly lower than Entry Price for a Swing Trade!")
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.current_page == "Catalyst":
    st.markdown("<div class='page-heading'>🔥 Catalyst</div>", unsafe_allow_html=True)
    cat_col1, cat_col2 = st.columns([2, 5])
    with cat_col1: user_ticker = st.selectbox("🔤 Search Symbol:", master_symbol_list, index=None, placeholder="Type symbol...")
    if user_ticker:
        catalyst_prompt = f"Please analyze {user_ticker} for me and provide the following, concise and clearly organized... [PROMPT]"
        st.code(catalyst_prompt, language="text")

elif st.session_state.current_page == "IPOs":
    st.markdown("<div class='page-heading'>🏢 IPOs</div>", unsafe_allow_html=True)
    if raw_ipo_data:
        df_ipo = pd.DataFrame(raw_ipo_data)
        display_ipo = df_ipo[['stock_symbol', 'company_name', 'listing_date']].sort_values(by='listing_date', ascending=False)
        display_ipo.columns = ['Symbol', 'Company Name', 'Listing Date']
        display_ipo['TV Chart'] = "https://in.tradingview.com/chart/?symbol=NSE:" + display_ipo['Symbol']
        st.markdown(render_html_table(display_ipo, max_height="500px"), unsafe_allow_html=True)

elif st.session_state.current_page == "Journal":
    st.markdown("<div class='page-heading'>📓 Trading Journal</div>", unsafe_allow_html=True)
    
    try:
        all_trades = supabase.table('trading_journal').select("*").order('buying_date', desc=True).execute().data
    except Exception:
        all_trades = []
        
    if all_trades is None:
        all_trades = []
        
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("🎯 Total Trades Logged", len(all_trades))
    with m2: st.metric("⏳ Active Positions", len([t for t in all_trades if not t.get('sold_30_date')]))
    with m3: st.metric("✅ Closed Positions", len([t for t in all_trades if t.get('sold_30_date')]))
    st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin-bottom:20px;'>", unsafe_allow_html=True)
    
    if is_admin:
        j_tabs = st.tabs(["➕ New Trade", "🔄 Update Exits", "📚 Journal Gallery"])
        with j_tabs[0]:
            with st.form("new_trade_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                with c1: symbol = st.text_input("Stock Symbol").upper(); quantity = st.number_input("Quantity", min_value=1)
                with c2: buying_date = st.date_input("Date"); buying_price = st.number_input("Buy Price", min_value=0.0)
                with c3: initial_sl = st.number_input("Initial SL", min_value=0.0)
                trade_logic = st.text_area("Trade Logic"); image_file = st.file_uploader("Upload Chart", type=['png', 'jpg', 'jpeg'])
                if st.form_submit_button("💾 Save Trade") and symbol:
                    img_url = cloudinary.uploader.upload(image_file, folder="trading_journal").get("secure_url") if image_file else None
                    supabase.table('trading_journal').insert({"symbol": symbol, "total_quantity": quantity, "buying_date": str(buying_date), "buying_price": float(buying_price), "initial_sl": float(initial_sl), "trade_logic": trade_logic, "image_url": img_url}).execute()
                    st.success("Saved!"); time.sleep(1); st.rerun()
        
        with j_tabs[1]:
            active_trades_data = [t for t in all_trades if not t.get('sold_30_date')] if all_trades else []
            if active_trades_data:
                trade_options = {f"{t['symbol']} (Bought @ ₹{t['buying_price']})": t for t in active_trades_data}
                t = trade_options[st.selectbox("🎯 Select Active Trade", list(trade_options.keys()))]
                with st.form("update_trade_form"):
                    st.markdown("### 1️⃣ 20% Booking")
                    c1, c2, c3 = st.columns(3)
                    with c1: s20_date = st.date_input("Date", value=None)
                    with c2: s20_price = st.number_input("Price", value=float(t['sold_20_price'] or 0.0))
                    with c3: sl_20 = st.number_input("New SL", value=float(t['sl_after_20'] or 0.0))
                    if st.form_submit_button("🔄 Update Exits", type="primary"):
                        supabase.table('trading_journal').update({"sold_20_price": s20_price if s20_price>0 else None, "sl_after_20": sl_20}).eq('id', t['id']).execute()
                        st.success("Updated!"); time.sleep(1); st.rerun()
            else:
                st.info("No active trades found.")
    else:
        j_tabs = st.tabs(["📚 Journal Gallery"])

    with j_tabs[-1]: 
        if all_trades:
            for tr in all_trades:
                st.markdown("<div class='journal-card'>", unsafe_allow_html=True)
                g1, g2 = st.columns([1, 2])
                with g1:
                    if tr.get('image_url'): st.image(tr['image_url'], use_container_width=True)
                with g2:
                    st.subheader(f"🚀 {tr['symbol']}")
                    st.write(f"**Date:** {tr['buying_date']} | **Buy Price:** ₹{tr['buying_price']} | **Qty:** {tr['total_quantity']}")
                    st.write(f"**Logic:** {tr['trade_logic']}")
                    if tr.get('sold_20_price'): st.success(f"**20% Booked @ ₹{tr['sold_20_price']}**")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Journal is empty.")

# Sticky Notes
if st.session_state.current_page != "Home":
    st.markdown("<br><br>### 📝 Sticky Notes", unsafe_allow_html=True)
    try: saved_text = supabase.table('global_notes').select('note_text').eq('id', 1).execute().data[0]['note_text']
    except: saved_text = ""
    with st.form("global_scratchpad_form"):
        user_notes = st.text_area(" ", value=saved_text, height=150, label_visibility="collapsed", disabled=not is_admin)
        if is_admin and st.form_submit_button("💾 Save Notes"):
            supabase.table('global_notes').upsert({"id": 1, "note_text": user_notes}).execute(); st.rerun()
