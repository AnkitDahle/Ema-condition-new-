import streamlit as st
import pandas as pd
from ui_styles import render_html_table

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

def show_ipos_page(raw_ipo_data):
    st.markdown("<div class='page-heading'>🏢 IPOs</div>", unsafe_allow_html=True)
    
    if raw_ipo_data is not None:
        if len(raw_ipo_data) > 0:
            df_ipo = pd.DataFrame(raw_ipo_data)
            
            sym_col = 'stock_symbol' if 'stock_symbol' in df_ipo.columns else ('symbol' if 'symbol' in df_ipo.columns else None)
            date_col = 'listing_date' if 'listing_date' in df_ipo.columns else ('date' if 'date' in df_ipo.columns else None)
            name_col = 'company_name' if 'company_name' in df_ipo.columns else ('name' if 'name' in df_ipo.columns else None)
            year_col = 'listing_year' if 'listing_year' in df_ipo.columns else ('year' if 'year' in df_ipo.columns else None)
            
            if not sym_col or not date_col:
                st.error("⚠️ Table toh mili par usme Symbol ya Date wale columns ke naam match nahi ho rahe hain!")
                st.write("Aapke maujuda columns hain:", list(df_ipo.columns))
            else:
                df_ipo['calc_date'] = pd.to_datetime(df_ipo[date_col], errors='coerce')
                df_ipo['Month'] = df_ipo['calc_date'].dt.strftime('%B')
                df_ipo['Year_Filter'] = df_ipo[year_col] if year_col else df_ipo['calc_date'].dt.year
                
                today = pd.to_datetime('today').date()
                
                this_year_count = len(df_ipo[df_ipo['calc_date'].dt.year == today.year])
                m1, m2, m3, m4 = st.columns([1, 1, 1, 3])
                with m1: st.metric("Today Listed", len(df_ipo[df_ipo['calc_date'].dt.date == today]))
                with m2: st.metric("This Month", len(df_ipo[(df_ipo['calc_date'].dt.month == today.month) & (df_ipo['calc_date'].dt.year == today.year)]))
                with m3: st.metric("This Year", this_year_count)
                st.markdown("<br>", unsafe_allow_html=True)

                col_y1, col_m1, col_search = st.columns([1.2, 1.2, 1.5])
                available_years = sorted([int(x) for x in df_ipo['Year_Filter'].dropna().unique()], reverse=True) if not df_ipo['Year_Filter'].dropna().empty else [today.year]
                with col_y1: selected_year = st.selectbox("📅 IPO Year:", available_years)
                with col_m1: selected_month = st.selectbox("🗓️ Month:", ["All Months", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
                
                fil = df_ipo[df_ipo['Year_Filter'].astype(str) == str(selected_year)]
                if selected_month != "All Months": fil = fil[fil['Month'] == selected_month]
                
                with col_search: selected_ipo_stock = st.selectbox("🔤 Search IPO:", sorted(list(fil[sym_col].dropna().unique())), index=None, placeholder="Type symbol...")
                if selected_ipo_stock: fil = fil[fil[sym_col] == selected_ipo_stock]
                
                display_ipo = fil[[sym_col, name_col if name_col else sym_col, date_col]].sort_values(by=date_col, ascending=False)
                display_ipo.columns = ['Symbol', 'Company Name', 'Listing Date']
                display_ipo['TV Chart'] = "https://in.tradingview.com/chart/?symbol=NSE:" + display_ipo['Symbol']
                
                st.markdown(render_html_table(display_ipo, max_height="500px"), unsafe_allow_html=True)

                # ==========================================
                # 📥 DOWNLOAD BUTTON SECTION
                # ==========================================
                st.markdown("<br><hr style='border-color: rgba(255,255,255,0.1);'><br>", unsafe_allow_html=True)
                st.markdown("### 📥 Download Filtered Data")
                
                btn_col1, btn_col2 = st.columns([2, 3])
                with btn_col1:
                    download_df = display_ipo.drop(columns=['TV Chart']).copy()
                    
                    # 🚀 TRADINGVIEW FORMAT + COMMA MAGIC
                    # Har stock ke aage ab automatically comma lag jayega (e.g., NSE:ZOMATO,)
                    download_df.insert(0, 'TradingView Copy', 'NSE:' + download_df['Symbol'] + ',')
                    
                    st.download_button(
                        label="📊 Download IPOs (CSV)",
                        data=convert_df_to_csv(download_df),
                        file_name=f"ipos_{selected_year}_TV.csv",
                        mime="text/csv",
                        use_container_width=True,
                        type="primary"
                    )

        else:
            st.info("💡 **Database Connected:** Table `ipo_master` mil gayi hai, par uske andar abhi koi data nahi hai (Khali hai).")
    else:
        st.error("❌ Table Connect Error: Supabase se data fetch nahi ho pa raha hai. Ek baar check karein ki table ka naam 'ipo_master' hi hai na?")
