import os
from datetime import datetime
from supabase import create_client, Client

# Supabase Connection
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

today_date = datetime.now().strftime("%Y-%m-%d")

# Sirf 3 stocks ka test
test_stocks = ["RELIANCE", "TCS", "HDFCBANK"]
print("Starting 2-Minute Test...")

for stock in test_stocks:
    supabase.table('swing_stocks').insert({
        "scan_date": today_date,
        "stock_symbol": stock,
        "close_price": 1000.50,
        "turnover_cr": 500.00,
        "condition_matched": "Test Successful ✅"
    }).execute()
    print(f"✅ Successfully Saved: {stock}")

print("Test Complete!")
