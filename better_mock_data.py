# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta

# class BetterMockDataLayer:
#     def __init__(self, index_symbol='NIFTY', ce_symbol='NIFTY_CE', pe_symbol='NIFTY_PE'):
#         self.index_symbol = index_symbol
#         self.ce_symbol = ce_symbol
#         self.pe_symbol = pe_symbol

#     def generate_mock_data(self, n_bars=1000):
#         # Generate 1-minute timestamps (Monday-Friday, 9:15-15:30)
#         start_time = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)
#         timestamps = []
#         current = start_time
#         for _ in range(n_bars):
#             if current.time() >= datetime.strptime('15:30', '%H:%M').time():
#                 current = (current + timedelta(days=1)).replace(hour=9, minute=15)
#                 # Skip weekends
#                 while current.weekday() >= 5:
#                     current = (current + timedelta(days=1)).replace(hour=9, minute=15)
#             timestamps.append(current)
#             current += timedelta(minutes=1)

#         # Base Index Price (Random walk with some trend)
#         index_price = 23400 + np.cumsum(np.random.normal(0.2, 3, n_bars))

#         # CE/PE Prices correlated with Index
#         ce_price = 200 + (index_price - index_price[0]) * 0.4 + np.cumsum(np.random.normal(0, 1, n_bars))
#         pe_price = 200 - (index_price - index_price[0]) * 0.4 + np.cumsum(np.random.normal(0, 1, n_bars))

#         # Ensure prices are positive
#         ce_price = np.maximum(ce_price, 10)
#         pe_price = np.maximum(pe_price, 10)

#         # Volume
#         idx_vol = np.random.randint(1000, 5000, n_bars).astype(float)
#         ce_vol = np.random.randint(500, 2000, n_bars).astype(float)
#         pe_vol = np.random.randint(500, 2000, n_bars).astype(float)

#         # Induced Signals for Testing
#         # Bullish: Idx > EMA, CE RS+, CE cross SH, PE break SL
#         # Let's induce one at bar 200
#         if n_bars > 250:
#             i = 200
#             # Induce a CE swing high at i-10
#             ce_price[i-15:i-5] = [180, 185, 190, 195, 200, 195, 190, 185, 180, 175]
#             # Induce a PE swing low at i-10
#             pe_price[i-15:i-5] = [220, 215, 210, 205, 200, 205, 210, 215, 220, 225]

#             # Setup for i
#             index_price[i-20:i+1] = np.linspace(index_price[i-20], index_price[i-20]+50, 21) # Idx Trending Up
#             ce_price[i] = 205 # Crosses 200 (SH)
#             pe_price[i] = 195 # Breaks 200 (SL)

#             # RS Context: ensure OptMove > IdxMove
#             # IdxMove: (Idx_close - Idx_low_min) / Idx_low_min
#             # We'll just force it by bumping ce_price a bit more
#             ce_price[i-10:i+1] += 5

#         # Bearish: Idx < EMA, PE RS+, PE cross SH, CE break SL
#         # Let's induce one at bar 400
#         if n_bars > 450:
#             i = 400
#             # Induce a PE swing high at i-10
#             pe_price[i-15:i-5] = [180, 185, 190, 195, 200, 195, 190, 185, 180, 175]
#             # Induce a CE swing low at i-10
#             ce_price[i-15:i-5] = [220, 215, 210, 205, 200, 205, 210, 215, 220, 225]

#             # Setup for i
#             index_price[i-20:i+1] = np.linspace(index_price[i-20], index_price[i-20]-50, 21) # Idx Trending Down
#             pe_price[i] = 205 # Crosses 200 (SH)
#             ce_price[i] = 195 # Breaks 200 (SL)

#             # RS Context
#             pe_price[i-10:i+1] += 5

#         data = {
#             'idx_open': index_price - 1,
#             'idx_high': index_price + 2,
#             'idx_low': index_price - 2,
#             'idx_close': index_price,
#             'idx_volume': idx_vol,

#             'ce_open': ce_price - 1,
#             'ce_high': ce_price + 2,
#             'ce_low': ce_price - 2,
#             'ce_close': ce_price,
#             'ce_volume': ce_vol,

#             'pe_open': pe_price - 1,
#             'pe_high': pe_price + 2,
#             'pe_low': pe_price - 2,
#             'pe_close': pe_price,
#             'pe_volume': pe_vol
#         }

#         df = pd.DataFrame(data, index=timestamps)
#         df.index.name = 'datetime'
#         return df

# if __name__ == "__main__":
#     bmdl = BetterMockDataLayer()
#     df = bmdl.generate_mock_data(500)
#     print(df.head())
#     print(f"Total rows: {len(df)}")
