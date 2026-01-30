---
name: strategy-writer
description: |
  AUTO-INVOKE when the user asks to write, create, build, or implement a trading strategy.
  Triggers on: "write a strategy", "create a momentum strategy", "build an RSI strategy",
  "implement mean reversion", "make a crossover algorithm", or similar requests.
allowed-tools: Read, Write, Glob, Grep, Bash
---

# Strategy Writer

**Auto-invokes to create QuantConnect Lean trading strategies.**

## Project Structure

Each strategy project in `algorithms/{name}/` contains:

```
algorithms/{name}/
├── main.py           # Strategy implementation
├── spec.md           # Strategy specification (goals, rules, parameters)
├── results.md        # Backtest results summary (updated after each run)
└── research.ipynb    # Research notebook for analysis
```

**Keep all files in sync** - update spec.md when strategy changes, update results.md after backtests.

## Workflow

### 1. Parse Requirements

Parse the user's request for:
- **Strategy type**: momentum, mean-reversion, breakout, trend-following, pairs
- **Asset class**: crypto (preferred), equity, forex, futures
- **Timeframe**: intraday, daily, weekly
- **Indicators**: specific indicators or signals mentioned
- **Risk parameters**: position size, stops, targets mentioned

### 2. Ensure Data Exists

**Prefer Binance crypto data** - the `lp download` tool fetches it directly.

#### Check Available Data

```bash
ls /Lean/Data/crypto/binance/         # Binance crypto (preferred)
ls /Lean/Data/crypto/coinbase/        # Coinbase crypto
ls /Lean/Data/equity/usa/daily/       # US Equity (SPY, AAPL, etc.)
```

#### Download Crypto Data (Binance)

Use `lp download` to fetch Binance data in Lean format:

```bash
# Basic - last 10 days, 1m and 1h intervals
lp download --symbols BTCUSDT

# Multiple symbols, 30 days
lp download --symbols BTCUSDT ETHUSDT --days 30

# Specific date range
lp download --symbols BTCUSDT --start-date 2024-01-01 --end-date 2024-06-01

# Daily data only
lp download --symbols BTCUSDT --intervals 1d

# Futures data (perpetuals)
lp download --symbols BTCUSDT --account-type usdt_future

# All intervals
lp download --symbols BTCUSDT --intervals 1m 5m 15m 1h 4h 1d
```

**Options:**
- `--symbols` - Trading pairs (BTCUSDT, ETHUSDT, SOLUSDT, etc.)
- `--intervals` - 1s, 1m, 5m, 15m, 30m, 1h, 4h, 1d
- `--days` - Days of history (default: 10)
- `--start-date` / `--end-date` - Specific date range (YYYY-MM-DD)
- `--account-type` - spot (default), usdt_future, coin_future

Data is written to `/Lean/Data/crypto/binance/`.

### 3. Load Relevant Knowledge

Read all files from `.claude/skills/strategy-writer/knowledge/`:

```bash
# List and read all knowledge files
ls .claude/skills/strategy-writer/knowledge/
```

For each knowledge file:
- Filter entries by tags matching strategy type, asset class, timeframe
- Prioritize high-confidence entries (confidence > 0.7)
- Load both patterns (to apply) and anti-patterns (to avoid)

### 4. Design Strategy

Based on requirements and knowledge:
- Select entry signal approach
- Design exit rules
- Define position sizing
- Add risk management (stops, limits)

### 5. Create Project

```bash
lp create algorithms/{name}
# Or from example:
lp create algorithms/{name} --from {ExampleAlgorithm}
```

### 6. Generate Code

Create the strategy following Lean conventions:
- Location: `algorithms/{strategy_name}/main.py`
- Import: `from AlgorithmImports import *`
- Class inherits from `QCAlgorithm`
- Implement `initialize()` and `on_data()`
- Use snake_case method names

### 7. Write Strategy Files

#### main.py - Strategy Implementation

