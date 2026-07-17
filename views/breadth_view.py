import streamlit as st
import pandas as pd

# CSV Convertor Helper Function
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

def show_breadth_page(supabase):
    st.markdown("<div class='page-heading'>📈 Market Breadth Analysis</div>", unsafe_allow_html=True)
    
    # 1. Supabase se Data Fetch Karna
    try:
        res_all = supabase.table('market_breadth_all').select('*').execute()
        res_nifty = supabase.table('market_breadth_nifty500').select('*').execute()
        
        df_all = pd.DataFrame(res_all.data)
        df_nifty = pd.DataFrame(res_nifty.data)
        
        # Data ko Date ke hisaab se sort karna taaki chart seedha chale
        if not df_all.empty:
            df_all['date'] = pd.to_datetime(df_all['date'])
            df_all = df_all.sort_values('date')
        
        if not df_nifty.empty:
            df_nifty['date'] = pd.to_datetime(df_nifty['date'])
            df_nifty = df_nifty.sort_values('date')
            
    except Exception as e:
        st.error(f"❌ Error fetching data from Supabase: {e}")
        return

    # 2. Tabs Banake Data aur Charts Dikhana
    tab1, tab2 = st.tabs(["🌐 All Stocks", "🏆 Nifty 500"])
    
    # --- TAB 1: ALL STOCKS ---
    with tab1:
        if not df_all.empty:
            st.subheader("All Stocks: Above 20 DMA vs 50 DMA")
            # Chart ban banana
            chart_data_all = df_all.set_index('date')[['above_20dma', 'above_50dma']]
            st.line_chart(chart_data_all, use_container_width=True)
            
            # Raw Data Table (Expander ke andar taaki UI clean rahe)
            with st.expander("👀 View Raw Data (All Stocks)"):
                st.dataframe(df_all.sort_values('date', ascending=False), use_container_width=True)
        else:
            st.info("⚠️ No data available for All Stocks yet.")
            
    # --- TAB 2: NIFTY 500 ---
    with tab2:
        if not df_nifty.empty:
            st.subheader("Nifty 500: Above 20 DMA vs 50 DMA")
            # Chart banana
            chart_data_nifty = df_nifty.set_index('date')[['above_20dma', 'above_50dma']]
            st.line_chart(chart_data_nifty, use_container_width=True)
            
            # Raw Data Table
            with st.expander("👀 View Raw Data (Nifty 500)"):
                st.dataframe(df_nifty.sort_values('date', ascending=False), use_container_width=True)
        else:
            st.info("⚠️ No data available for Nifty 500 yet.")

    # ==========================================
    # 3. DOWNLOAD BUTTONS SECTION (Naya Feature)
    # ==========================================
    st.markdown("<br><hr style='border-color: rgba(255,255,255,0.1);'><br>", unsafe_allow_html=True)
    st.markdown("### 📥 Download Historical Data")
    
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        if not df_all.empty:
            # Pura data download ke liye ready karna (latest date upar)
            download_df_all = df_all.sort_values('date', ascending=False)
            csv_all = convert_df_to_csv(download_df_all)
            
            st.download_button(
                label="📊 Download All Stocks (CSV)",
                data=csv_all,
                file_name="market_breadth_all.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )
            
    with btn_col2:
        if not df_nifty.empty:
            # Pura data download ke liye ready karna (latest date upar)
            download_df_nifty = df_nifty.sort_values('date', ascending=False)
            csv_nifty = convert_df_to_csv(download_df_nifty)
            
            st.download_button(
                label="📊 Download Nifty 500 (CSV)",
                data=csv_nifty,
                file_name="market_breadth_nifty500.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )
