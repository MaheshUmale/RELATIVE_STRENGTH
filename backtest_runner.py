import pandas as pd
from better_mock_data import BetterMockDataLayer
from strategy_logic import StrategyLogic
from execution_engine import ExecutionEngine

def run_backtest(n_bars=1000, swing_window=3):
    mdl = BetterMockDataLayer()
    df = mdl.generate_mock_data(n_bars=n_bars)

    sl = StrategyLogic(swing_window=swing_window)
    for p in ['idx', 'ce', 'pe']:
        df = sl.find_swings(df, p)
        df = sl.find_major_swings(df, p)

    df = sl.detect_signals(df)

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
        if trades:
            total_pnl = sum(t['net_pnl'] for t in trades)
            print(f"Swing Window={window}: Net PnL={total_pnl:.2f}, Trades={len(trades)}")
            if total_pnl > best_pnl:
                best_pnl = total_pnl
                best_params = {'swing_window': window}
        else:
            print(f"Swing Window={window}: No trades.")

    print(f"\nBest Parameters: {best_params}, Best PnL: {best_pnl:.2f}")
