import pandas as pd
import requests
from tvDatafeed import TvDatafeed, Interval
import time
from datetime import datetime, timedelta

class DataLayer:
    def __init__(self, index_symbol='NIFTY', exchange='NSE', option_exchange='NSE'):
        self.tv = TvDatafeed()
        self.session = requests.Session()
        self.index_symbol = index_symbol
        self.exchange = exchange
        self.option_exchange = option_exchange
        self.last_strike_refresh = None
        self.ce_symbol = None
        self.pe_symbol = None
        self.interval = Interval.in_1_minute

    def get_latest_expiry(self):
        """Fetch latest expiry date from NSE API and format as YYMMDD."""
        url = f"https://www.nseindia.com/api/option-chain-contract-info?symbol={self.index_symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "*/*",
        }
        try:
            # Try getting cookies from NSE home page first
            self.session.get("https://www.nseindia.com", headers=headers, timeout=5)
            response = self.session.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                expiry_dates = data.get("expiryDates", [])
                if expiry_dates:
                    dt = datetime.strptime(expiry_dates[0], "%d-%b-%Y")
                    return dt.strftime("%y%m%d")
        except Exception as e:
            print(f"Error fetching live expiry: {e}")

        return "260330" # Default fallback

    def refresh_strikes(self):
        """
        Refresh ATM/ITM strikes based on current Index price and live expiry.
        Naming Format: INDEX_SYM + YYMMDD + C/P + STRIKE (e.g., NIFTY260330C23400)
        """
        print("Refreshing strikes...")
        expiry_str = self.get_latest_expiry()
        print(f"Using Expiry: {expiry_str}")
        hist = self.tv.get_hist(symbol=self.index_symbol, exchange=self.exchange, interval=self.interval, n_bars=1)
        if hist is None or hist.empty:
            print("Failed to fetch Index price for strike refresh. Using current prices as fallback.")
            last_price = 23400 # Fallback
        else:
            last_price = hist['close'].iloc[-1]

        atm_strike = int(round(last_price / 50) * 50)
        print(f"Index Price: {last_price}, ATM Strike: {atm_strike}")

        # Update symbols with user-defined format: NIFTY260330C23400
        self.ce_symbol = f"{self.index_symbol}{expiry_str}C{atm_strike}"
        self.pe_symbol = f"{self.index_symbol}{expiry_str}P{atm_strike}"

        if self.ce_symbol and self.pe_symbol:
            self.last_strike_refresh = datetime.now()
            print(f"Refreshed Symbols - CE: {self.ce_symbol}, PE: {self.pe_symbol}")
            return True
        else:
            print("Failed to find appropriate CE or PE symbols.")
            return False

    def get_synchronized_data(self, n_bars=100):
        # Check if refresh is needed (every 30 mins)
        if self.last_strike_refresh is None or (datetime.now() - self.last_strike_refresh) > timedelta(minutes=30):
            if not self.refresh_strikes():
                return None

        # Fetch all three streams
        index_df = self.tv.get_hist(symbol=self.index_symbol, exchange=self.exchange, interval=self.interval, n_bars=n_bars)
        ce_df = self.tv.get_hist(symbol=self.ce_symbol, exchange=self.option_exchange, interval=self.interval, n_bars=n_bars)
        pe_df = self.tv.get_hist(symbol=self.pe_symbol, exchange=self.option_exchange, interval=self.interval, n_bars=n_bars)

        if index_df is None or ce_df is None or pe_df is None:
            print("Failed to fetch one or more data streams.")
            return None

        # Prepare for join
        index_df = index_df[['open', 'high', 'low', 'close', 'volume']].rename(columns=lambda x: f'idx_{x}')
        ce_df = ce_df[['open', 'high', 'low', 'close', 'volume']].rename(columns=lambda x: f'ce_{x}')
        pe_df = pe_df[['open', 'high', 'low', 'close', 'volume']].rename(columns=lambda x: f'pe_{x}')

        # Inner join on timestamps
        merged_df = index_df.join(ce_df, how='inner').join(pe_df, how='inner')

        return merged_df

if __name__ == "__main__":
    dl = DataLayer()
    data = dl.get_synchronized_data(n_bars=50)
    if data is not None:
        print("Synchronized Data (First 5 rows):")
        print(data.head())
        print(f"Total rows: {len(data)}")
    else:
        print("Failed to get synchronized data.")
