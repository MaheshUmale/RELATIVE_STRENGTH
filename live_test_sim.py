import pandas as pd
from better_mock_data import BetterMockDataLayer
from relative_strength_bot import RelativeStrengthBot
import time

def run_live_simulation():
    """
    Simulates a complete day of live trading, candle-by-candle.
    """
    print("Initializing Live Simulation (Candle-by-Candle)...")

    # 1. Setup Bot (in mock mode for simulation)
    bot = RelativeStrengthBot(use_mock=True, swing_window=3)

    # 2. Pre-generate a full day of data (375 minutes in a NIFTY session)
    bmdl = BetterMockDataLayer()
    full_day_df = bmdl.generate_mock_data(n_bars=375)

    print(f"Starting simulation for {len(full_day_df)} candles...")

    # 3. Iterate through data one candle at a time, mimicking live loop
    for i in range(50, len(full_day_df)): # Start with enough context for major swings (41*2+1)
        # In a real live loop, we fetch 'n' previous bars at each step
        current_view_df = full_day_df.iloc[:i+1]

        # Process the data slice
        processed_df = bot.process_data(current_view_df)

        # Execute the LATEST candle from the processed slice
        last_ts = processed_df.index[-1]
        last_row = processed_df.iloc[-1]

        bot.execution.process_candle(last_ts, last_row)

        if (i % 50 == 0):
            print(f"Simulated {i}/{len(full_day_df)} candles...")

    print("\nSimulation Complete.")
    print(bot.execution.get_summary())

    if bot.execution.trades:
        bot.export(full_day_df)

if __name__ == "__main__":
    run_live_simulation()
