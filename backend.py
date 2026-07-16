import streamlit as st
from supabase import create_client
import pandas as pd

@st.cache_resource
def init_supabase():
    """Supabase connection ko cache karta hai taaki app fast rahe."""
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def fetch_swing_stocks():
    """Scanner ka data fetch karta hai."""
    supabase = init_supabase()
    try:
        return supabase.table('swing_stocks').select("*").order('scan_date', desc=True).execute().data
    except Exception as e:
        print(f"Error fetching swing stocks: {e}")
        return None

def fetch_ipo_data():
    """IPOs ka data fetch karta hai."""
    supabase = init_supabase()
    try:
        return supabase.table('ipo_master').select("*").execute().data
    except Exception as e:
        print(f"Error fetching IPO data: {e}")
        return None

def get_master_symbol_list(raw_data):
    """Catalyst aur Search tabs ke liye unique stocks ki master list banata hai."""
    master_symbol_list = ["RELIANCE", "TCS", "INFY", "ZOMATO", "SBIN"]
    if raw_data:
        # Scan kiye hue naye stocks ko bhi list mein add kar deta hai
        fetched_symbols = [str(x).upper() for x in pd.DataFrame(raw_data)['stock_symbol'].dropna().unique()]
        master_symbol_list.extend(fetched_symbols)
    return sorted(list(set(master_symbol_list)))
