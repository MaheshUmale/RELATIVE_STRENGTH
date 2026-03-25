import pandas as pd
from better_mock_data import BetterMockDataLayer
from strategy_logic import StrategyLogic
from execution_engine import ExecutionEngine

def run_backtest(n_bars=1000, swing_window=5, vol_sma=20):
    # For now, using Mock Data since live data is unavailable
    mdl = BetterMockDataLayer()
    df = mdl.generate_mock_data(n_bars=n_bars)

    sl = StrategyLogic(swing_window=swing_window)
    df = sl.find_major_swings(df, 'idx')
    df = sl.find_major_swings(df, 'ce')
    df = sl.find_major_swings(df, 'pe')
    df = sl.detect_phase1_setup(df)
    df = sl.detect_phase2_trigger(df)

    # We can override the vol_sma inside detection if needed
    # (The current StrategyLogic uses 20 by default)

    engine = ExecutionEngine()
    for ts, row in df.iterrows():
        engine.process_candle(ts, row)

    return engine.get_summary(), engine.trades

if __name__ == "__main__":
    print("Running Backtest (Last 5 days mock)...")
    # 5 days * 6 hours * 60 minutes ~= 1800 bars
    summary, trades = run_backtest(n_bars=1800)
    print(summary)

    # Simple Optimization Loop Example
    best_pnl = -float('inf')
    best_params = {}

    print("\nStarting Parameter Optimization (Mock)...")
    for window in [3, 5, 7]:
        summary, trades = run_backtest(n_bars=1800, swing_window=window)
        # Extract PnL from summary (simplified)
        if trades:
            total_pnl = sum(t['net_pnl'] for t in trades)
            print(f"Swing Window={window}: Net PnL={total_pnl:.2f}, Trades={len(trades)}")
            if total_pnl > best_pnl:
                best_pnl = total_pnl
                best_params = {'swing_window': window}
        else:
            print(f"Swing Window={window}: No trades.")

    print(f"\nBest Parameters: {best_params}, Best PnL: {best_pnl:.2f}")
