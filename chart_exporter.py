import matplotlib.pyplot as plt
import os
import pandas as pd

class ChartExporter:
    def __init__(self, output_dir='trade_charts'):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def export_trade_chart(self, trade, df):
        """
        Export a chart for a single trade showing Entry, SL, TP1, and Exit.
        df should contain the OHLCV data for the trade duration (+ some buffer).
        """
        # Define window (from 30 mins before entry to 30 mins after exit)
        start_time = trade['entry_time'] - pd.Timedelta(minutes=30)
        exit_time = trade.get('exit_time', df.index[-1])
        end_time = exit_time + pd.Timedelta(minutes=30)

        trade_df = df.loc[start_time:end_time]
        if trade_df.empty:
            print("No data found for the trade period.")
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), gridspec_kw={'height_ratios': [3, 1]})

        # Plot Option Price (CE or PE - here we use CE as target in spec)
        ax1.plot(trade_df.index, trade_df['ce_close'], label='Option Price', color='blue', alpha=0.6)

        # Mark Entry
        ax1.scatter(trade['entry_time'], trade['entry_price'], color='green', marker='^', s=100, label='Entry')
        ax1.annotate(f'Entry: {trade["entry_price"]:.2f}', (trade['entry_time'], trade['entry_price']), textcoords="offset points", xytext=(0,10), ha='center', color='green')

        # Mark Stop Loss
        ax1.axhline(trade['stop_loss'], color='red', linestyle='--', alpha=0.5, label='SL')

        # Mark Target 1 (TP1)
        ax1.axhline(trade['target_1'], color='orange', linestyle='--', alpha=0.5, label='TP1 (2R)')

        # Mark Exit
        if 'exit_time' in trade:
            ax1.scatter(trade['exit_time'], trade['exit_price'], color='red', marker='v', s=100, label='Exit')
            ax1.annotate(f'Exit: {trade["exit_price"]:.2f} ({trade["reason"]})', (trade['exit_time'], trade['exit_price']), textcoords="offset points", xytext=(0,-15), ha='center', color='red')

        # Plot Index Price for context
        ax1_idx = ax1.twinx()
        ax1_idx.plot(trade_df.index, trade_df['idx_close'], label='Index Price', color='gray', alpha=0.3, linestyle=':')
        ax1_idx.set_ylabel('Index Price')

        # Plot Volume
        ax2.bar(trade_df.index, trade_df['ce_volume'], color='blue', alpha=0.3, label='Volume')

        # Formatting
        ax1.set_title(f"Trade Analysis - Entry @ {trade['entry_time']}")
        ax1.set_ylabel('Option Price')
        ax1.legend(loc='upper left')
        ax2.set_ylabel('Volume')

        filename = f"trade_{trade['entry_time'].strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath)
        plt.close()
        print(f"Chart exported to {filepath}")

if __name__ == "__main__":
    # Test chart exporter with dummy data
    from better_mock_data import BetterMockDataLayer
    from datetime import datetime, timedelta

    bmdl = BetterMockDataLayer()
    df = bmdl.generate_mock_data(200)

    trade = {
        'entry_time': df.index[50],
        'entry_price': df.iloc[50]['ce_close'],
        'stop_loss': df.iloc[50]['ce_close'] - 10,
        'target_1': df.iloc[50]['ce_close'] + 20,
        'exit_time': df.index[80],
        'exit_price': df.iloc[80]['ce_close'],
        'reason': 'TP1 HIT',
        'risk': 10
    }

    exporter = ChartExporter()
    exporter.export_trade_chart(trade, df)
