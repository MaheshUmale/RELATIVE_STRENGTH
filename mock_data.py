import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MockDataLayer:
    def __init__(self, index_symbol='NIFTY', expiry_str='260330', atm_strike=23400):
        self.index_symbol = index_symbol
        self.ce_symbol = f"{index_symbol}{expiry_str}C{atm_strike}"
        self.pe_symbol = f"{index_symbol}{expiry_str}P{atm_strike}"

    def generate_mock_data(self, n_bars=100):
        # Generate 1-minute timestamps
        end_time = datetime.now().replace(second=0, microsecond=0)
        timestamps = [end_time - timedelta(minutes=i) for i in range(n_bars)][::-1]

        # Base Index Price
        index_price = 23400 + np.cumsum(np.random.normal(0, 5, n_bars))

        # Mocking a setup where Index makes a new low, but CE holds
        # Let's say at bar 80, index makes a new low
        # index_lows = index_price - 10

        data = {
            'idx_open': index_price - 2,
            'idx_high': index_price + 5,
            'idx_low': index_price - 5,
            'idx_close': index_price,
            'idx_volume': np.random.randint(1000, 5000, n_bars),

            'ce_open': (index_price - 23000) * 0.5 - 2,
            'ce_high': (index_price - 23000) * 0.5 + 5,
            'ce_low': (index_price - 23000) * 0.5 - 5,
            'ce_close': (index_price - 23000) * 0.5,
            'ce_volume': np.random.randint(500, 2000, n_bars),

            'pe_open': (23800 - index_price) * 0.5 - 2,
            'pe_high': (23800 - index_price) * 0.5 + 5,
            'pe_low': (23800 - index_price) * 0.5 - 5,
            'pe_close': (23800 - index_price) * 0.5,
            'pe_volume': np.random.randint(500, 2000, n_bars)
        }

        df = pd.DataFrame(data, index=timestamps)
        df.index.name = 'datetime'
        return df

if __name__ == "__main__":
    mdl = MockDataLayer()
    df = mdl.generate_mock_data(50)
    print(df.head())
    print(f"Total rows: {len(df)}")