```python
from AlgorithmImports import *


class StrategyName(QCAlgorithm):
    """
    Strategy description.

    Type: {type}
    Entry: {entry_logic}
    Exit: {exit_logic}
    Knowledge: [{applied_ids}]
    """

    def initialize(self):
        self.set_start_date(2024, 1, 1)
        self.set_end_date(2024, 6, 1)
        self.set_cash(100_000)

        # Crypto (Binance) - preferred
        self.symbol = self.add_crypto("BTCUSDT", Resolution.HOUR, Market.BINANCE).symbol
        # Equity alternative:
        # self.symbol = self.add_equity("SPY", Resolution.DAILY).symbol

        # Indicators
        self.sma_fast = self.sma(self.symbol, 10)
        self.sma_slow = self.sma(self.symbol, 30)

        # Risk parameters
        self.position_size = 1.0

        # Warm up
        self.set_warm_up(30)

    def on_data(self, data: Slice):
        if self.is_warming_up:
            return
        if not data.contains_key(self.symbol):
            return
        if not self.sma_fast.is_ready or not self.sma_slow.is_ready:
            return

        # Entry logic
        if not self.portfolio.invested:
            if self.sma_fast.current.value > self.sma_slow.current.value:
                self.set_holdings(self.symbol, self.position_size)

        # Exit logic
        else:
            if self.sma_fast.current.value < self.sma_slow.current.value:
                self.liquidate(self.symbol)
```

#### spec.md - Strategy Specification

```markdown
# {Strategy Name}

## Overview
Brief description of the strategy concept.

## Hypothesis
What market behavior does this strategy exploit?

## Rules

### Entry Conditions
- Condition 1
- Condition 2

### Exit Conditions
- Condition 1
- Condition 2

### Risk Management
- Position size: X%
- Stop loss: X%
- Take profit: X%

## Parameters
| Parameter | Value | Description |
|-----------|-------|-------------|
| fast_period | 10 | Fast MA period |
| slow_period | 30 | Slow MA period |

## Data Requirements
- Symbol: BTCUSDT
- Resolution: Hour
- Date range: 2024-01-01 to 2024-06-01

## Knowledge Applied
- [ID] Description of applied pattern
```

#### results.md - Backtest Results

```markdown
# Backtest Results: {Strategy Name}

## Latest Run
- **Date**: {timestamp}
- **Period**: {start} to {end}

## Performance Metrics
| Metric | Value |
|--------|-------|
| Total Return | X% |
| Sharpe Ratio | X.XX |
| Max Drawdown | X% |
| Win Rate | X% |
| Total Trades | N |

## Summary
Brief analysis of the results.

## History
| Date | Sharpe | Return | Drawdown | Notes |
|------|--------|--------|----------|-------|
| ... | ... | ... | ... | ... |
```

### 8. Run Backtest

```bash
lp backtest algorithms/{name}
```

### 9. Update Results

After backtest completes:
1. Read `results/{name}/{timestamp}/main-summary.json`
2. Update `algorithms/{name}/results.md` with new metrics
3. Add entry to history table

### 10. Output

Provide:
- The complete strategy code
- Brief explanation of how knowledge was applied
- Suggested backtest command: `lp backtest algorithms/{strategy_name}`
- Reminder to run `/evolve` after viewing results

## Browse Examples

```bash
lp browse              # List all ~500 examples
lp browse macd         # Search for MACD examples
cat /Lean/Algorithm.Python/MACDTrendAlgorithm.py  # Read example
```

## Lean API Quick Reference

**Adding Securities:**
```python
self.add_crypto("BTCUSDT", Resolution.HOUR, Market.BINANCE)  # Preferred
self.add_equity("SPY", Resolution.DAILY)
self.add_forex("EURUSD", Resolution.HOUR, Market.OANDA)
```

**Resolutions:** `Resolution.TICK`, `SECOND`, `MINUTE`, `HOUR`, `DAILY`

**Built-in Indicators:**
```python
self.sma(symbol, period)      # Simple Moving Average
self.ema(symbol, period)      # Exponential MA
self.rsi(symbol, period)      # Relative Strength Index
self.macd(symbol, fast, slow, signal)  # MACD
self.bb(symbol, period, k)    # Bollinger Bands
self.atr(symbol, period)      # Average True Range
self.adx(symbol, period)      # Average Directional Index
```

**Position Management:**
```python
self.set_holdings(symbol, 1.0)   # 100% long
self.set_holdings(symbol, -0.5)  # 50% short
self.liquidate(symbol)           # Close position
self.portfolio.invested          # Bool: has positions?
```

## File Maintenance

**After strategy changes:**
- Update `spec.md` with new parameters/rules
- Update docstring in `main.py`

**After each backtest:**
- Parse `results/{name}/{latest}/main-summary.json`
- Update `results.md` with metrics and history entry
