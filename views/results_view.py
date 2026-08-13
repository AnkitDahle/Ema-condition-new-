import streamlit as st
import pandas as pd
import datetime
from ui_styles import render_html_table

def show_results_page(supabase):
    st.markdown("<div class='page-heading'>📅 Upcoming Earnings (Next 30 Days)</div>", unsafe_allow_html=True)
    
    try: 
        response = supabase.table('earnings_calendar').select("*").execute()
        raw_res_data = response.data 
    except Exception as e: 
        raw_res_data = None
        
    if raw_res_data is not None: 
        df_res = pd.DataFrame(raw_res_data)
        
        if not df_res.empty and 'result_date' in df_res.columns:
            df_res['calc_date'] = pd.to_datetime(df_res['result_date'], errors='coerce').dt.date
            today = pd.to_datetime('today').date()
            next_30 = today + datetime.timedelta(days=30)
            
            df_res = df_res[(df_res['calc_date'] >= today) & (df_res['calc_date'] <= next_30)]
            df_res = df_res.sort_values(by='calc_date', ascending=True)
            
            if not df_res.empty:
                display_res = df_res[['stock_symbol', 'result_date']].copy()
                display_res.columns = ['Stock Symbol', 'Result Date']
                display_res['TV Chart'] = "https://in.tradingview.com/chart/?symbol=NSE:" + display_res['Stock Symbol']
                
                res_col_text, res_col_dl = st.columns([4, 1])
                with res_col_text:
                    st.markdown("<p style='color: #94a3b8; margin-top:10px;'>In stocks ke results aane wale hain, inpar khaas nazar rakhein momentum ke liye!</p>", unsafe_allow_html=True)
                with res_col_dl:
                    tv_res_txt = "".join([f"NSE:{sym},\n" for sym in display_res['Stock Symbol']])
                    st.download_button("📥 Watchlist (.txt)", data=tv_res_txt, file_name=f"Earnings_Watchlist.txt", mime="text/plain", use_container_width=True)
                    
                # ==========================================
                # 🌟 THE NEW DATE-WISE LOGIC (Expander Loop)
                # ==========================================
                unique_dates = display_res['Result Date'].unique()
                
                for date in unique_dates:
                    # Format date to look better (Optional: You can change format here)
                    display_date = pd.to_datetime(date).strftime('%d %b %Y') 
                    
                    # Har date ke liye ek alag dropdown/expander box
                    with st.expander(f"📅 Results on {display_date}", expanded=True):
                        
                        # Sirf us specific date ka data filter karna
                        date_df = display_res[display_res['Result Date'] == date].copy()
                        
                        # Ab table me date dikhane ki zaroorat nahi, toh use drop kar diya
                        date_df = date_df[['Stock Symbol', 'TV Chart']]
                        
                        # Aapki custom UI style wali table ko render karna
                        st.markdown(render_html_table(date_df, max_height="300px"), unsafe_allow_html=True)
                        
            else:
                st.info("✅ Database Connected: Par agle 30 dino mein kisi bhi stock ka result scheduled nahi hai.")
        else:
            st.info("✅ Database Connected: Par table abhi khali (empty) hai. GitHub se Earnings Script run hone ka wait karein.")
    else:
        st.error("❌ Database Alert: Supabase mein `earnings_calendar` table missing hai ya error hai.")
