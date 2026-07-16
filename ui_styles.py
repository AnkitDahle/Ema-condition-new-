import streamlit as st
import pandas as pd

def render_html_table(df, max_height="350px"):
    html = f"<div style='overflow-x:auto; overflow-y:auto; max-height: {max_height}; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;'>"
    html += "<table style='width:100%; text-align:left; border-collapse: collapse; font-size: 14px;'>"
    html += "<thead><tr>"
    for col in df.columns:
        html += f"<th style='position: sticky; top: 0; background: #18181b; padding: 12px; color:#00e5ff; border-bottom: 1px solid rgba(255,255,255,0.1); white-space: nowrap; z-index: 1;'>{col}</th>"
    html += "</tr></thead><tbody>"
    for i, row in df.iterrows():
        bg = "background: rgba(0,0,0,0.2);" if i%2==0 else "background: rgba(255,255,255,0.02);"
        html += f"<tr style='{bg} border-bottom: 1px solid rgba(255,255,255,0.05);'>"
        for col in df.columns:
            val = row[col]
            if str(val).startswith("http"):
                html += f"<td style='padding: 10px;'><a href='{val}' target='_blank' style='background: #10b981; color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 12px; display: inline-block; white-space: nowrap;'>📈 Open Chart</a></td>"
            else:
                html += f"<td style='padding: 10px; color: #e2e8f0; white-space: nowrap;'>{val}</td>"
        html += "</tr>"
    html += "</tbody></table></div>"
    return html

def get_custom_css(active_index):
    return f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
