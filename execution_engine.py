import pandas as pd

class ExecutionEngine:
    def __init__(self, slippage=0.001):
        self.slippage = slippage
        self.active_trade = None
        self.trades = []

    def process_candle(self, timestamp, row):
        # Operational Guardrail: Time filter (no new setups after 14:45 IST)
        # Assuming IST is UTC+5:30. But for simplicity, we'll check the hour/minute
        current_time = timestamp.time()
        allow_new_trade = current_time < pd.to_datetime('14:45').time()

        if self.active_trade:
            self._manage_active_trade(timestamp, row)
        elif allow_new_trade and row['entry_signal']:
            self._enter_trade(timestamp, row)

    def _enter_trade(self, timestamp, row):
        # Entry Price (EP): Close of trigger candle
        ep = row['ce_close']
        # Stop Loss (SL): Low of the CE Swing that held
        sl = row['ce_prev_swing_low']
        # Risk (R)
        risk = ep - sl

        if risk <= 0:
            return # Invalid risk

        self.active_trade = {
            'entry_time': timestamp,
            'entry_price': ep,
            'stop_loss': sl,
            'risk': risk,
            'target_1': ep + (2 * risk),
            'tp1_hit': False,
            'max_high': row['ce_high'],
            'lots': 2
        }
        print(f"[{timestamp}] ENTER TRADE: EP={ep:.2f}, SL={sl:.2f}, R={risk:.2f}, TP1={self.active_trade['target_1']:.2f}")

    def _manage_active_trade(self, timestamp, row):
        trade = self.active_trade
        ce_low = row['ce_low']
        ce_high = row['ce_high']
        ce_close = row['ce_close']

        # Update max high reached for trailing stop
        if ce_high > trade['max_high']:
            trade['max_high'] = ce_high

        # 1. Invalidation: Close below SL
        if ce_close < trade['stop_loss']:
            self._exit_trade(timestamp, ce_close, "SL HIT")
            return

        # 2. TP1: Hit Target 1
        if not trade['tp1_hit'] and ce_high >= trade['target_1']:
            trade['tp1_hit'] = True
            print(f"[{timestamp}] TP1 HIT: Selling 1 lot at {trade['target_1']:.2f}. Moving SL to BE ({trade['entry_price']:.2f})")
            trade['tp1_exit_price'] = trade['target_1']
            trade['stop_loss'] = trade['entry_price'] # Move SL to Break-Even

        # 3. TP2: Trailing Stop
        if trade['tp1_hit']:
            # Formula: SL_trail = Current High - R (can only move up)
            potential_sl = trade['max_high'] - trade['risk']
            if potential_sl > trade['stop_loss']:
                trade['stop_loss'] = potential_sl
                # print(f"[{timestamp}] Trailing SL updated to {trade['stop_loss']:.2f}")

            if ce_low <= trade['stop_loss']:
                self._exit_trade(timestamp, trade['stop_loss'], "TRAILING SL HIT")
                return

    def _exit_trade(self, timestamp, exit_price, reason):
        trade = self.active_trade

        # Calculate PnL
        # Contract 1 PnL
        if trade['tp1_hit']:
            c1_pnl = (trade['tp1_exit_price'] - trade['entry_price'])
            c2_pnl = (exit_price - trade['entry_price'])
        else:
            # If exited before TP1, both lots exited at exit_price
            c1_pnl = (exit_price - trade['entry_price'])
            c2_pnl = (exit_price - trade['entry_price'])

        total_pnl = c1_pnl + c2_pnl
        # Apply slippage (0.1% per contract on entry and exit)
        total_slippage = (trade['entry_price'] + exit_price) * self.slippage * 2
        net_pnl = total_pnl - total_slippage

        trade['exit_time'] = timestamp
        trade['exit_price'] = exit_price
        trade['net_pnl'] = net_pnl
        trade['reason'] = reason

        self.trades.append(trade)
        print(f"[{timestamp}] EXIT TRADE ({reason}): Price={exit_price:.2f}, Net PnL={net_pnl:.2f}")
        self.active_trade = None

    def get_summary(self):
        if not self.trades:
            return "No trades executed."

        df = pd.DataFrame(self.trades)
        total_pnl = df['net_pnl'].sum()
        win_rate = (df['net_pnl'] > 0).mean() * 100

        summary = (
            f"--- Trading Summary ---\n"
            f"Total Trades: {len(df)}\n"
            f"Total PnL: {total_pnl:.2f}\n"
            f"Win Rate: {win_rate:.2f}%\n"
            f"Max PnL: {df['net_pnl'].max():.2f}\n"
            f"Min PnL: {df['net_pnl'].min():.2f}\n"
        )
        return summary

    def export_trades_to_csv(self, filename='trades.csv'):
        if not self.trades:
            print("No trades to export.")
            return

        df = pd.DataFrame(self.trades)
        df.to_csv(filename, index=False)
        print(f"Trades exported to {filename}")

if __name__ == "__main__":
    # Test with logic results
    from mock_data import MockDataLayer
    from strategy_logic import StrategyLogic

    mdl = MockDataLayer()
    df = mdl.generate_mock_data(500)

    # Force a signal for testing
    df.loc[df.index[100], 'entry_signal'] = True
    df.loc[df.index[100], 'ce_prev_swing_low'] = df.loc[df.index[100], 'ce_close'] - 10
    # Also need to make sure subsequent candles don't immediately hit SL
    df.loc[df.index[101:], 'ce_low'] = df.loc[df.index[100], 'ce_close'] - 5
    df.loc[df.index[150], 'ce_high'] = df.loc[df.index[100], 'ce_close'] + 50 # Hit TP1

    sl = StrategyLogic()
    engine = ExecutionEngine()

    for ts, row in df.iterrows():
        engine.process_candle(ts, row)

    print(engine.get_summary())
