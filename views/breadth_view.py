import streamlit as st
import pandas as pd

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

def show_breadth_page(supabase):
    st.markdown("<div class='page-heading'>📈 Market Breadth Analysis</div>", unsafe_allow_html=True)
    
    # 1. Data Fetch Karna
    try:
        res_all = supabase.table('market_breadth_all').select('*').execute()
        res_nifty = supabase.table('market_breadth_nifty500').select('*').execute()
        
        df_all = pd.DataFrame(res_all.data)
        df_nifty = pd.DataFrame(res_nifty.data)
        
        # 🚀 TIME HATAANE KA MAGIC (dt.strftime)
        if not df_all.empty:
            df_all['date'] = pd.to_datetime(df_all['date']).dt.strftime('%Y-%m-%d')
            df_all = df_all.sort_values('date', ascending=False)
            
        if not df_nifty.empty:
            df_nifty['date'] = pd.to_datetime(df_nifty['date']).dt.strftime('%Y-%m-%d')
            df_nifty = df_nifty.sort_values('date', ascending=False)
            
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return

    # 2. Main Tabs (Sirf Table ke sath)
    main_tab1, main_tab2 = st.tabs(["🌐 All Stocks", "🏆 Nifty 500"])
    
    with main_tab1:
        if not df_all.empty:
            st.dataframe(df_all, use_container_width=True)
        else:
            st.info("⚠️ No data available for All Stocks yet.")
            
    with main_tab2:
        if not df_nifty.empty:
            st.dataframe(df_nifty, use_container_width=True)
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
            st.download_button(
                label="📊 Download All Stocks (CSV)",
                data=convert_df_to_csv(df_all),
                file_name="market_breadth_all.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )
            
    with btn_col2:
        if not df_nifty.empty:
            st.download_button(
                label="📊 Download Nifty 500 (CSV)",
                data=convert_df_to_csv(df_nifty),
                file_name="market_breadth_nifty500.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )
