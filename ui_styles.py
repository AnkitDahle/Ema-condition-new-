import pandas as pd

def get_custom_css():
    return """
    <style>
    /* =========================================
       🎨 GLOBAL THEME & COLORS
       ========================================= */
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    
    .page-heading { font-size: 30px; font-weight: 800; color: #00e5ff; margin-bottom: 20px; border-bottom: 1px solid #1f2937; padding-bottom: 10px; }

    .login-container { background: rgba(13, 17, 23, 0.8); padding: 40px; border-radius: 12px; border: 1px solid #30363d; text-align: center; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3); }

    /* =========================================
       🚀 NEW NAVIGATION STYLING (Box look removed)
       ========================================= */
    
    /* 1. INACTIVE BUTTONS (Sleek & Transparent) */
    button[data-testid="baseButton-secondary"] {
        background-color: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #94a3b8 !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        transition: all 0.3s ease !important;
    }
    button[data-testid="baseButton-secondary"]:hover {
        border-color: #00e5ff !important;
        color: #00e5ff !important;
        background-color: rgba(0, 229, 255, 0.05) !important;
    }

    /* 2. ACTIVE TAB & LOGO (Glowing Highlight) */
    button[data-testid="baseButton-primary"] {
        background-color: rgba(0, 229, 255, 0.15) !important;
        border: 1px solid #00e5ff !important;
        color: #00e5ff !important;
        font-weight: 800 !important;
        border-radius: 6px !important;
        box-shadow: 0 0 10px rgba(0, 229, 255, 0.2) !important;
    }

    /* =========================================
       📱 MOBILE RESPONSIVE DESIGN (Swipe Menu)
       ========================================= */
    @media (max-width: 768px) {
        [data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
            padding-bottom: 10px; 
        }
        [data-testid="column"] { min-width: 110px !important; }
        .stDataFrame, [data-testid="stTable"], .stTable { overflow-x: auto !important; display: block !important; white-space: nowrap !important; }
        .page-heading { font-size: 24px !important; text-align: center !important; }
        .block-container { padding-top: 2rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
        [data-testid="stMetricValue"] > div {
            white-space: normal !important; 
            font-size: 22px !important; 
            overflow: visible !important;
        }
    }
    </style>
    """

def render_html_table(df, max_height="500px"):
    html = f'<div style="overflow-y: auto; overflow-x: auto; max-height: {max_height}; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 15px;">'
    html += '<table style="width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 14px; text-align: left;">'
    html += '<thead style="position: sticky; top: 0; background-color: #161b22; z-index: 1;"><tr>'
    for col in df.columns:
        html += f'<th style="padding: 12px 15px; color: #00e5ff; border-bottom: 2px solid #30363d; white-space: nowrap;">{col}</th>'
    html += '</tr></thead><tbody>'
    for i, row in df.iterrows():
        bg_color = "#0d1117" if i % 2 == 0 else "#161b22"
        html += f'<tr style="background-color: {bg_color}; border-bottom: 1px solid #21262d; transition: 0.2s;">'
        for val in row:
            if isinstance(val, str) and val.startswith("http"):
                val = f'<a href="{val}" target="_blank" style="color: #58a6ff; text-decoration: none;">View Chart</a>'
            html += f'<td style="padding: 10px 15px; color: #c9d1d9; white-space: nowrap;">{val}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    return html
