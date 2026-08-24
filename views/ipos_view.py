import streamlit as st
import pandas as pd
from ui_styles import render_html_table  # Aapki custom table styling

def show_ipos_page(raw_ipo_data):
    st.markdown("<div class='page-heading'>🚀 Latest Genuine IPOs (2020+)</div>", unsafe_allow_html=True)
    
    if raw_ipo_data:
        df = pd.DataFrame(raw_ipo_data)
        
        # Agar aage piche columns ko format karna ho toh yahan kar sakte hain
        st.write("Below is the list of purely verified IPOs fetched from the database.")
        
        # Display the table using your custom UI style
        st.markdown(render_html_table(df, max_height="600px"), unsafe_allow_html=True)
    else:
        st.info("⚠️ Table is empty. Database se koi IPO data fetch nahi hua.")
