import pandas as pd

def get_custom_css(active_index=0):
    return """
    <style>
    /* =========================================
       🎨 GLOBAL THEME & COLORS
       ========================================= */
    .stApp {
        background-color: #0e1117;
        color: #c9d1d9;
    }
    
    /* Page Headings */
    .page-heading {
        font-size: 30px;
        font-weight: 800;
        color: #00e5ff;
        margin-bottom: 20px;
        border-bottom: 1px solid #1f2937;
        padding-bottom: 10px;
    }

    /* Login Box Styling */
    .login-container {
        background: rgba(13, 17, 23, 0.8);
        padding: 40px;
        border-radius: 12px;
        border: 1px solid #30363d;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }

    /* Button Customizations */
    .stButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        border: 1px solid #30363d !important;
    }
    .stButton > button:hover {
        border-color: #00e5ff !important;
        color: #00e5ff !important;
    }

    /* Sidebar Customization */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }

    /* =========================================
       📱 MOBILE RESPONSIVE DESIGN (Option B)
       ========================================= */
    @media (max-width: 768px) {
        /* Badi Tables ko horizontal scrollable banana */
        .stDataFrame, [data-testid="stTable"], .stTable {
            overflow-x: auto !important;
            display: block !important;
            white-space: nowrap !important;
        }

        /* Page Headings ka size chota karna */
        .page-heading {
            font-size: 24px !important;
            text-align: center !important;
        }

        /* Container padding kam karna taaki jagah bache */
        .login-container, div[style*="background: rgba(0,0,0,0.4)"] {
            padding: 15px !important;
        }

        /* Main screen padding adjust karna */
        .block-container {
            padding-top: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        /* 🚀 FIX: Date aur Breakout Numbers ko same size ka banana aur wrap karna */
        [data-testid="stMetricValue"] > div {
            white-space: normal !important; 
            font-size: 26px !important; /* Dono ekdum same size (26px) ke dikhenge */
            line-height: 1.2 !important;
            overflow: visible !important;
        }
    }
    </style>
    """

def render_html_table(df, max_height="500px"):
    """Renders a beautiful, scrollable HTML table with dark theme."""
    html = f'<div style="overflow-y: auto; overflow-x: auto; max-height: {max_height}; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 15px;">'
    html += '<table style="width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 14px; text-align: left;">'
    
    # Table Header
    html += '<thead style="position: sticky; top: 0; background-color: #161b22; z-index: 1;"><tr>'
    for col in df.columns:
        html += f'<th style="padding: 12px 15px; color: #00e5ff; border-bottom: 2px solid #30363d; white-space: nowrap;">{col}</th>'
    html += '</tr></thead>'
    
    # Table Body
    html += '<tbody>'
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
