---
name: strategy.write
description: Write a trading strategy for QuantConnect Lean, informed by accumulated knowledge. Use when asked to create a new trading strategy.
allowed-tools: Read, Write, Glob, Grep, Bash
argument-hint: "[strategy description]"
---

# Write Trading Strategy

Generate a trading strategy for QuantConnect Lean, applying knowledge from the strategy-writer skill.

## Arguments

- `$ARGUMENTS`: Description of the desired strategy
  - Strategy type, indicators, asset class, etc.

## Workflow

### Step 1: Parse Requirements

Extract from `$ARGUMENTS`:
- **Strategy type**: momentum, mean-reversion, breakout, trend-following, pairs
- **Asset class**: equity, crypto, forex (default: equity)
- **Timeframe**: intraday, daily, weekly (default: daily)
- **Indicators**: Any specific indicators mentioned
- **Risk parameters**: Position size, stops, targets mentioned

### Step 2: Load Knowledge

Read relevant knowledge files from `.claude/skills/strategy-writer/knowledge/`:

```
knowledge/entry-signals.yaml    → Entry patterns
knowledge/exit-rules.yaml       → Exit patterns
knowledge/risk-management.yaml  → Risk patterns
knowledge/mistakes.yaml         → Anti-patterns to avoid
```

Filter entries by:
- Tags matching strategy type, asset class, timeframe
- Confidence >= 0.5 (higher confidence = higher priority)

### Step 3: Apply Knowledge

For each relevant knowledge entry:
- **Patterns**: Incorporate into strategy design
- **Anti-patterns**: Explicitly avoid in implementation
- Note which entries were applied (for `/evolve.reflect`)

### Step 4: Generate Strategy Name

Create a descriptive name:
- Format: `{type}_{asset}_{indicator}` or similar
- Example: `momentum_crypto_rsi`, `mean_reversion_equity_bollinger`

### Step 5: Create Strategy Directory

```bash
lp create algorithms/{strategy_name}
```

Or if it should be based on an example:
```bash
lp create algorithms/{strategy_name} --from {ExampleAlgorithm}
```

### Step 6: Write Strategy Code

Generate `algorithms/{strategy_name}/main.py` following this structure:

```python
from AlgorithmImports import *

class StrategyName(QCAlgorithm):
    """
    Strategy description.

    Type: {type}
    Entry: {entry_description}
    Exit: {exit_description}
    Risk: {risk_description}

    Knowledge applied:
    - {entry_id}: {summary}
    - {exit_id}: {summary}
    """

    def initialize(self):
        # Time range
        self.set_start_date(2020, 1, 1)
        self.set_end_date(2024, 1, 1)
        self.set_cash(100000)

        # Securities
        self.symbol = self.add_equity("SPY", Resolution.DAILY).symbol
        # Or for crypto: self.add_crypto("BTCUSD", Resolution.DAILY)

        # Indicators
        self.indicator = self.SMA(self.symbol, 20)

        # Risk parameters
        self.position_size = 0.1  # 10% of portfolio

    def on_data(self, data):
        if not self.indicator.is_ready:
            return

        if not data.contains_key(self.symbol):
            return

        # Entry logic
        # ...

        # Exit logic
        # ...
```

### Step 7: Output

Provide:

1. **Strategy code** (written to file)

2. **Summary**:
   ```
   Strategy created: algorithms/{strategy_name}/main.py

   Knowledge applied:
   - [ES-001] {summary}
   - [MK-002] Avoided: {summary}

   Backtest command:
   lp backtest algorithms/{strategy_name}

   After reviewing results, run /evolve.reflect to capture learnings.
   ```

## Example

User: `/strategy.write momentum strategy for crypto using RSI with proper risk management`

Output:
- Creates `algorithms/momentum_crypto_rsi/main.py`
- Applies relevant entry-signals, exit-rules, risk-management patterns
- Avoids mistakes from mistakes.yaml
- Suggests: `lp backtest algorithms/momentum_crypto_rsi`
