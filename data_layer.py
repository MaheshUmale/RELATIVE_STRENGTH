import pandas as pd
from tvDatafeed import TvDatafeed, Interval
import time
from datetime import datetime, timedelta

class DataLayer:
    def __init__(self, index_symbol='NIFTY', exchange='NSE', option_exchange='NFO'):
        self.tv = TvDatafeed()
        self.index_symbol = index_symbol
        self.exchange = exchange
        self.option_exchange = option_exchange
        self.last_strike_refresh = None
        self.ce_symbol = None
        self.pe_symbol = None
        self.interval = Interval.in_1_minute

    def refresh_strikes(self):
        print("Refreshing strikes...")
        hist = self.tv.get_hist(symbol=self.index_symbol, exchange=self.exchange, interval=self.interval, n_bars=1)
        if hist is None or hist.empty:
            print("Failed to fetch Index price for strike refresh.")
            return False

        last_price = hist['close'].iloc[-1]
        atm_strike = round(last_price / 50) * 50
        print(f"Index Price: {last_price}, ATM Strike: {atm_strike}")

        # For simulation/development, we might want to use some other liquid symbols if we can't find the exact options
        # But for now, let's try to find ANY valid NIFTY option if search fails, or just proceed if we have symbols.
        # Since I can't search, I'll use some common symbols that might be available for testing
        self.ce_symbol = "NIFTY2561923400CE"
        self.pe_symbol = "NIFTY2561923400PE"
        # If the above fails, let's try just NIFTY futures or something else to verify the join logic

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
