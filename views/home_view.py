import streamlit as st
import streamlit.components.v1 as components

def show_home_page():
    components.html(
        """
        <script src="https://cdn.jsdelivr.net/npm/typed.js@2.0.12"></script>
        <style>
            body { font-family: 'Inter', sans-serif; text-align: center; background-color: transparent; margin: 0; padding-top: 80px; color: #f8fafc; }
            .main-text { font-size: 50px; font-weight: 800; letter-spacing: -1px; }
            .highlight { color: #00e5ff; text-shadow: 0 0 20px rgba(0, 229, 255, 0.5);}
        </style>
        <div class="main-text">AlphaSwing Pro: Best tool for <br><span id="typed" class="highlight"></span></div>
        <script>
            var typed = new Typed('#typed', {
                strings: ['Swing Trading.', 'Live Market Scans.', 'Technical Analysis.', 'Pro Trading Journal.'],
                typeSpeed: 60, backSpeed: 40, backDelay: 1500, loop: true, showCursor: true, cursorChar: '|'
            });
        </script>
        """,
        height=300,
    )