<style>
/* ---------- BASE + FONT ---------- */
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif !important; font-size: 1.06rem !important; letter-spacing: 0.1px; }}
.stApp {{ background: linear-gradient(-45deg, #09090b, #18181b, #0f172a, #171717); background-size: 400% 400%; animation: gradientBG 18s ease infinite; color: #f8fafc; }}
@keyframes gradientBG {{ 0%{{background-position:0% 50%}} 50%{{background-position:100% 50%}} 100%{{background-position:0% 50%}} }}
.block-container {{ padding-top: 1rem !important; animation: fadeUp 0.6s ease both; }}
header {{ visibility: hidden; }}

/* ---------- ENTRANCE ANIMATIONS ---------- */
@keyframes fadeUp {{ from{{opacity:0; transform:translateY(14px)}} to{{opacity:1; transform:translateY(0)}} }}
@keyframes popIn {{ 0%{{opacity:0; transform:scale(.96)}} 100%{{opacity:1; transform:scale(1)}} }}
.page-heading, .journal-card, div[data-testid="stMetric"], .stPlotlyChart {{ animation: fadeUp 0.5s ease both; }}

/* ---------- HEADINGS (bold hierarchy) ---------- */
.page-heading {{ font-family: 'Space Grotesk', sans-serif; font-size: 32px; font-weight: 700; color: #ffffff; margin-top: -6px; margin-bottom: 22px; padding-bottom: 12px; border-bottom: 2px solid rgba(0,229,255,0.25); text-shadow: 0 0 22px rgba(0,229,255,0.15); letter-spacing: -0.5px; }}
h1,h2,h3,h4 {{ font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.3px; }}

/* ---------- METRIC CARDS ---------- */
div[data-testid="stMetric"] {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 16px 18px !important; backdrop-filter: blur(8px); transition: all 0.25s ease; }}
div[data-testid="stMetric"]:hover {{ border-color: rgba(0,229,255,0.5); transform: translateY(-3px); box-shadow: 0 10px 30px rgba(0,229,255,0.12); }}
div[data-testid="stMetricValue"] {{ font-family: 'Space Grotesk', sans-serif !important; font-weight: 700 !important; font-size: 30px !important; color: #00e5ff !important; }}
div[data-testid="stMetricLabel"] p {{ color:#94a3b8 !important; font-weight:500 !important; }}

/* ---------- BUTTONS ---------- */
.stButton > button[kind="secondary"], .stDownloadButton > button {{ background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.2) !important; border-radius: 10px !important; padding: 8px 14px !important; color: #e2e8f0 !important; font-weight: 600 !important; transition: all 0.25s cubic-bezier(.2,.8,.2,1) !important; }}
.stButton > button[kind="secondary"]:hover, .stDownloadButton > button:hover {{ border-color: #00e5ff !important; background: rgba(0,229,255,0.08) !important; color: #ffffff !important; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,229,255,0.18); }}
.stButton > button:active {{ transform: translateY(0) scale(.98); }}

/* ---------- TOP NAV ---------- */
div[data-testid="stHorizontalBlock"]:first-of-type .stButton > button {{ background: transparent !important; border: none !important; box-shadow: none !important; }}
div[data-testid="stHorizontalBlock"]:first-of-type .stButton > button p {{ color: #7b8fa3 !important; font-weight: 600 !important; font-size: 16px !important; letter-spacing: 0.4px; white-space: nowrap !important; transition: all 0.2s ease; }}
div[data-testid="stHorizontalBlock"]:first-of-type .stButton > button:hover p {{ color: #ffffff !important; text-shadow: 0 0 12px rgba(0,229,255,0.6); }}
div[data-testid="stHorizontalBlock"]:first-of-type div[data-testid="stColumn"]:nth-child({active_index}) .stButton > button p {{ color: #00e5ff !important; font-weight: 900 !important; text-shadow: 0 0 14px rgba(0,229,255,0.5); }}
div[data-testid="stHorizontalBlock"]:first-of-type button[kind="primary"] {{ background: linear-gradient(135deg,#00e5ff,#00b8d4) !important; border-radius: 8px !important; border: none !important; white-space: nowrap !important; box-shadow: 0 4px 16px rgba(0,229,255,0.35) !important; transition: all 0.25s ease !important; }}
div[data-testid="stHorizontalBlock"]:first-of-type button[kind="primary"]:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,229,255,0.5) !important; }}
div[data-testid="stHorizontalBlock"]:first-of-type button[kind="primary"] p {{ color:#000 !important; font-weight:900 !important; }}

@media (max-width: 768px) {{
    div[data-testid="stHorizontalBlock"]:first-of-type {{ display:flex !important; flex-wrap:nowrap !important; overflow-x:auto !important; padding-bottom:5px !important; }}
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="stColumn"] {{ min-width:max-content !important; flex:0 0 auto !important; width:auto !important; }}
    div[data-testid="stHorizontalBlock"]:first-of-type::-webkit-scrollbar {{ display:none; }}
    .page-heading {{ font-size: 26px; }}
}}

/* ---------- FORM SUBMIT ---------- */
div.stForm button[kind="primaryFormSubmit"] {{ background: linear-gradient(135deg,#3b82f6 0%,#8b5cf6 100%) !important; border:none !important; border-radius:10px !important; box-shadow: 0 4px 18px rgba(139,92,246,0.35) !important; transition: all 0.25s ease !important; }}
div.stForm button[kind="primaryFormSubmit"]:hover {{ transform: translateY(-2px); box-shadow: 0 8px 26px rgba(139,92,246,0.5) !important; }}
div.stForm button[kind="primaryFormSubmit"] p {{ font-weight:800 !important; color:white !important; }}

/* ---------- INPUTS ---------- */
.stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div, .stTextArea textarea {{ border-radius: 10px !important; transition: all 0.2s ease !important; }}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{ border-color: #00e5ff !important; box-shadow: 0 0 0 2px rgba(0,229,255,0.25) !important; }}

/* ---------- CARDS ---------- */
.journal-card {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); padding: 22px; border-radius: 16px; margin-bottom: 20px; backdrop-filter: blur(8px); transition: all 0.3s ease; }}
.journal-card:hover {{ border-color: rgba(0,229,255,0.3); transform: translateY(-4px); box-shadow: 0 14px 40px rgba(0,0,0,0.4); }}
.login-container {{ background: rgba(0,0,0,0.4); padding: 44px; border-radius: 18px; border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(12px); max-width: 400px; margin: 5vh auto auto; text-align: center; animation: popIn 0.5s ease both; box-shadow: 0 20px 60px rgba(0,0,0,0.5); }}

/* ---------- HTML TABLE ROW HOVER ---------- */
tbody tr {{ transition: background 0.15s ease; }}
tbody tr:hover {{ background: rgba(0,229,255,0.06) !important; }}

/* ---------- SCROLLBAR ---------- */
::-webkit-scrollbar {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-thumb {{ background: rgba(0,229,255,0.3); border-radius: 8px; }}
::-webkit-scrollbar-thumb:hover {{ background: rgba(0,229,255,0.5); }}
</style>
"""
