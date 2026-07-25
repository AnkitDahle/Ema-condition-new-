import streamlit as st
import pandas as pd

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

def format_breadth_data(df, view_type):
    """Data ko Absolute ya Percentage view ke hisaab se format karne ka function"""
    if df.empty:
        return df
    
    res = df.copy()
    
    if view_type == "Absolute":
        # Absolute view mein jaisa data database se aaya hai waisa hi dikhana hai
        return res[['date', 'above_20dma', 'below_20dma', 'above_50dma', 'below_50dma']]
        
    elif view_type == "Percentage":
        # Text/String errors se bachne ke liye data ko numbers mein convert karna
        for col in ['above_20dma', 'below_20dma', 'above_50dma', 'below_50dma']:
            res[col] = pd.to_numeric(res[col], errors='coerce').fillna(0)
            
        # Total stocks calculate karna
        total_20 = res['above_20dma'] + res['below_20dma']
        total_50 = res['above_50dma'] + res['below_50dma']
        
        # Safe division (agar total 0 ho toh 1 maan lo taaki error na aaye)
        total_20 = total_20.replace(0, 1)
        total_50 = total_50.replace(0, 1)
        
        # Pehle numbers (float) mein percentage nikalna
        pct_20 = (res['above_20dma'] / total_20) * 100
        pct_50 = (res['above_50dma'] / total_50) * 100
        
        # 🚀 NAYA LOGIC: Dono percentage ko add karna
        total_pct = pct_20 + pct_50
        
        # Ab sabke aage '%' sign lagana
        res['% Above 20 DMA'] = pct_20.round(1).astype(str) + "%"
        res['% Above 50 DMA'] = pct_50.round(1).astype(str) + "%"
        res['Total % (20+50 DMA)'] = total_pct.round(1).astype(str) + "%"
        
        # Percentage view mein teeno columns return karna
        return res[['date', '% Above 20 DMA', '% Above 50 DMA', 'Total % (20+50 DMA)']]

def show_breadth_page(supabase):
    st.markdown("<div class='page-heading'>📈 Market Breadth Analysis</div>", unsafe_allow_html=True)
    
    # 1. Data Fetch Karna
    try:
        res_all = supabase.table('market_breadth_all').select('*').execute()
        res_nifty = supabase.table('market_breadth_nifty500').select('*').execute()
        
        df_all = pd.DataFrame(res_all.data)
        df_nifty = pd.DataFrame(res_nifty.data)
        
        if not df_all.empty:
            df_all['date'] = pd.to_datetime(df_all['date']).dt.strftime('%Y-%m-%d')
            df_all = df_all.sort_values('date', ascending=False)
            
        if not df_nifty.empty:
            df_nifty['date'] = pd.to_datetime(df_nifty['date']).dt.strftime('%Y-%m-%d')
            df_nifty = df_nifty.sort_values('date', ascending=False)
            
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return

    # 2. Main Tabs
    main_tab1, main_tab2 = st.tabs(["🌐 All Stocks", "🏆 Nifty 500"])
    
    # --- TAB 1: ALL STOCKS ---
    with main_tab1:
        if not df_all.empty:
            # Absolute/Percentage Toggle Button
            view_all = st.radio("👁️ Select View Format:", ["Absolute", "Percentage"], horizontal=True, key="view_all")
            
            # Function se data format karwa ke table dikhana
            display_df_all = format_breadth_data(df_all, view_all)
            st.dataframe(display_df_all, use_container_width=True)
        else:
            st.info("⚠️ No data available for All Stocks yet.")
            
    # --- TAB 2: NIFTY 500 ---
    with main_tab2:
        if not df_nifty.empty:
            # Absolute/Percentage Toggle Button
            view_nifty = st.radio("👁️ Select View Format:", ["Absolute", "Percentage"], horizontal=True, key="view_nifty")
            
            # Function se data format karwa ke table dikhana
            display_df_nifty = format_breadth_data(df_nifty, view_nifty)
            st.dataframe(display_df_nifty, use_container_width=True)
        else:
            st.info("⚠️ No data available for Nifty 500 yet.")

    # ==========================================
    # 3. DOWNLOAD BUTTONS (Raw Data Download Hoga)
    # ==========================================
    st.markdown("<br><hr style='border-color: rgba(255,255,255,0.1);'><br>", unsafe_allow_html=True)
    st.markdown("### 📥 Download Historical Data")
    
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        if not df_all.empty:
            st.download_button(
                label="📊 Download All Stocks (CSV)",
                data=convert_df_to_csv(df_all), # Yahan directly original DataFrame diya hai
                file_name="market_breadth_all.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )
            
    with btn_col2:
        if not df_nifty.empty:
            st.download_button(
                label="📊 Download Nifty 500 (CSV)",
                data=convert_df_to_csv(df_nifty), # Yahan directly original DataFrame diya hai
                file_name="market_breadth_nifty500.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )
