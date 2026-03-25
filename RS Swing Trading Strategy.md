# RS Swing Trading Strategy: Paired Relative Strength Analysis

## 1. Strategy Overview
The **RS Swing Strategy** is a high-conviction momentum and mean-reversion strategy designed for Index Options (Nifty 50 and Bank Nifty). It identifies structural divergences between the Spot Index and Option Premiums (ATM/OTM) to detect leading price action signals.

The core philosophy is **Paired Confirmation**: A trade is only valid when the primary option (e.g., CE) shows aggressive buying (breaking high) *simultaneously* with the counter-option (e.g., PE) showing aggressive selling (breaking low).

---

## 2. Data Requirements & Feeds

### Primary Data Sources:
*   **Spot Index:** Real-time 1-minute OHLC data for NIFTY 50 or BANK NIFTY.
*   **Option Chains:** Real-time OI and LTP for the Nearest Expiry.
*   **Option Premiums:** 1-minute OHLC data for 6 key strikes:
    *   **At-The-Money (ATM):** CE & PE
    *   **Out-of-The-Money (OTM):** CE (+1 Strike) & PE (-1 Strike)
    *   **In-The-Money (ITM):** CE (-1 Strike) & PE (+1 Strike) 

---

## 3. Analysis Mechanism

### A. Swing Identification (Lagging Confirmation)
To eliminate lookahead bias, swings are identified using a **Lookback Window** (Default: 3 bars).
*   **Swing High (SH):** Bar `i-3` is a SH if its high is the maximum in the window `[i-6, i]`.
*   **Swing Low (SL):** Bar `i-3` is a SL if its low is the minimum in the window `[i-6, i]`.
*   **Major Swings:** Detected using a 41-bar window for high-significance structural targets (SMC Raids).

### B. RS Context (Divergence Analysis)
The system compares the relative move of the Option vs. the Index over a rolling 10-bar window:
*   `IdxMove = (Close - LowMin) / LowMin`
*   `OptMove = (Close - LowMin) / LowMin`
*   **RS Divergence:** `OptMove > IdxMove` (Option is recovering faster or holding while index dips).

---

## 4. Signal Generation Logic

### Bullish Signal (CE Buy)
1.  **Trend Filter:** Index Price must be above the **9 EMA**.
2.  **Time Filter:** Entry must occur between 9.20 AM IST to 3.16 PM IST and all open position must be closed before 3.26PM IST.
3.  **RS Context:** CE must show positive Relative Strength vs. the Index.
4.  **Paired Breakout:**
    *   CE Premium crosses its **Last Confirmed Swing High**.
    *   PE Premium **breaks below** its **Last Confirmed Swing Low** (within a 3-bar buffer).

### Bearish Signal (PE Buy)
1.  **Trend Filter:** Index Price must be below the **9 EMA**.
2.  **Time Filter:** Entry must occur between 9.20 AM IST to 3.16 PM IST and all open position must be closed before 3.26PM IST.
3.  **RS Context:** PE must show positive Relative Strength (Rising as Index drops).
4.  **Paired Breakout:**
    *   PE Premium crosses its **Last Confirmed Swing High**.
    *   CE Premium **breaks below** its **Last Confirmed Swing Low**.

---

## 5. Setup & Execution (Entry / SL / TP)

### Setup (Two-Contract Strategy)
*   **Entry:** LTP of the option at the close of the confirmation bar.
*   **Stop Loss (Wall):** Minimum Low of the last 3 bars (Lookback window).
*   **Risk (R):** `Entry - Stop Loss`.
*   **Target 1 (Raid):** Next Major Resistance (SH Major) or a fixed **2:1 Reward-to-Risk (RR)**.

### Risk Management
*   **Break-Even (BE):** Once the premium reaches **1R profit**, the Stop Loss is automatically moved to the **Entry Price**.
*   **Runner (Contract 2):** After T1 is hit, the runner trails the price at a **1R distance** from the trailing high.
*   **Max Risk Limit:** Trades with a calculated risk > 25 points are filtered out.

---

## 6. UI Implementation (/rs-swing)

### Visualization Grid (4x2)
1.  **Top Left:** Spot Index (Candlesticks + 9 EMA).
2.  **Top Center/Right:** CE Premiums (ATM, OTM, ITM).
3.  **Bottom Left:** PCR vs. Spot (Line chart for sentiment).
4.  **Bottom Center/Right:** PE Premiums (ATM, OTM, ITM).

### Interactive Features
*   **Synchronization:** Crosshairs and zooming are linked across all 8 charts (`echarts.connect`).
*   **Maximization:** Individual charts can be maximized to full screen for granular study.
*   **Markers:**
    *   **Diamond (Green/Red):** Signal Entry.
    *   **Pin (Yellow/Gray):** Trade Exit (Target hit or BE).
    *   **Dashed Lines:** Raid (Target) and Wall (Stop Loss).

---

## 7. Implementation Guide (Code)

### Signal Engine (Python)
```python
def identify_paired_rs_signals(df_index, df_ce, df_pe, lookback=3):
    # 1. Sync dataframes on timestamp
    # 2. Calculate Swings with shift(lookback)
    # 3. Apply 9 EMA and Time Filters
    # 4. Check Paired Condition:
    ce_cross = df.at[i, 'close_ce'] > last_sh_ce and df.at[i-1, 'close_ce'] <= last_sh_ce
    pe_break = (df.iloc[i-3:i+1]['close_pe'] < last_sl_pe).any()

    if ce_cross and pe_break:
        # Generate Signal
```

### Export Logic (JavaScript)
*   **CSV:** Iterates through the `signals` array and creates a `data:text/csv` URI for download.
*   **PNG:** Uses ECharts `getDataURL({type: 'png'})` to capture snapshots of each quadrant.

---

## 8. Summary Table (Dashboard)
The UI includes a real-time backtest table with:
*   **Entry/Exit Times** (IST).
*   **Outcome Status:** "T1 Hit", "Stopped at BE", "Full SL Hit".
*   **PnL Tracking:** Aggregate and trade-wise points.
