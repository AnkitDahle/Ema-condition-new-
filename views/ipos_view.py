import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from ui_styles import render_html_table

def show_ipos_page(raw_ipo_data):
    st.markdown("<div class='page-heading'>🚀 Fresh IPO Radar (2020+)</div>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8;'>Track genuine newly listed companies, filter by timeline, and export them directly to your TradingView Watchlist.</p>", unsafe_allow_html=True)
    
    if not raw_ipo_data:
        st.info("⚠️ Database se koi IPO data fetch nahi hua. Backend script run hone ka wait karein.")
        return
        
    df = pd.DataFrame(raw_ipo_data)
    
    # Date ko properly format karna
    if 'listing_date' in df.columns:
        df['listing_date'] = pd.to_datetime(df['listing_date'], errors='coerce')
        df = df.dropna(subset=['listing_date'])
        df = df.sort_values(by='listing_date', ascending=False)
        
        # Filters ke liye Year aur Month nikalna
        df['Year'] = df['listing_date'].dt.year
        df['Month'] = df['listing_date'].dt.strftime('%B') # ex: 'January', 'August'
        df['Month_Num'] = df['listing_date'].dt.month # Internal sorting ke liye
        df['Formatted Date'] = df['listing_date'].dt.strftime('%d %b %Y')
    else:
        st.error("⚠️ 'listing_date' column missing from data.")
        return

    # ==========================================
    # 🌟 NEW: LIVE STATS SECTION (IST TIME)
    # ==========================================
    # Indian Standard Time (IST) set karna zaroori hai Cloud servers ke liye
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    current_date = ist_now.date()
    current_year = ist_now.year
    current_month_num = ist_now.month
    current_month_name = ist_now.strftime('%B')

    # Math Calculations
    ipos_today = len(df[df['listing_date'].dt.date == current_date])
    ipos_this_month = len(df[(df['Year'] == current_year) & (df['Month_Num'] == current_month_num)])
    ipos_this_year = len(df[df['Year'] == current_year])

    st.write("---")
    st.write("### 📊 Live IPO Statistics")
    # Streamlit ke native 'metric' cards banayenge
    c1, c2, c3 = st.columns(3)
    c1.metric(label=f"🔥 Listed Today ({current_date.strftime('%d %b')})", value=ipos_today)
    c2.metric(label=f"📅 Listed This Month ({current_month_name})", value=ipos_this_month)
    c3.metric(label=f"📈 Listed This Year ({current_year})", value=ipos_this_year)
    
    st.write("---")

    # ==========================================
    # 🔍 YEAR AND MONTH FILTERS
    # ==========================================
    st.write("### 🔍 Filter Watchlist")
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        # Years ki list banakar dropdown me dalna
        years = ["All"] + sorted([str(int(y)) for y in df['Year'].unique()], reverse=True)
        selected_year = st.selectbox("📅 Filter by Year:", years)
        
    with filter_col2:
        # Agar koi specific saal chuna hai, toh sirf usi saal ke mahine dikhao
        if selected_year != "All":
            available_months = df[df['Year'] == int(selected_year)].sort_values('Month_Num')['Month'].unique()
        else:
            available_months = df.sort_values('Month_Num')['Month'].unique()
            
        months = ["All"] + list(available_months)
        selected_month = st.selectbox("📆 Filter by Month:", months)

    # ------------------------------------------
    # ⚙️ APPLY FILTERS TO DATA
    # ------------------------------------------
    display_df = df.copy()
    
    if selected_year != "All":
        display_df = display_df[display_df['Year'] == int(selected_year)]
        
    if selected_month != "All":
        display_df = display_df[display_df['Month'] == selected_month]

    if display_df.empty:
        st.warning(f"🤷‍♂️ Bhai, {selected_month} {selected_year} me koi naya IPO list nahi hua tha.")
        return

    # ==========================================
    # 🖨️ PREPARE TABLE & DOWNLOAD
    # ==========================================
    display_df['TV Chart'] = "https://in.tradingview.com/chart/?symbol=NSE:" + display_df['stock_symbol']
    
    cols_to_show = ['stock_symbol', 'company_name', 'Formatted Date', 'TV Chart']
    final_df = display_df[cols_to_show].copy()
    
    # Table ke header names clean karna
    rename_map = {
        'stock_symbol': 'Symbol', 
        'company_name': 'Company Name', 
        'Formatted Date': 'Listing Date'
    }
    final_df.rename(columns=rename_map, inplace=True)
    
    st.write("---")
    dl_col1, dl_col2 = st.columns([4, 1])
    with dl_col1:
        st.write(f"Showing **{len(final_df)}** verified IPOs based on your filter.")
    with dl_col2:
        # Comma-separated list for TradingView
        tv_txt = ", ".join([f"NSE:{sym}" for sym in final_df['Symbol']])
        
        # Custom file name logic
        file_yr = selected_year if selected_year != "All" else "AllYears"
        file_mo = selected_month if selected_month != "All" else "AllMonths"
        
        st.download_button(
            label="📥 Watchlist (.txt)", 
            data=tv_txt, 
            file_name=f"IPOs_{file_mo}_{file_yr}.txt", 
            mime="text/plain", 
            use_container_width=True
        )
        
    # CSS Table render
    st.markdown(render_html_table(final_df, max_height="550px"), unsafe_allow_html=True)
