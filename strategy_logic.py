import pandas as pd
import numpy as np

class StrategyLogic:
    def __init__(self, swing_window=3, major_swing_window=41):
        self.swing_window = swing_window
        self.major_swing_window = major_swing_window

    def find_swings(self, df, prefix, window=None):
        """
        Identify Swing Highs and Lows using a centered window to find local extrema,
        then shifting it to make it 'lagging' and avoid look-ahead bias.
        As per strategy: Bar i-3 is SH if it's max in [i-6, i].
        """
        if window is None:
            window = self.swing_window

        # For a 3-bar lookback, window size is 7 (i-6 to i, with i-3 in middle)
        window_size = 2 * window + 1
        low_col = f'{prefix}_low'
        high_col = f'{prefix}_high'

        # Detect local extrema at 't - window'
        is_min = df[low_col].rolling(window=window_size, center=True).apply(
            lambda x: 1 if x.iloc[window] == x.min() else 0, raw=False
        )
        is_max = df[high_col].rolling(window=window_size, center=True).apply(
            lambda x: 1 if x.iloc[window] == x.max() else 0, raw=False
        )

        # Shift the results so that at index 'i', we know if 'i - window' was a swing.
        # Rolling with center=True already 'looks ahead'.
        # To make it available only at 'i', we shift by 'window'.
        df[f'{prefix}_is_swing_low'] = is_min.shift(window)
        df[f'{prefix}_is_swing_high'] = is_max.shift(window)

        # Track last confirmed swing levels
        df[f'{prefix}_last_sl'] = df[low_col].shift(window).where(df[f'{prefix}_is_swing_low'] == 1).ffill()
        df[f'{prefix}_last_sh'] = df[high_col].shift(window).where(df[f'{prefix}_is_swing_high'] == 1).ffill()

        # Wall SL: Minimum Low of the last 3 bars (including current bar)
        df[f'{prefix}_wall_sl'] = df[low_col].rolling(window=3).min()

        return df

    def find_major_swings(self, df, prefix):
        window = self.major_swing_window
        window_size = 2 * window + 1
        low_col = f'{prefix}_low'
        high_col = f'{prefix}_high'

        is_min = df[low_col].rolling(window=window_size, center=True).apply(
            lambda x: 1 if x.iloc[window] == x.min() else 0, raw=False
        )
        is_max = df[high_col].rolling(window=window_size, center=True).apply(
            lambda x: 1 if x.iloc[window] == x.max() else 0, raw=False
        )

        df[f'{prefix}_is_major_sl'] = is_min.shift(window)
        df[f'{prefix}_is_major_sh'] = is_max.shift(window)

        df[f'{prefix}_last_major_sl'] = df[low_col].shift(window).where(df[f'{prefix}_is_major_sl'] == 1).ffill()
        df[f'{prefix}_last_major_sh'] = df[high_col].shift(window).where(df[f'{prefix}_is_major_sh'] == 1).ffill()

        return df

    def apply_indicators(self, df):
        # 1. 9 EMA for Index
        df['idx_ema9'] = df['idx_close'].ewm(span=9, adjust=False).mean()

        # 2. RS Context (10-bar rolling)
        for p in ['idx', 'ce', 'pe']:
            low_min = df[f'{p}_low'].rolling(window=10).min()
            df[f'{p}_move'] = (df[f'{p}_close'] - low_min) / (low_min + 1e-9)

        df['ce_rs_divergence'] = df['ce_move'] > df['idx_move']
        df['pe_rs_divergence'] = df['pe_move'] > df['idx_move']

        return df

    def detect_signals(self, df):
        df = self.apply_indicators(df)

        # Time Filter: 9:20 AM to 3:16 PM IST
        # Assuming df index is datetime
        df['time_valid'] = (df.index.time >= pd.to_datetime('09:20').time()) & \
                           (df.index.time <= pd.to_datetime('15:16').time())

        # Bullish Signal (CE Buy)
        # 1. Trend: Index > 9 EMA
        # 2. RS: CE positive RS vs Index
        # 3. Paired Breakout: CE crosses last SH, PE breaks last SL (3-bar buffer)

        ce_cross_sh = (df['ce_close'] > df['ce_last_sh']) & (df['ce_close'].shift(1) <= df['ce_last_sh'].shift(1))
        # PE breaks below last SL within a 3-bar buffer
        pe_break_sl = (df['pe_close'] < df['pe_last_sl']).rolling(window=4).max().fillna(0).astype(bool)

        df['bullish_signal'] = (
            df['time_valid'] &
            (df['idx_close'] > df['idx_ema9']) &
            df['ce_rs_divergence'] &
            ce_cross_sh &
            pe_break_sl
        )

        # Bearish Signal (PE Buy)
        pe_cross_sh = (df['pe_close'] > df['pe_last_sh']) & (df['pe_close'].shift(1) <= df['pe_last_sh'].shift(1))
        ce_break_sl = (df['ce_close'] < df['ce_last_sl']).rolling(window=4).max().fillna(0).astype(bool)

        df['bearish_signal'] = (
            df['time_valid'] &
            (df['idx_close'] < df['idx_ema9']) &
            df['pe_rs_divergence'] &
            pe_cross_sh &
            ce_break_sl
        )

        # Entry signal for bot
        df['entry_signal'] = df['bullish_signal'] | df['bearish_signal']
        # Map back for execution engine
        df['signal_type'] = np.where(df['bullish_signal'], 'CE', np.where(df['bearish_signal'], 'PE', None))

        return df

if __name__ == "__main__":
    # Minimal test
    from better_mock_data import BetterMockDataLayer
    mdl = BetterMockDataLayer()
    df = mdl.generate_mock_data(500)

    sl = StrategyLogic()
    for p in ['idx', 'ce', 'pe']:
        df = sl.find_swings(df, p)
        df = sl.find_major_swings(df, p)

    df = sl.detect_signals(df)
    print(f"Signals detected: {df['entry_signal'].sum()}")
    if df['entry_signal'].any():
        print(df[df['entry_signal']][['signal_type', 'ce_close', 'pe_close']])
