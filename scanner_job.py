import os
from datetime import datetime
from supabase import create_client, Client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

print("Starting Fast Dummy Test...")
today = datetime.now().strftime("%Y-%m-%d")

try:
    # 2 dummy stocks directly godown mein dalne ka code
    data = supabase.table('swing_stocks').insert([
        {"scan_date": today, "stock_symbol": "RELIANCE", "close_price": 2500, "turnover_cr": 500, "condition_matched": "Test Pass ✅"},
        {"scan_date": today, "stock_symbol": "TCS", "close_price": 3500, "turnover_cr": 600, "condition_matched": "Test Pass ✅"}
    ]).execute()
    print("✅ Dono stocks Supabase mein chaley gaye!")
except Exception as e:
    print(f"❌ Supabase ka Error: {e}")
