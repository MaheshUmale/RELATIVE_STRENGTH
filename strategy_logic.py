import pandas as pd
import numpy as np

class StrategyLogic:
    def __init__(self, swing_window=5):
        self.swing_window = swing_window

    def find_major_swings(self, df, prefix):
        """
        Identify Major Swing Highs and Lows using a trailing window to avoid look-ahead bias.
        A point is a swing low if it's the lowest in the [t-2*window, t] range and was at t-window.
        """
        low_col = f'{prefix}_low'
        high_col = f'{prefix}_high'

        # We detect the swing at 't', but it actually occurred at 't - self.swing_window'
        # To avoid look-ahead bias in backtesting, we mark it at 't' that 't-window' WAS a swing.

        window_size = 2 * self.swing_window + 1

        # Swing Low detection (confirmed after 'window' candles)
        is_min = df[low_col].rolling(window=window_size).apply(
            lambda x: 1 if x.iloc[self.swing_window] == x.min() else 0, raw=False
        )
        # We shift it by 'swing_window' to align the "1" with the candle where it is CONFIRMED
        # No, we should mark the candle where it HAPPENED but only use it AFTER it's confirmed.
        # Actually, for the strategy, we need to know the 'prev_swing_low'.
        # If at candle T, we confirm T-window was a swing low, then 'prev_swing_low' becomes low[T-window].

        df[f'{prefix}_is_swing_low'] = is_min

        # Swing High detection
        is_max = df[high_col].rolling(window=window_size).apply(
            lambda x: 1 if x.iloc[self.swing_window] == x.max() else 0, raw=False
        )
        df[f'{prefix}_is_swing_high'] = is_max

        df.fillna(0, inplace=True)
        return df

    def detect_phase1_setup(self, df):
        # Conditions:
        # 1. Index breaches previous Major Swing Low
        # 2. CE holds its previous Major Swing Low (current low >= prev swing low)
        # 3. PE fails to break its previous Major Swing High (current high <= prev swing high)

        # Track the MOST RECENT CONFIRMED major swing points
        # When idx_is_swing_low is 1 at time 't', it refers to the low at 't - self.swing_window'
        df['idx_confirmed_swing_low'] = df['idx_low'].shift(self.swing_window).where(df['idx_is_swing_low'] == 1).ffill()
        df['ce_confirmed_swing_low'] = df['ce_low'].shift(self.swing_window).where(df['ce_is_swing_low'] == 1).ffill()
        df['pe_confirmed_swing_high'] = df['pe_high'].shift(self.swing_window).where(df['pe_is_swing_high'] == 1).ffill()

        # Shift to avoid look-ahead. We can only use the confirmed swing from the PREVIOUS candle
        df['idx_prev_swing_low'] = df['idx_confirmed_swing_low'].shift(1)
        df['ce_prev_swing_low'] = df['ce_confirmed_swing_low'].shift(1)
        df['pe_prev_swing_high'] = df['pe_confirmed_swing_high'].shift(1)

        df['setup_valid'] = (
            (df['idx_low'] < df['idx_prev_swing_low']) &
            (df['ce_low'] >= df['ce_prev_swing_low']) &
            (df['pe_high'] <= df['pe_prev_swing_high'])
        ).astype(int)

        return df

    def detect_phase2_trigger(self, df):
        # Conditions:
        # 1. Price Uptick: CE Price > High of candle that formed CE Swing Low
        # 2. Volume Spike: Vol > 1.5 * SMA(20) of volume
        # 3. Candle Health: Close > Open (Bullish)
        # Must occur within 3 candles of Setup

        # High of the candle that formed the most recent confirmed CE swing low
        df['ce_swing_low_high'] = df['ce_high'].shift(self.swing_window).where(df['ce_is_swing_low'] == 1).ffill().shift(1)

        # Volume SMA
        df['ce_vol_sma'] = df['ce_volume'].rolling(window=20).mean()

        # Trigger Condition (at candle close)
        df['trigger_signal'] = (
            (df['ce_close'] > df['ce_swing_low_high']) &
            (df['ce_volume'] > 1.5 * df['ce_vol_sma']) &
            (df['ce_close'] > df['ce_open'])
        ).astype(int)

        # Check if Trigger occurs within 3 candles of Setup
        # We look back at the most recent 3 candles (including current) to see if setup_valid was ever 1
        df['setup_recently_valid'] = df['setup_valid'].rolling(window=3).max().fillna(0)

        df['entry_signal'] = (df['trigger_signal'] == 1) & (df['setup_recently_valid'] == 1)

        return df

if __name__ == "__main__":
    # Test with mock data
    from mock_data import MockDataLayer
    mdl = MockDataLayer()
    df = mdl.generate_mock_data(200)

    sl = StrategyLogic(swing_window=3)
    df = sl.find_major_swings(df, 'idx')
    df = sl.find_major_swings(df, 'ce')
    df = sl.find_major_swings(df, 'pe')
    df = sl.detect_phase1_setup(df)
    df = sl.detect_phase2_trigger(df)

    signals = df[df['entry_signal'] == True]
    print(f"Detected {len(signals)} signals.")
    if not signals.empty:
        print(signals[['idx_close', 'ce_close', 'pe_close', 'entry_signal']].head())
