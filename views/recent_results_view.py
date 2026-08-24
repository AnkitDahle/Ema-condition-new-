import streamlit as st
import pandas as pd
from datetime import timedelta
from ui_styles import render_html_table  # Your custom CSS style

def show_recent_results_page(supabase):
    st.markdown("<div class='page-heading'>📅 Results Filtered Stocks (Time Machine)</div>", unsafe_allow_html=True)
    
    # ==========================================
    # 1. Fetch Data from Supabase (Fetches only once for speed)
    # ==========================================
    try: 
        response = supabase.table('recent_results_log').select("*").execute()
        raw_res_data = response.data 
    except Exception as e: 
        raw_res_data = None
        st.error(f"❌ Error fetching data: {e}")
        return
        
    if not raw_res_data:
        st.info("✅ Table is empty. Please wait for the backend script to run on GitHub.")
        return
        
    # Process Data
    df_res = pd.DataFrame(raw_res_data)
    
    if 'scan_date' not in df_res.columns:
        st.error("❌ 'scan_date' column is missing in the table.")
        return
        
    df_res['scan_date'] = pd.to_datetime(df_res['scan_date'], errors='coerce').dt.date
    df_res = df_res.dropna(subset=['scan_date'])
    
    if df_res.empty:
        st.info("✅ Database connected but no valid dates found.")
        return
        
    min_date = df_res['scan_date'].min()
    max_date = df_res['scan_date'].max()

    # ==========================================
    # 2. 🌟 THE SUB-NAVIGATION (TABS)
    # ==========================================
    tab1, tab2 = st.tabs(["📊 All Results", "🔥 Fresh Entries (Radar)"])
    
    # ------------------------------------------
    # TAB 1: EXISTING LOGIC (All Stocks)
    # ------------------------------------------
    with tab1:
        st.write("### 🔍 Select Scan Date")
        # key="tab1_date" is necessary so it doesn't conflict with Tab 2 calendars
        selected_date = st.date_input(
            "Select the date to view scanned data:", 
            value=max_date, 
            min_value=min_date, 
            max_value=max_date,
            key="tab1_date"
        )
        
        filtered_df = df_res[df_res['scan_date'] == selected_date].copy()
        
        if not filtered_df.empty:
            filtered_df = filtered_df.sort_values(by='result_date', ascending=False)
            
            display_res = filtered_df[['stock_symbol', 'result_date']].copy()
            display_res.columns = ['Stock Symbol', 'Result Date']
            display_res['TV Chart'] = "https://in.tradingview.com/chart/?symbol=NSE:" + display_res['Stock Symbol']
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"<p style='color: #94a3b8;'>Showing stocks whose results matched the criteria on <b>{selected_date.strftime('%d %B %Y')}</b>.</p>", unsafe_allow_html=True)
            with col2:
                # TradingView comma-separated format
                tv_txt = ", ".join([f"NSE:{sym}" for sym in display_res['Stock Symbol']])
                st.download_button(
                    "📥 Watchlist (.txt)", 
                    data=tv_txt, 
                    file_name=f"All_Results_{selected_date}.txt", 
                    mime="text/plain", 
                    use_container_width=True,
                    key="dl_tab1"
                )
            
            # Your custom table render
            st.markdown(render_html_table(display_res, max_height="500px"), unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ No results were fetched for any stock on {selected_date.strftime('%d %b %Y')}.")

    # ------------------------------------------
    # TAB 2: FRESH ENTRIES (Comparison Logic)
    # ------------------------------------------
    with tab2:
        st.write("### 🚀 Compare & Find Fresh Breakouts")
        st.markdown("<p style='color: #94a3b8;'>Compare two dates to identify brand new stocks that appeared on the Comparison Date but weren't there on the Base Date.</p>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            # Default base date is set to 1 day before the max_date
            default_base = max_date - timedelta(days=1) if max_date > min_date else min_date
            base_date = st.date_input("📅 Base Date (Older Date)", value=default_base, min_value=min_date, max_value=max_date, key="base_date")
        with c2:
            comp_date = st.date_input("⚡ Comparison Date (Newer Date)", value=max_date, min_value=min_date, max_value=max_date, key="comp_date")
            
        if st.button("🔍 Find Fresh Stocks", type="primary"):
            if base_date >= comp_date:
                st.warning("⚠️ Base Date must always be older than the Comparison Date!")
            else:
                # Filter Dataframes
                df_base = df_res[df_res['scan_date'] == base_date]
                df_comp = df_res[df_res['scan_date'] == comp_date]
                
                # Math: New Stocks = Comparison List - Base List
                base_stocks = set(df_base['stock_symbol'].tolist())
                comp_stocks = set(df_comp['stock_symbol'].tolist())
                fresh_symbols = comp_stocks - base_stocks
                
                st.write("---")
                st.write(f"📊 **{base_date}** Stocks: `{len(base_stocks)}` | **{comp_date}** Stocks: `{len(comp_stocks)}`")
                
                if fresh_symbols:
                    st.success(f"🔥 BINGO! {len(fresh_symbols)} FRESH stocks hit the radar!")
                    
                    # Create a new DataFrame for the fresh stocks
                    fresh_df = df_comp[df_comp['stock_symbol'].isin(fresh_symbols)].copy()
                    fresh_df = fresh_df.sort_values(by='result_date', ascending=False)
                    
                    display_fresh = fresh_df[['stock_symbol', 'result_date']].copy()
                    display_fresh.columns = ['Stock Symbol', 'Result Date']
                    display_fresh['TV Chart'] = "https://in.tradingview.com/chart/?symbol=NSE:" + display_fresh['Stock Symbol']
                    
                    colA, colB = st.columns([4, 1])
                    with colA:
                        st.write("👇 **Fresh Entries List:**")
                    with colB:
                        # New TradingView Download Button for fresh stocks
                        tv_txt_fresh = ", ".join([f"NSE:{sym}" for sym in display_fresh['Stock Symbol']])
                        st.download_button(
                            label="📥 Watchlist (.txt)", 
                            data=tv_txt_fresh, 
                            file_name=f"Fresh_Breakouts_{comp_date}.txt", 
                            mime="text/plain", 
                            use_container_width=True,
                            key="dl_tab2"
                        )
                        
                    # Custom CSS Table for fresh entries
                    st.markdown(render_html_table(display_fresh, max_height="500px"), unsafe_allow_html=True)
                else:
                    st.info(f"🤷‍♂️ No new entries. All the stocks scanned on {comp_date} were already in the list on {base_date}.")
