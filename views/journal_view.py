import streamlit as st
import cloudinary.uploader
import time

def show_journal_page(supabase, is_admin):
    st.markdown("<div class='page-heading'>📓 Trading Journal</div>", unsafe_allow_html=True)
    try: 
        all_trades = supabase.table('trading_journal').select("*").order('buying_date', desc=True).execute().data
    except Exception: 
        all_trades = []
    if all_trades is None: all_trades = []
        
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("🎯 Total Trades Logged", len(all_trades))
    with m2: st.metric("⏳ Active Positions", len([t for t in all_trades if not t.get('sold_30_date')]))
    with m3: st.metric("✅ Closed Positions", len([t for t in all_trades if t.get('sold_30_date')]))
    st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin-bottom:20px;'>", unsafe_allow_html=True)
    
    if is_admin:
        j_tabs = st.tabs(["➕ New Trade", "🔄 Update Exits", "📚 Journal Gallery"])
        with j_tabs[0]:
            with st.form("new_trade_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                with c1: symbol = st.text_input("Stock Symbol").upper(); quantity = st.number_input("Quantity", min_value=1)
                with c2: buying_date = st.date_input("Date"); buying_price = st.number_input("Buy Price", min_value=0.0)
                with c3: initial_sl = st.number_input("Initial SL", min_value=0.0)
                trade_logic = st.text_area("Trade Logic"); image_file = st.file_uploader("Upload Chart", type=['png', 'jpg', 'jpeg'])
                if st.form_submit_button("💾 Save Trade") and symbol:
                    img_url = cloudinary.uploader.upload(image_file, folder="trading_journal").get("secure_url") if image_file else None
                    supabase.table('trading_journal').insert({"symbol": symbol, "total_quantity": quantity, "buying_date": str(buying_date), "buying_price": float(buying_price), "initial_sl": float(initial_sl), "trade_logic": trade_logic, "image_url": img_url}).execute()
                    st.success("Saved!"); time.sleep(1); st.rerun()
        
        with j_tabs[1]:
            active_trades_data = [t for t in all_trades if not t.get('sold_30_date')] if all_trades else []
            if active_trades_data:
                trade_options = {f"{t['symbol']} (Bought @ ₹{t['buying_price']})": t for t in active_trades_data}
                t = trade_options[st.selectbox("🎯 Select Active Trade", list(trade_options.keys()))]
                with st.form("update_trade_form"):
                    st.markdown("### 1️⃣ 20% Booking")
                    c1, c2, c3 = st.columns(3)
                    with c1: s20_date = st.date_input("Date", value=None)
                    with c2: s20_price = st.number_input("Price", value=float(t['sold_20_price'] or 0.0))
                    with c3: sl_20 = st.number_input("New SL", value=float(t['sl_after_20'] or 0.0))
                    if st.form_submit_button("🔄 Update Exits", type="primary"):
                        supabase.table('trading_journal').update({"sold_20_price": s20_price if s20_price>0 else None, "sl_after_20": sl_20}).eq('id', t['id']).execute()
                        st.success("Updated!"); time.sleep(1); st.rerun()
            else: st.info("No active trades found.")
    else: 
        j_tabs = st.tabs(["📚 Journal Gallery"])

    with j_tabs[-1]: 
        if all_trades:
            for tr in all_trades:
                st.markdown("<div class='journal-card'>", unsafe_allow_html=True)
                g1, g2 = st.columns([1, 2])
                with g1:
                    if tr.get('image_url'): st.image(tr['image_url'], use_container_width=True)
                with g2:
                    st.subheader(f"🚀 {tr['symbol']}")
                    st.write(f"**Date:** {tr['buying_date']} | **Buy Price:** ₹{tr['buying_price']} | **Qty:** {tr['total_quantity']}")
                    st.write(f"**Logic:** {tr['trade_logic']}")
                    if tr.get('sold_20_price'): st.success(f"**20% Booked @ ₹{tr['sold_20_price']}**")
                st.markdown("</div>", unsafe_allow_html=True)
        else: st.info("Journal is empty.")
