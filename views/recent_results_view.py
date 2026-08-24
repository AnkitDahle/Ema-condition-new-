import streamlit as st
import pandas as pd
from ui_styles import render_html_table  # Aapki custom CSS style (agar use ho rahi hai)

def show_recent_results_page(supabase):
    st.markdown("<div class='page-heading'>📅 Results in Last 3 Days (Time Machine)</div>", unsafe_allow_html=True)
    
    # 1. Fetch Data from Supabase
    try: 
        response = supabase.table('recent_results_log').select("*").execute()
        raw_res_data = response.data 
    except Exception as e: 
        raw_res_data = None
        st.error(f"❌ Error fetching data: {e}")
        return
        
    # 2. Process and Display Data
    if raw_res_data:
        df_res = pd.DataFrame(raw_res_data)
        
        # Check column existence aur date format theek karna
        if 'scan_date' in df_res.columns:
            df_res['scan_date'] = pd.to_datetime(df_res['scan_date'], errors='coerce').dt.date
            df_res = df_res.dropna(subset=['scan_date'])
            
            if not df_res.empty:
                min_date = df_res['scan_date'].min()
                max_date = df_res['scan_date'].max()
                
                # 🌟 THE DATE PICKER (Scan Date Filter)
                st.write("### 🔍 Select Scan Date")
                selected_date = st.date_input(
                    "Aap kis din ka scanned data dekhna chahte hain?", 
                    value=max_date, 
                    min_value=min_date, 
                    max_value=max_date
                )
                
                # Filter Data
                filtered_df = df_res[df_res['scan_date'] == selected_date].copy()
                
                if not filtered_df.empty:
                    filtered_df = filtered_df.sort_values(by='result_date', ascending=False)
                    
                    display_res = filtered_df[['stock_symbol', 'result_date']].copy()
                    display_res.columns = ['Stock Symbol', 'Result Date']
                    display_res['TV Chart'] = "https://in.tradingview.com/chart/?symbol=NSE:" + display_res['Stock Symbol']
                    
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"<p style='color: #94a3b8;'>Showing stocks whose results came out within 3 days prior to <b>{selected_date.strftime('%d %B %Y')}</b>.</p>", unsafe_allow_html=True)
                    with col2:
                        tv_txt = "".join([f"NSE:{sym},\n" for sym in display_res['Stock Symbol']])
                        st.download_button("📥 Watchlist (.txt)", data=tv_txt, file_name=f"Recent_Results_{selected_date}.txt", mime="text/plain", use_container_width=True)
                    
                    # Aapki custom table call
                    st.markdown(render_html_table(display_res, max_height="500px"), unsafe_allow_html=True)
                else:
                    st.warning(f"⚠️ {selected_date.strftime('%d %b %Y')} ko list ke kisi stock ka result fetch nahi hua tha.")
            else:
                st.info("✅ Database connected par valid dates nahi mili.")
        else:
            st.error("❌ 'scan_date' column table mein nahi hai.")
    else:
        st.info("✅ Table is empty. Github par pehle backend script run hone ka wait karein.")
