import requests
import json
from datetime import datetime

def test_expiry():
    symbol = "NIFTY"
    url = f"https://www.nseindia.com/api/option-chain-contract-info?symbol={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # NSE requires a cookie session sometimes. Let's try to get it from the home page first if direct fails.
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers) # Set cookies

    try:
        response = session.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            expiry_dates = data.get("expiryDates", [])
            if expiry_dates:
                latest_expiry = expiry_dates[0]
                print(f"Latest Expiry: {latest_expiry}")
                # Parse "30-Mar-2026"
                dt = datetime.strptime(latest_expiry, "%d-%b-%Y")
                formatted = dt.strftime("%y%m%d")
                print(f"Formatted Expiry: {formatted}")
            else:
                print("No expiry dates found.")
        else:
            print(f"Failed to fetch data: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_expiry()
