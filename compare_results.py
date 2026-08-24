import os
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from supabase import create_client, Client

# ==========================================
# 1. Page Configuration
# ==========================================
st.set_page_config(page_title="Bhai's Fresh Breakout Radar", page_icon="🎯", layout="centered")
st.title("🎯 Fresh Breakout Radar (Result Filtered)")
st.write("Compare dates to find fresh institutional entries that just crossed the scanner!")

# ==========================================
# 2. Supabase Connection
# ==========================================
@st.cache_resource # Streamlit caching taaki baar baar connect na kare
def init_connection():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        st.error("⚠️ Supabase Credentials missing! Please set SUPABASE_URL and SUPABASE_KEY environment variables.")
        st.stop()
    return create_client(url, key)

supabase = init_connection()

# ==========================================
# 3. UI: Date Pickers
# ==========================================
col1, col2 = st.columns(2)
with col1:
    # Default Base date: 1 din pehle
    base_date = st.date_input("📅 Select Base Date (Purani Date)", datetime.today() - timedelta(days=1))
with col2:
    # Default Comparison date: Aaj ki date
    comp_date = st.date_input("🚀 Select Comparison Date (Nayi Date)", datetime.today())

# ==========================================
# 4. Core Logic & Button Action
# ==========================================
if st.button("🔍 Find Fresh Entries", type="primary"):
    
    if base_date >= comp_date:
        st.warning("⚠️ Base Date hamesha Comparison Date se purani (pehle ki) honi chahiye Bhai!")
    else:
        with st.spinner("Supabase se data fetch kar rahe hain..."):
            try:
                # Base Date ka data mangwana
                res_base = supabase.table('recent_results_log').select('stock_symbol').eq('scan_date', str(base_date)).execute()
                base_stocks = {row['stock_symbol'] for row in res_base.data}
                
                # Comparison Date ka data mangwana
                res_comp = supabase.table('recent_results_log').select('stock_symbol').eq('scan_date', str(comp_date)).execute()
                comp_stocks = {row['stock_symbol'] for row in res_comp.data}
                
                # Math: Naye Stocks = Comparison List MINUS Base List
                fresh_entries = comp_stocks - base_stocks
                
                # Statistics Dikhana
                st.write("---")
                st.write(f"📊 **Base Date ({base_date}) Stocks:** {len(base_stocks)}")
                st.write(f"📊 **Comparison Date ({comp_date}) Stocks:** {len(comp_stocks)}")
                
                # ==========================================
                # 5. Output & TradingView Download
                # ==========================================
                if fresh_entries:
                    st.success(f"🔥 Mila! {len(fresh_entries)} bilkul naye stocks aaye hain!")
                    
                    # Naye stocks ki list dikhana
                    fresh_list = sorted(list(fresh_entries))
                    st.write(", ".join(fresh_list))
                    
                    # TradingView Format banana (NSE:SYMBOL1, NSE:SYMBOL2)
                    tv_format = ", ".join([f"NSE:{sym}" for sym in fresh_list])
                    
                    st.write("---")
                    st.subheader("📥 Export for TradingView")
                    
                    # The Magic Download Button
                    st.download_button(
                        label="⬇️ Download TradingView Watchlist (.txt)",
                        data=tv_format,
                        file_name=f"Fresh_Breakouts_{comp_date}.txt",
                        mime="text/plain",
                        help="Download this file, copy the text inside, and paste it directly into your TradingView Watchlist + icon!"
                    )
                else:
                    st.info(f"🤷‍♂️ Koi nayi entry nahi aayi. Jo stocks {comp_date} ko the, wo {base_date} ko bhi the.")
                    
            except Exception as e:
                st.error(f"❌ Error fetching data: {e}")
