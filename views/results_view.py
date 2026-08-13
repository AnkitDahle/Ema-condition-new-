import streamlit as st
import pandas as pd
import datetime
from ui_styles import render_html_table

def show_results_page(supabase):
    st.markdown("<div class='page-heading'>📅 Upcoming Earnings (Time Machine)</div>", unsafe_allow_html=True)
    
    try: 
        response = supabase.table('earnings_calendar').select("*").execute()
        raw_res_data = response.data 
    except Exception as e: 
        raw_res_data = None
        
    if raw_res_data is not None: 
        df_res = pd.DataFrame(raw_res_data)
        
        if not df_res.empty and 'result_date' in df_res.columns:
            
            # 🌟 SMART HACK: Dataframe me humne 'result_date' ko 'scan_date' maan liya hai
            df_res['scan_date'] = pd.to_datetime(df_res['result_date'], errors='coerce').dt.date
            df_res = df_res.dropna(subset=['scan_date'])
            
            if not df_res.empty:
                # Filter ke liye sabse purani aur sabse nayi date nikalna
                min_date = df_res['scan_date'].min()
                max_date = df_res['scan_date'].max()
                
                # 🌟 DATE PICKER (Time Machine)
                st.write("### 🔍 Select Scan Date")
                selected_date = st.date_input(
                    "Aap kis din ka scanned data dekhna chahte hain?", 
                    value=max_date, 
                    min_value=min_date, 
                    max_value=max_date
                )
                
                # Jo date chunenge, sirf wahi data filter hoga
                filtered_df = df_res[df_res['scan_date'] == selected_date].copy()
                
                if not filtered_df.empty:
                    # Table ko Symbol ke A to Z me sort karna
                    filtered_df = filtered_df.sort_values(by='stock_symbol', ascending=True)
                    
                    # 🌟 DISPLAY PREPARATION: Table me sirf Stock ka naam aur chart ka link jayega
                    display_res = filtered_df[['stock_symbol']].copy()
                    display_res.columns = ['Stock Symbol']
                    display_res['TV Chart'] = "https://in.tradingview.com/chart/?symbol=NSE:" + display_res['Stock Symbol']
                    
                    res_col_text, res_col_dl = st.columns([4, 1])
                    with res_col_text:
                        st.markdown(f"<p style='color: #94a3b8; margin-top:10px;'>In stocks ke results agle 30 din me aane wale the jab inhe <b>{selected_date.strftime('%d %b %Y')}</b> ko scan kiya gaya tha.</p>", unsafe_allow_html=True)
                    with res_col_dl:
                        tv_res_txt = "".join([f"NSE:{sym},\n" for sym in display_res['Stock Symbol']])
                        st.download_button("📥 Watchlist (.txt)", data=tv_res_txt, file_name=f"Earnings_Watchlist_{selected_date}.txt", mime="text/plain", use_container_width=True)
                        
                    # Aapki custom UI render HTML table
                    st.markdown(render_html_table(display_res, max_height="500px"), unsafe_allow_html=True)
                else:
                    st.warning(f"⚠️ {selected_date.strftime('%d %b %Y')} ko koi data scan nahi hua tha.")
            else:
                st.info("✅ Database Connected: Par date ka format kharab hai.")
        else:
            st.info("✅ Database Connected: Par table abhi khali (empty) hai. Script run hone ka wait karein.")
    else:
        st.error("❌ Database Alert: Supabase mein `earnings_calendar` table missing hai ya error hai.")
