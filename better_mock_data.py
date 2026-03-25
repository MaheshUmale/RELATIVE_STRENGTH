import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class BetterMockDataLayer:
    def __init__(self, index_symbol='NIFTY', ce_symbol='NIFTY_CE', pe_symbol='NIFTY_PE'):
        self.index_symbol = index_symbol
        self.ce_symbol = ce_symbol
        self.pe_symbol = pe_symbol

    def generate_mock_data(self, n_bars=1000):
        # Generate 1-minute timestamps (Monday-Friday, 9:15-15:30)
        start_time = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)
        timestamps = []
        current = start_time
        for _ in range(n_bars):
            if current.time() >= datetime.strptime('15:30', '%H:%M').time():
                current = (current + timedelta(days=1)).replace(hour=9, minute=15)
                # Skip weekends
                while current.weekday() >= 5:
                    current = (current + timedelta(days=1)).replace(hour=9, minute=15)
            timestamps.append(current)
            current += timedelta(minutes=1)

        # Base Index Price
        index_price = 23400 + np.cumsum(np.random.normal(0, 3, n_bars))

        # CE/PE Prices correlated with Index
        ce_price = 200 + (index_price - index_price[0]) * 0.4 + np.cumsum(np.random.normal(0, 1, n_bars))
        pe_price = 200 - (index_price - index_price[0]) * 0.4 + np.cumsum(np.random.normal(0, 1, n_bars))

        # Volume (with occasional spikes)
        idx_vol = np.random.randint(1000, 5000, n_bars).astype(float)
        ce_vol = np.random.randint(500, 2000, n_bars).astype(float)
        pe_vol = np.random.randint(500, 2000, n_bars).astype(float)

        # Induce some signals
        # A swing low takes 'swing_window' candles to be confirmed.
        # Let's induce confirmed swings first.
        swing_win = 7
        for i in range(100, n_bars, 200):
            # Induce a swing low at i
            # index_price[i] is already low-ish
            index_price[i-swing_win:i+swing_win+1] = np.linspace(index_price[i-swing_win], index_price[i], swing_win+1).tolist() + np.linspace(index_price[i], index_price[i+swing_win], swing_win+1).tolist()[1:]
            ce_price[i-swing_win:i+swing_win+1] = np.linspace(ce_price[i-swing_win], ce_price[i], swing_win+1).tolist() + np.linspace(ce_price[i], ce_price[i+swing_win], swing_win+1).tolist()[1:]

            # Now at i + 100, we trigger a setup using the swing at i
            setup_idx = i + 100
            if setup_idx + 10 < n_bars:
                # Index breach
                index_price[setup_idx] = index_price[i] - 10
                # CE holds
                ce_price[setup_idx] = ce_price[i] + 5
                # PE fails to break high
                pe_price[setup_idx] = pe_price[setup_idx-1] - 5

                # Volume spike for trigger
                trigger_idx = setup_idx + 2
                ce_vol[trigger_idx] *= 4
                ce_price[trigger_idx] = ce_price[trigger_idx-1] + 10

        data = {
            'idx_open': index_price - 1,
            'idx_high': index_price + 2,
            'idx_low': index_price - 2,
            'idx_close': index_price,
            'idx_volume': idx_vol,

            'ce_open': ce_price - 1,
            'ce_high': ce_price + 2,
            'ce_low': ce_price - 2,
            'ce_close': ce_price,
            'ce_volume': ce_vol,

            'pe_open': pe_price - 1,
            'pe_high': pe_price + 2,
            'pe_low': pe_price - 2,
            'pe_close': pe_price,
            'pe_volume': pe_vol
        }

        df = pd.DataFrame(data, index=timestamps)
        df.index.name = 'datetime'
        return df

if __name__ == "__main__":
    bmdl = BetterMockDataLayer()
    df = bmdl.generate_mock_data(500)
    print(df.head())
    print(f"Total rows: {len(df)}")
