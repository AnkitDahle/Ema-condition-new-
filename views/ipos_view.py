import streamlit as st
import pandas as pd
from ui_styles import render_html_table

def show_ipos_page(raw_ipo_data):
    st.markdown("<div class='page-heading'>🚀 Fresh IPO Radar (2020+)</div>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8;'>Explore genuine newly listed companies and export them directly to your TradingView Watchlist.</p>", unsafe_allow_html=True)
    
    # 1. Check if Data Exists
    if not raw_ipo_data:
        st.info("⚠️ Database se koi IPO data fetch nahi hua. Backend script run hone ka wait karein.")
        return
        
    # 2. Process Data
    df = pd.DataFrame(raw_ipo_data)
    
    # Date ko properly format karna taaki sort ho sake
    if 'listing_date' in df.columns:
        df['listing_date'] = pd.to_datetime(df['listing_date'], errors='coerce')
        df = df.sort_values(by='listing_date', ascending=False)
        df['Formatted Date'] = df['listing_date'].dt.strftime('%d %b %Y')
    else:
        df['Formatted Date'] = "N/A"
        
    # 3. UI Filters (Year Select)
    st.write("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.write(f"📊 **Total Genuine IPOs:** `{len(df)}`")
    with col2:
        # Get unique years from the data for dropdown
        if 'listing_year' in df.columns:
            years = sorted(df['listing_year'].dropna().unique(), reverse=True)
            years_list = ["All"] + [str(int(y)) for y in years]
        else:
            years_list = ["All"]
            
        selected_year = st.selectbox("📅 Filter by Listing Year:", years_list)
        
    # Apply Filter
    if selected_year != "All":
        # Convert listing_year back to int for comparison
        display_df = df[df['listing_year'] == int(selected_year)].copy()
    else:
        display_df = df.copy()
        
    if display_df.empty:
        st.warning(f"🤷‍♂️ {selected_year} me koi data nahi mila.")
        return
        
    # 4. Prepare Table Format
    display_df['TV Chart'] = "https://in.tradingview.com/chart/?symbol=NSE:" + display_df['stock_symbol']
    
    # Select specific columns to show
    cols_to_show = ['stock_symbol', 'company_name', 'Formatted Date', 'TV Chart']
    available_cols = [c for c in cols_to_show if c in display_df.columns]
    final_df = display_df[available_cols].copy()
    
    # Rename columns for clean UI
    rename_map = {
        'stock_symbol': 'Symbol', 
        'company_name': 'Company Name', 
        'Formatted Date': 'Listing Date'
    }
    final_df.rename(columns=rename_map, inplace=True)
    
    # 5. The Magic Download Button
    colA, colB = st.columns([4, 1])
    with colA:
        st.write(f"Showing **{len(final_df)}** stocks for **{selected_year}**.")
    with colB:
        tv_txt = ", ".join([f"NSE:{sym}" for sym in final_df['Symbol']])
        st.download_button(
            label="📥 Watchlist (.txt)", 
            data=tv_txt, 
            file_name=f"IPOs_{selected_year}.txt", 
            mime="text/plain", 
            use_container_width=True
        )
        
    # 6. Render Custom Table
    st.markdown(render_html_table(final_df, max_height="550px"), unsafe_allow_html=True)
