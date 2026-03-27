import pandas as pd
import time
from datetime import datetime, timedelta
from data_layer import DataLayer
from mock_data import MockDataLayer
# from better_mock_data import BetterMockDataLayer
from strategy_logic import StrategyLogic
from execution_engine import ExecutionEngine
from chart_exporter import ChartExporter

class RelativeStrengthBot:
    def __init__(self, use_mock=True, swing_window=3, slippage=0.001):
        if use_mock:
            self.data_layer =  None # BetterMockDataLayer()
        else:
            self.data_layer = DataLayer()

        self.strategy = StrategyLogic(swing_window=swing_window)
        self.execution = ExecutionEngine(slippage=slippage)
        self.use_mock = use_mock

 
    def run(self, n_bars=1000, export_results=True):
        """Standard Backtest Run""" 
        print(f"Starting Relative Strength Bot (Mock={self.use_mock})...")

        if self.use_mock:
            df = self.data_layer.generate_mock_data(n_bars=n_bars)
        else:
            df = self.data_layer.get_synchronized_data(n_bars=n_bars)

        if df is None or df.empty:
            print("Failed to acquire data.")
            return

        # Process and Execute
        df = self.process_data(df)
        for ts, row in df.iterrows():
            self.execution.process_candle(ts, row)

        print("\nBacktest Complete.")
        print(self.execution.get_summary())

        if export_results and self.execution.trades:
            self.export(df)

    def process_data(self, df):
        """Apply strategy logic to the dataframe"""
        # 1. Identify Swings
        for p in ['idx', 'ce', 'pe']:
            df = self.strategy.find_swings(df, p)
            df = self.strategy.find_major_swings(df, p)

        # 2. Detect Signals
        df = self.strategy.detect_signals(df)
        return df

    def export(self, df):
        """Export charts and CSV"""
        print("Exporting results...")
        self.execution.export_trades_to_csv()
        chart_exporter = ChartExporter()
        for trade in self.execution.trades:
            chart_exporter.export_trade_chart(trade, df)

    def run_live(self):
        """Live Run for the entire day"""
        print(f"Starting Live Relative Strength Bot (Mock={self.use_mock})...")

        while True:
            now = datetime.now()
            # 1. Check Operational Hours (9:15 to 15:30 IST)
            current_time = now.time()
            if current_time < pd.to_datetime('09:15').time():
                print(f"Market not open yet ({now}). Waiting...")
                time.sleep(60)
                continue
            if current_time > pd.to_datetime('15:30').time():
                print("Market closed. Ending live run.")
                break

            # 2. Wait for next minute completion
            wait_seconds = 60 - now.second
            print(f"Waiting {wait_seconds}s for next candle...")
            time.sleep(wait_seconds)

            # 3. Fetch latest data (e.g., last 200 bars for swing detection)
            if self.use_mock:
                df = self.data_layer.generate_mock_data(n_bars=200)
            else:
                df = self.data_layer.get_synchronized_data(n_bars=200)

            if df is None or df.empty:
                print("Skipping iteration due to data error.")
                continue

            # 4. Process
            df = self.process_data(df)

            # 5. Execute latest candle
            last_ts = df.index[-1]
            last_row = df.iloc[-1]
            print(f"Processing Live Candle: {last_ts}")
            self.execution.process_candle(last_ts, last_row)

if __name__ == "__main__":
    # Standard backtest on mock data
    bot = RelativeStrengthBot(use_mock=False, swing_window=3)
    bot.run(n_bars=1000)
