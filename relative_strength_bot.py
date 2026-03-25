import pandas as pd
import time
from datetime import datetime, timedelta
from data_layer import DataLayer
from mock_data import MockDataLayer
from better_mock_data import BetterMockDataLayer
from strategy_logic import StrategyLogic
from execution_engine import ExecutionEngine
from chart_exporter import ChartExporter

class RelativeStrengthBot:
    def __init__(self, use_mock=True, swing_window=5, slippage=0.001):
        if use_mock:
            self.data_layer = BetterMockDataLayer()
        else:
            self.data_layer = DataLayer()

        self.strategy = StrategyLogic(swing_window=swing_window)
        self.execution = ExecutionEngine(slippage=slippage)
        self.use_mock = use_mock

    def run(self, n_bars=5000, export_results=True):
        print(f"Starting Relative Strength Bot (Mock={self.use_mock})...")

        if self.use_mock:
            df = self.data_layer.generate_mock_data(n_bars=n_bars)
        else:
            df = self.data_layer.get_synchronized_data(n_bars=n_bars)

        if df is None or df.empty:
            print("Failed to acquire data.")
            return

        # 1. Identify Swings
        df = self.strategy.find_major_swings(df, 'idx')
        df = self.strategy.find_major_swings(df, 'ce')
        df = self.strategy.find_major_swings(df, 'pe')

        # 2. Detect Setup and Trigger
        df = self.strategy.detect_phase1_setup(df)
        df = self.strategy.detect_phase2_trigger(df)

        # 3. Execute
        for ts, row in df.iterrows():
            self.execution.process_candle(ts, row)

        print("\nBacktest Complete.")
        print(self.execution.get_summary())

        if export_results and self.execution.trades:
            print("Exporting results...")
            self.execution.export_trades_to_csv()
            chart_exporter = ChartExporter()
            for trade in self.execution.trades:
                chart_exporter.export_trade_chart(trade, df)

if __name__ == "__main__":
    bot = RelativeStrengthBot(use_mock=False, swing_window=5)
    bot.run(n_bars=2000)
