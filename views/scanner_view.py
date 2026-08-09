import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from ui_styles import render_html_table
import os
from supabase import create_client, Client

# --- 🚀 Setup Supabase Client (For Free Float Fetch) ---
@st.cache_resource
def get_supabase_client():
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

def show_scanner_page(raw_data, is_admin):
    role_badge = "👑 Admin" if is_admin else "👁️ Viewer"
    st.markdown(f"<div class='page-heading'>📊 Market Scanner <span style='font-size:14px; color:#94a3b8; float:right; padding-top:10px;'>{role_badge}</span></div>", unsafe_allow_html=True)
    
    if not raw_data:
        st.info("No scan data available.")
        return

    # 1. Base Data Load
    df = pd.DataFrame(raw_data)
    
    # 2. 🚀 Fetch Free Float Data from Supabase
    supabase = get_supabase_client()
    try:
        res = supabase.table('free_float_master').select('*').execute()
        float_df = pd.DataFrame(res.data)
    except:
        float_df = pd.DataFrame()

    # 3. 🚀 Merge Data (Scanner Data + Free Float Data)
    if not float_df.empty and 'stock_symbol' in df.columns:
        df = pd.merge(df, float_df, left_on='stock_symbol', right_on='symbol', how='left')
        
        # Calculate % Float Traded 
        if 'traded_volume' in df.columns and 'float_shares_cr' in df.columns:
            df['% Float Traded'] = ((df['traded_volume'] / 10000000) / df['float_shares_cr']) * 100
            df['% Float Traded'] = df['% Float Traded'].round(2).astype(str) + "%"
            df['float_shares_cr'] = df['float_shares_cr'].astype(str) + " Cr"
            df['delivery_pct'] = df['delivery_pct'].astype(str) + "%"

    # 4. Rename Columns as per your original code
    cols_to_keep = ['scan_date', 'stock_symbol', 'close_price', 'turnover_cr', 'sector', 'industry_proxy', 'float_shares_cr', '% Float Traded', 'delivery_pct', 'traded_volume']
    df = df[[c for c in cols_to_keep if c in df.columns]]
    
    df.rename(columns={
        'scan_date': 'Scan Date', 
        'stock_symbol': 'Stock Symbol', 
        'close_price': 'Close Price (₹)', 
        'turnover_cr': 'Turnover (Cr)', 
        'sector': 'Sector', 
        'industry_proxy': 'Proxy / Industry',
        'float_shares_cr': 'Free Float Shares',
        'delivery_pct': 'Delivery %'
    }, inplace=True)
    
    df = df.drop_duplicates(subset=['Scan Date', 'Stock Symbol'], keep='first')
    
    # 5. UI Filters (Your exact logic)
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

    # 6. Admin Actions (Your exact logic)
    if is_admin:
        with f_col_run:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🚀 Run Scan", use_container_width=True):
                with st.spinner("Scanning..."):
                    requests.post(f"https://api.github.com/repos/{st.secrets['GITHUB_REPO']}/actions/workflows/daily_scan.yml/dispatches", headers={"Authorization": f"token {st.secrets['GITHUB_TOKEN']}", "Accept": "application/vnd.github.v3+json"}, json={"ref": "main"})
                    st.success("✅ Initiated!")

    # 7. Watchlist Download
    with f_col_dl:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        tv_text = "".join([f"### {sec} / {proxy},\n" + "".join([f"NSE:{sym},\n" for sym in group['Stock Symbol']]) for (sec, proxy), group in df_filtered.groupby(['Sector', 'Proxy / Industry'])]) if not df_filtered.empty else ""
        st.download_button("📥 Watchlist (.txt)", data=tv_text, file_name=f"AlphaSwing_{selected_date}.txt", mime="text/plain", use_container_width=True)

    # 8. Main Display Table (Hiding Sector & Proxy from UI ONLY)
    if not df_filtered.empty:
        display_df = df_filtered.copy()
        display_df['TV Chart'] = "https://in.tradingview.com/chart/?symbol=NSE:" + display_df['Stock Symbol']
        
        # 🧹 HIDING COLUMNS LOGIC (Data safe for Pie Charts, hidden from UI)
        cols_to_hide = ['Sector', 'Proxy / Industry', 'traded_volume']
        display_df = display_df.drop(columns=[c for c in cols_to_hide if c in display_df.columns])
        
        st.markdown(render_html_table(display_df, max_height="350px"), unsafe_allow_html=True)

    def create_custom_legend(counts_df, is_sector=True):
        colors = px.colors.qualitative.Pastel if is_sector else px.colors.qualitative.Set3
        html = "<div style='display: flex; flex-wrap: wrap; gap: 15px; margin-top: 15px; justify-content: center;'>"
        for i, row in counts_df.iterrows():
            color = colors[i % len(colors)]
            label = row['Legend_Label']
            html += f"<div style='display: flex; align-items: center; font-size: 13px; color: #e2e8f0;'><div style='width: 14px; height: 14px; background-color: {color}; border-radius: 3px; margin-right: 8px;'></div>{label}</div>"
        html += "</div>"
        return html

    st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin-top: 30px;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #ffffff; margin-bottom: 20px;'>🍩 Advanced Sector Explorer</h3>", unsafe_allow_html=True)

    # 9. Advanced Sector Explorer (Your EXACT Logic, using the preserved Sector data)
    if not df_selected_date.empty and 'Sector' in df_selected_date.columns:
        sector_counts = df_selected_date['Sector'].value_counts().reset_index()
        sector_counts.columns = ['Sector', 'Stock Count']
        sector_list = sorted(list(sector_counts['Sector']))
        total_sectors = sector_counts['Stock Count'].sum()
        sector_counts['Legend_Label'] = sector_counts.apply(lambda row: f"{row['Sector']} ({row['Stock Count']/total_sectors*100:.1f}%) ({row['Stock Count']})", axis=1)

        fig_sector = px.pie(sector_counts, values='Stock Count', names='Legend_Label', hole=0.45, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_sector.update_traces(textposition='inside', textinfo='percent', hovertemplate="<b>%{label}</b><br>Stocks: %{value}<extra></extra>")
        fig_sector.update_layout(
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
            margin=dict(t=40, b=10, l=0, r=0), title=dict(text="1️⃣ Overall Sector Distribution", font=dict(color="#00e5ff", size=16))
        )

        c_chart1, c_chart2 = st.columns([1, 1])
        with c_chart1: 
            st.plotly_chart(fig_sector, use_container_width=True)
            st.markdown(create_custom_legend(sector_counts, is_sector=True), unsafe_allow_html=True)

        with c_chart2:
            st.markdown("<div style='margin-top: 10px;'></div><p style='color:#00e5ff; font-weight: 600;'>👇 Select Sector to Explore:</p>", unsafe_allow_html=True)
            active_sector = st.selectbox("Sector", sector_list, label_visibility="collapsed")

            if active_sector:
                sector_df = df_selected_date[df_selected_date['Sector'] == active_sector]
                proxy_counts = sector_df['Proxy / Industry'].value_counts().reset_index()
                proxy_counts.columns = ['Proxy', 'Stock Count']
                total_proxies = proxy_counts['Stock Count'].sum()
                proxy_counts['Legend_Label'] = proxy_counts.apply(lambda row: f"{row['Proxy']} ({row['Stock Count']/total_proxies*100:.1f}%) ({row['Stock Count']})", axis=1)
                
                fig_proxy = px.pie(proxy_counts, values='Stock Count', names='Legend_Label', hole=0.45, color_discrete_sequence=px.colors.qualitative.Set3)
                fig_proxy.update_traces(textposition='inside', textinfo='percent', hovertemplate="<b>%{label}</b><br>Stocks: %{value}<extra></extra>")
                fig_proxy.update_layout(
                    showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
                    margin=dict(t=30, b=10, l=0, r=0), title=dict(text=f"2️⃣ Proxies in {active_sector}", font=dict(color="#10b981", size=16))
                )
                st.plotly_chart(fig_proxy, use_container_width=True)
                st.markdown(create_custom_legend(proxy_counts, is_sector=False), unsafe_allow_html=True)
                
        if active_sector:
            st.markdown(f"<h4 style='color:#ffffff; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-top: 30px;'>📋 {active_sector} Breakout List</h4>", unsafe_allow_html=True)
            
            display_proxy_df = sector_df[['Stock Symbol', 'Proxy / Industry']].copy()
            display_proxy_df.columns = ['Stock Name', 'Proxy Name']
            
            filter_c1, filter_c2 = st.columns([2, 1])
            with filter_c1: proxy_search = st.text_input("🔍 Search Stock or Proxy...", "")
            with filter_c2: proxy_sort = st.selectbox("↕️ Sort By", ["Stock Name (A-Z)", "Proxy Name (A-Z)"])
            
            if proxy_search:
                display_proxy_df = display_proxy_df[display_proxy_df['Stock Name'].str.contains(proxy_search, case=False, na=False) | display_proxy_df['Proxy Name'].str.contains(proxy_search, case=False, na=False)]
            
            if proxy_sort == "Stock Name (A-Z)": display_proxy_df = display_proxy_df.sort_values(by='Stock Name')
            else: display_proxy_df = display_proxy_df.sort_values(by='Proxy Name')
            
            display_proxy_df['TV Chart'] = "https://in.tradingview.com/chart/?symbol=NSE:" + display_proxy_df['Stock Name']
            st.markdown(render_html_table(display_proxy_df, max_height="350px"), unsafe_allow_html=True)
