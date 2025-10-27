import requests
import json

API_KEY = "44328ca83c9a5d4044ebc9901725605d"
BASE_URL = "http://api.marketstack.com/v2/eod"

# Test just 2-3 Indian NSE symbols
symbols = "RELIANCE.NS,HDFCBANK.NS,TCS.NS"

params = {
    "access_key": API_KEY,
    "symbols": symbols,
    "limit": 3,
    "sort": "DESC"
}

print("🔍 Testing Marketstack API...\n")

try:
    response = requests.get(BASE_URL, params=params, timeout=10)
    print("✅ API status code:", response.status_code)
    
    if response.status_code != 200:
        print("❌ Error:", response.text)
    else:
        data = response.json()
        print("\n✅ Raw Response:")
        print(json.dumps(data, indent=2))

        if "data" in data and len(data["data"]) > 0:
            print("\n✅ Successfully fetched stock data!")
            for item in data["data"]:
                print(f"{item['symbol']} | {item['date']} | Close: {item['close']}")
        else:
            print("⚠️ No data returned. Check if these symbols are supported.")
except Exception as e:
    print("❌ Exception:", e)
