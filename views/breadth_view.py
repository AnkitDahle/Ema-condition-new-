import streamlit as st
import pandas as pd
from ui_styles import render_html_table

# Ek helper function taaki humein same code do baar na likhna pade
def fetch_and_display_breadth(supabase, table_name, desc_text):
    st.markdown(f"<p style='color: #94a3b8; margin-top: 5px; margin-bottom: 25px;'>{desc_text}</p>", unsafe_allow_html=True)
    
    try: 
        # Table name dynamically pass ho raha hai
        response = supabase.table(table_name).select("*").order('date', desc=True).execute()
        raw_data = response.data 
    except Exception as e: 
        raw_data = []
        
    if raw_data:
        df = pd.DataFrame(raw_data)
        
        df.rename(columns={
            'date': 'Date',
            'above_20dma': 'Above 20dma',
            'below_20dma': 'Below 20dma',
            'above_50dma': 'Above 50dma',
            'below_50dma': 'Below 50dma'
        }, inplace=True)
        
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime("%d %b'%y")
        
        # Table render karna
        st.markdown(render_html_table(df, max_height="550px"), unsafe_allow_html=True)
    else:
        st.info(f"⚠️ Data abhi database table '{table_name}' mein nahi mila.")

# Main page function
def show_breadth_page(supabase):
    st.markdown("<div class='page-heading'>📈 Market Breadth</div>", unsafe_allow_html=True)
    
    # Streamlit ke native TABS create karna
    tab1, tab2 = st.tabs(["🌐 All Stocks (NSE)", "🏆 Nifty 500"])
    
    # Pehle Tab ke andar ka content
    with tab1:
        fetch_and_display_breadth(
            supabase, 
            "market_breadth_all", 
            "Tracking complete broad market health (including small & micro caps). Fast market rotation pakadne ke liye best hai."
        )
        
    # Doosre Tab ke andar ka content
    with tab2:
        fetch_and_display_breadth(
            supabase, 
            "market_breadth_nifty500", 
            "Tracking mid and large-cap institutional sentiment. Yeh smooth aur stable trends dikhata hai."
        )
