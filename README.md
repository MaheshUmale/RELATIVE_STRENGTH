# RELATIVE_STRENGTH

This document serves as a technical specification for an AI Coding Agent to build an automated trading system. The system identifies institutional "absorption" where option premiums refuse to fall despite the Index making new lows (Relative Strength), followed by an aggressive volume-based trigger.

---

## 1. Data Layer & Synchronization
The Agent must use `TvDatafeed` to fetch and align three data streams.

* **Symbols:** * `INDEX_SYM`: Spot Index (e.g., NIFTY).
    * `CE_SYM`: Current ATM/ITM Call Option.
    * `PE_SYM`: Current ATM/ITM Put Option.
* **Timeframe:** 1-minute or 5-minute (User defined).
* **Alignment:** Perform an `inner join` on timestamps. If a timestamp is missing in any of the three streams, the entire row must be discarded to ensure perfect synchronization.

---

## 2. Phase 1: The Setup (Structural Divergence)
The system remains in a "Monitoring" state until these **three** conditions are met simultaneously:

1.  **Index Action:** The Spot Index breaches its previous **Major Swing Low**.
2.  **CE (Target) Action:** The Call Option **holds** its previous **Major Swing Low** (i.e., its current low is $\ge$ previous low). This indicates "Buying Pressure" or Absorption.
3.  **PE (Opposing) Action:** The Put Option **fails** to break its previous **Major Swing High**. This indicates "Selling Pressure" on the hedge, confirming the Index move is likely a "False Break."

---

## 3. Phase 2: The Trigger (Aggression Confirmation)
A "Swing Hold" is only a setup. The **Execution Trigger** occurs only when the bulls show active aggression.

**Trigger Conditions (Must occur within 3 candles of the Setup):**
* **Price Uptick:** CE Price breaks above the `High` of the candle that formed the CE Swing Low.
* **Volume Spike:** The volume of the trigger candle must be $> 1.5 \times$ the **Simple Moving Average (SMA)** of the last 20 volume bars.
* **Candle Health:** The trigger candle must be **Bullish** (Close > Open).



---

## 4. Phase 3: Execution (Entry, SL, & Take Profit)

The Agent manages the trade using a **Two-Contract (or Two-Slice) Logic**:

### A. Entry & Risk Definition
* **Entry Price ($EP$):** Market Buy (2 Lots/Slices) at the **Close** of the Trigger Candle.
* **Stop Loss ($SL$):** Fixed at the **Low** of the CE Swing that held.
* **Initial Risk ($R$):** $R = EP - SL$.
* **Invalidation:** If at any point the CE price closes below the $SL$, the setup is dead. **Exit 100% immediately.**

### B. Take Profit 1 (Target 1)
* **Level:** $TP1 = EP + (2 \times R)$.
* **Action:** Sell **50%** of the position (1 Lot).
* **Safety Adjustment:** Move the $SL$ for the remaining 50% to the **Entry Price (Break-Even)**.

### C. Take Profit 2 (Trailing)
* **Level:** Dynamic Trailing Stop.
* **Logic:** The $SL$ trails at a distance of $1R$ from the **highest high** reached after $TP1$ was hit.
* **Formula:** $SL_{trail} = \text{Current High} - R$.
* **Rule:** The $SL_{trail}$ can only move **upwards**, never downwards.

---

## 5. PnL & Logic Calculations
The Agent must log and calculate performance based on the following logic:

| Component | Variable/Formula |
| :--- | :--- |
| **Trade Risk** | $R = \text{Entry} - \text{Swing Low}$ |
| **Contract 1 PnL** | $2 \times R$ |
| **Contract 2 PnL** | $\text{Exit Price} - \text{Entry Price}$ |
| **Total PnL** | $(\text{C1 PnL}) + (\text{C2 PnL}) - \text{Slippage}$ |
| **Invalidation Exit** | If $\text{Price} < \text{Swing Low}$ then $\text{Result} = -1R$ (per contract) |

### Logic Pseudo-code for Agent:
```python
# TRIGGER LOGIC
if (index_low < prev_index_swing_low) and (ce_low >= prev_ce_swing_low):
    if pe_high <= prev_pe_swing_high: # SETUP VALID
        if current_ce_price > prev_candle_high and current_vol > (1.5 * sma_vol):
            # EXECUTE ENTRY
            entry_p = close
            sl_p = ce_low
            risk = entry_p - sl_p
            target_1 = entry_p + (2 * risk)
```

---

## 6. Operational Guardrails
* **Time Filter:** Do not initiate new setups after 14:45 IST (Intraday volatility risk).
* **Slippage Buffer:** Add a 0.1% buffer to PnL calculations to account for real-world fills in liquid Indian Option markets.
* **Strike Refresh:** Re-fetch ATM/ITM symbols every 30 minutes to ensure the Agent is always tracking the "Active" contract.

---

## 7. Implementation Overview
The system is implemented across several Python modules for modularity and maintainability:

- **`data_layer.py`**: Handles data fetching and synchronization using `tvDatafeed`. Contains `DataLayer` and `MockDataLayer`.
- **`strategy_logic.py`**: Implements the three-phase strategy logic (Swing Detection, Setup, and Trigger).
- **`execution_engine.py`**: Manages trade entries, exits (TP1/TP2), trailing stops, and PnL calculations with slippage.
- **`relative_strength_bot.py`**: The main entry point that integrates all components into a functional bot.
- **`backtest_runner.py`**: A utility script for running backtests and parameter optimization on historical data.

## 8. Usage Instructions
1. **Dependencies:** Install requirements via:
   ```bash
   pip install pandas rookiepy websocket-client requests
   pip install --upgrade --no-cache-dir git+https://github.com/MaheshUmale/TvDataFeed_modified.git
   ```
2. **Configuration:** Set `use_mock=False` in `relative_strength_bot.py` for live data (requires browser cookies).
3. **Execution:** Run `python3 relative_strength_bot.py` to start the bot.
4. **Backtest:** Run `python3 backtest_runner.py` to evaluate performance on mock or historical data.
5. **Live Mode:** To keep the bot running for the entire day, the `run_live()` method in `RelativeStrengthBot` can be used. It waits for each 1-minute candle completion and processes it in real-time.

## 9. Live Test Simulation
To verify the bot's behavior for a complete day candle-by-candle, use:
```bash
python3 live_test_sim.py
```
This script simulates a full trading day (9:15 to 15:30 IST) by iterating through historical/mock data one bar at a time, exactly as it would in a live environment.

## 10. Backtest Results (Mock Data)
Initial backtests on a 5-day mock dataset with a `swing_window` of 7 showed:
- **Total PnL:** -64.07 (on mock volatility)
- **Win Rate:** ~30% (dependent on market conditions)
- **Max PnL:** +71.48
- **Min PnL:** -40.01

See `NEXT_STEPS.md` for optimization recommendations.
