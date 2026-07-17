import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta

# CSV Convertor Helper Function
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# Graph Banane ka helper function (Taaki code clean rahe)
def render_grouped_bar_chart(df, chart_key):
    # Default Last 7 Days ki range set karna
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    default_start = max_date - timedelta(days=7)
    
    if default_start < min_date:
        default_start = min_date

    # Date Range Selector
    dates = st.date_input(
        f"📅 Select Date Range", 
        [default_start, max_date], 
        min_value=min_date, 
        max_value=max_date,
        key=chart_key
    )
    
    # Streamlit date_input kabhi 1 date deta hai kabhi 2
    if len(dates) == 2:
        start_date, end_date = dates
    else:
        start_date = end_date = dates[0]

    # Data Filter Karna
    mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
    filtered_df = df.loc[mask]

    if not filtered_df.empty:
        # Plotly Grouped Bar Chart Banana
        fig = go.Figure(data=[
            # 20 DMA (Green Shades)
            go.Bar(name='Above 20 DMA', x=filtered_df['date'], y=filtered_df['above_20dma'], marker_color='#10b981'), # Dark Green
            go.Bar(name='Below 20 DMA', x=filtered_df['date'], y=filtered_df['below_20dma'], marker_color='#a7f3d0'), # Light Green
            # 50 DMA (Blue Shades)
            go.Bar(name='Above 50 DMA', x=filtered_df['date'], y=filtered_df['above_50dma'], marker_color='#3b82f6'), # Dark Blue
            go.Bar(name='Below 50 DMA', x=filtered_df['date'], y=filtered_df['below_50dma'], marker_color='#bfdbfe')  # Light Blue
        ])
        
        # Chart UI Setup (Dark mode ke hisaab se)
        fig.update_layout(
            barmode='group',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#c9d1d9'),
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Selected date range mein koi data nahi hai.")

def show_breadth_page(supabase):
    st.markdown("<div class='page-heading'>📈 Market Breadth Analysis</div>", unsafe_allow_html=True)
    
    # 1. Data Fetch Karna
    try:
        res_all = supabase.table('market_breadth_all').select('*').execute()
        res_nifty = supabase.table('market_breadth_nifty500').select('*').execute()
        
        df_all = pd.DataFrame(res_all.data)
        df_nifty = pd.DataFrame(res_nifty.data)
        
        if not df_all.empty:
            df_all['date'] = pd.to_datetime(df_all['date'])
            df_all = df_all.sort_values('date')
            df_all['date'] = df_all['date'].dt.normalize() # Time hatane ke liye
            
        if not df_nifty.empty:
            df_nifty['date'] = pd.to_datetime(df_nifty['date'])
            df_nifty = df_nifty.sort_values('date')
            df_nifty['date'] = df_nifty['date'].dt.normalize()
            
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return

    # 2. Main Tabs
    main_tab1, main_tab2 = st.tabs(["🌐 All Stocks", "🏆 Nifty 500"])
    
    # --- MAIN TAB 1: ALL STOCKS ---
    with main_tab1:
        if not df_all.empty:
            # Sub Tabs for Table & Graph
            sub_tab_table1, sub_tab_graph1 = st.tabs(["📋 Table View", "📊 Graph View"])
            
            with sub_tab_table1:
                st.dataframe(df_all.sort_values('date', ascending=False), use_container_width=True)
                
            with sub_tab_graph1:
                render_grouped_bar_chart(df_all, chart_key="all_stocks_dates")
        else:
            st.info("⚠️ No data available for All Stocks yet.")
            
    # --- MAIN TAB 2: NIFTY 500 ---
    with main_tab2:
        if not df_nifty.empty:
            # Sub Tabs for Table & Graph
            sub_tab_table2, sub_tab_graph2 = st.tabs(["📋 Table View", "📊 Graph View"])
            
            with sub_tab_table2:
                st.dataframe(df_nifty.sort_values('date', ascending=False), use_container_width=True)
                
            with sub_tab_graph2:
                render_grouped_bar_chart(df_nifty, chart_key="nifty500_dates")
        else:
            st.info("⚠️ No data available for Nifty 500 yet.")

    # ==========================================
    # 3. DOWNLOAD BUTTONS
    # ==========================================
    st.markdown("<br><hr style='border-color: rgba(255,255,255,0.1);'><br>", unsafe_allow_html=True)
    st.markdown("### 📥 Download Historical Data")
    
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        if not df_all.empty:
            download_df_all = df_all.sort_values('date', ascending=False)
            # Date ko wapas string format (YYYY-MM-DD) mein karna Excel ke liye
            download_df_all['date'] = download_df_all['date'].dt.strftime('%Y-%m-%d')
            st.download_button(
                label="📊 Download All Stocks (CSV)",
                data=convert_df_to_csv(download_df_all),
                file_name="market_breadth_all.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )
            
    with btn_col2:
        if not df_nifty.empty:
            download_df_nifty = df_nifty.sort_values('date', ascending=False)
            download_df_nifty['date'] = download_df_nifty['date'].dt.strftime('%Y-%m-%d')
            st.download_button(
                label="📊 Download Nifty 500 (CSV)",
                data=convert_df_to_csv(download_df_nifty),
                file_name="market_breadth_nifty500.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )
