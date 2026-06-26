import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import requests
import pandas as pd
import time
import datetime
import cloudinary
import cloudinary.uploader
import json

# 1. Page Configuration
st.set_page_config(page_title="AlphaSwing Pro", layout="wide", page_icon="📈", initial_sidebar_state="collapsed")

if 'current_page' not in st.session_state: st.session_state.current_page = "Home"

pages = ['Home', 'Scanner', 'Catalyst', 'IPOs', 'Journal']
active_index = pages.index(st.session_state.current_page) + 2

# --- 🎨 FINAL CSS (LOCKED BACKGROUND & NAVBAR) ---
custom_css = f"""
<style>
    .stApp {{ background: linear-gradient(-45deg, #09090b, #18181b, #0f172a, #171717); background-size: 400% 400%; animation: gradientBG 15s ease infinite; color: #f8fafc; }}
    @keyframes gradientBG {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} 100% {{ background-position: 0% 50%; }} }}
    
    header {{visibility: hidden;}}
    .block-container {{ padding-top: 1rem !important; }}

    /* NAVBAR LINKS */
    div[data-testid="stHorizontalBlock"]:first-of-type div.stButton > button {{ background: transparent !important; border: none !important; white-space: nowrap !important; }}
    div[data-testid="stHorizontalBlock"]:first-of-type div.stButton > button p {{ color: #7b8fa3 !important; font-weight: 500 !important; font-size: 19px !important; transition: all 0.2s; white-space: nowrap !important; }}
    div[data-testid="stHorizontalBlock"]:first-of-type div[data-testid="stColumn"]:nth-child({active_index}) div.stButton > button p {{ color: #ffffff !important; font-weight: 900 !important; }}

    /* ACTION BOXES (Run Scan & Watchlist) */
    .button-box-style button {{ background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; border-radius: 8px !important; font-weight: 500 !important; color: #e2e8f0 !important; padding: 6px 12px !important; }}
    .button-box-style button:hover {{ border-color: #00e5ff !important; color: #ffffff !important; }}

    .page-heading {{ font-size: 28px; font-weight: 600; color: #ffffff; border-bottom: 2px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-bottom: 20px; }}
    .journal-card {{ background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-bottom: 20px; }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 2. Navbar
col_logo, nav1, nav2, nav3, nav4, nav5, space, col_login = st.columns([2.5, 1.2, 1.2, 1.2, 1.2, 1.2, 0.5, 1.5])
with col_logo: st.markdown('<a href="/" target="_self" style="font-size: 22px; font-weight: 800; color: white; text-decoration: none;">AlphaSwing</a>', unsafe_allow_html=True)
with nav1:
    if st.button("Home", use_container_width=True): st.session_state.current_page = "Home"; st.rerun()
with nav2:
    if st.button("Scanner", use_container_width=True): st.session_state.current_page = "Scanner"; st.rerun()
with nav3:
    if st.button("Catalyst", use_container_width=True): st.session_state.current_page = "Catalyst"; st.rerun()
with nav4:
    if st.button("IPOs", use_container_width=True): st.session_state.current_page = "IPOs"; st.rerun()
with nav5:
    if st.button("Journal", use_container_width=True): st.session_state.current_page = "Journal"; st.rerun()
with col_login: st.button("Get Started", type="primary", use_container_width=True)
st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)

# 3. Logic & Routing
if st.session_state.current_page == "Home":
    st.markdown("<div style='text-align: center; padding-top: 100px;'><h1>Welcome to AlphaSwing Pro</h1></div>", unsafe_allow_html=True)

elif st.session_state.current_page == "Scanner":
    st.markdown("<div class='page-heading'>📊 Scanner</div>", unsafe_allow_html=True)
    # (Scanner logic here - Run Scan + Filters + Download + Dataframe)

elif st.session_state.current_page == "Catalyst":
    st.markdown("<div class='page-heading'>🔥 Catalyst</div>", unsafe_allow_html=True)
    # (Prompt logic here)

elif st.session_state.current_page == "IPOs":
    st.markdown("<div class='page-heading'>🏢 IPOs</div>", unsafe_allow_html=True)
    # (IPO logic here)

elif st.session_state.current_page == "Journal":
    st.markdown("<div class='page-heading'>📓 Journal</div>", unsafe_allow_html=True)
    # (Journal logic here)

# Footer Notes
st.markdown("<br><br>### Notes", unsafe_allow_html=True)
with st.form("global_scratchpad_form"):
    user_notes = st.text_area(" ", height=150, label_visibility="collapsed")
    if st.form_submit_button("💾 Save Notes", use_container_width=True): st.toast("✅ Saved!")
