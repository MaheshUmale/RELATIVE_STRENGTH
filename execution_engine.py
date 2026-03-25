import pandas as pd
import numpy as np

class ExecutionEngine:
    def __init__(self, slippage=0.001):
        self.slippage = slippage
        self.active_trade = None
        self.trades = []

    def process_candle(self, timestamp, row):
        # Operational Guardrail: Time filter
        current_time = timestamp.time()
        # Hard exit at 15:26 IST
        if current_time >= pd.to_datetime('15:26').time():
            if self.active_trade:
                # Exit at close of current candle
                side = self.active_trade['side'].lower()
                exit_price = row[f'{side}_close']
                self._exit_trade(timestamp, exit_price, "HARD TIME EXIT")
            return

        # No new trades after 15:16 IST
        allow_new_trade = current_time <= pd.to_datetime('15:16').time()

        if self.active_trade:
            self._manage_active_trade(timestamp, row)
        elif allow_new_trade and row.get('entry_signal'):
            self._enter_trade(timestamp, row)

    def _enter_trade(self, timestamp, row):
        side = row['signal_type'] # 'CE' or 'PE'
        if side is None:
            return

        prefix = side.lower()

        # Entry Price (EP): Close of confirmation bar
        ep = row[f'{prefix}_close']

        # Stop Loss (Wall): Minimum Low of the last 3 bars (Lookback window)
        sl = row.get(f'{prefix}_wall_sl', row[f'{prefix}_low'])

        # Risk (R)
        risk = ep - sl

        if risk <= 0:
            return # Invalid risk

        # Max Risk Limit: > 25 points are filtered out
        if risk > 25:
            print(f"[{timestamp}] TRADE REJECTED: Risk {risk:.2f} > 25")
            return

        # Target 1 (Raid): Next Major Resistance (SH Major) or 2:1 RR
        major_sh = row.get(f'{prefix}_last_major_sh', 0)
        target_1 = max(ep + (2 * risk), major_sh)

        self.active_trade = {
            'side': side,
            'entry_time': timestamp,
            'entry_price': ep,
            'stop_loss': sl,
            'risk': risk,
            'target_1': target_1,
            'tp1_hit': False,
            'max_high': row[f'{prefix}_high'],
            'lots': 2
        }
        print(f"[{timestamp}] ENTER {side} TRADE: EP={ep:.2f}, SL={sl:.2f}, R={risk:.2f}, TP1={target_1:.2f}")

    def _manage_active_trade(self, timestamp, row):
        trade = self.active_trade
        prefix = trade['side'].lower()

        low = row[f'{prefix}_low']
        high = row[f'{prefix}_high']
        close = row[f'{prefix}_close']

        # Update max high reached for trailing stop
        if high > trade['max_high']:
            trade['max_high'] = high

        # 1R Profit check for Break-Even
        if not trade.get('be_hit', False) and high >= (trade['entry_price'] + trade['risk']):
            trade['be_hit'] = True
            trade['stop_loss'] = max(trade['stop_loss'], trade['entry_price'])
            print(f"[{timestamp}] 1R REACHED: SL moved to BE ({trade['stop_loss']:.2f})")

        # Invalidation
        if close < trade['stop_loss']:
            self._exit_trade(timestamp, close, "SL HIT (CLOSE)")
            return
        if low <= trade['stop_loss']:
            self._exit_trade(timestamp, trade['stop_loss'], "SL HIT (LOW)")
            return

        # 2. TP1: Hit Target 1
        if not trade['tp1_hit'] and high >= trade['target_1']:
            trade['tp1_hit'] = True
            print(f"[{timestamp}] TP1 HIT: Selling 50% at {trade['target_1']:.2f}.")
            trade['tp1_exit_price'] = trade['target_1']

        # 3. TP2: Trailing Stop
        if trade['tp1_hit']:
            potential_sl = trade['max_high'] - trade['risk']
            if potential_sl > trade['stop_loss']:
                trade['stop_loss'] = potential_sl

            if low <= trade['stop_loss']:
                self._exit_trade(timestamp, trade['stop_loss'], "TRAILING SL HIT")
                return

    def _exit_trade(self, timestamp, exit_price, reason):
        trade = self.active_trade

        # Calculate PnL
        if trade['tp1_hit']:
            c1_pnl = (trade['tp1_exit_price'] - trade['entry_price'])
            c2_pnl = (exit_price - trade['entry_price'])
        else:
            c1_pnl = (exit_price - trade['entry_price'])
            c2_pnl = (exit_price - trade['entry_price'])

        total_pnl = c1_pnl + c2_pnl
        net_pnl = total_pnl - (trade['entry_price'] + exit_price) * self.slippage * 2

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
