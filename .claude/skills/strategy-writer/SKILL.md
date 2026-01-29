---
name: strategy-writer
description: Write trading strategies for QuantConnect Lean, informed by accumulated knowledge. Use when asked to create, design, or implement a trading strategy.
allowed-tools: Read, Write, Glob, Grep, Bash
---

# Strategy Writer Skill

Write trading strategies for QuantConnect Lean, applying accumulated knowledge from the `knowledge/` folder.

## Purpose

- Generate trading strategy code based on user requirements
- Apply proven patterns from knowledge base
- Avoid known anti-patterns and mistakes
- Produce strategies ready for backtesting with `lp backtest`

## Knowledge Location

Strategy knowledge lives in:
- `.claude/skills/strategy-writer/knowledge/`

Key knowledge files:
- `entry-signals.yaml` - Entry pattern knowledge
- `exit-rules.yaml` - Exit pattern knowledge
- `risk-management.yaml` - Position sizing, stops
- `mistakes.yaml` - Anti-patterns to avoid

## Workflow

When writing a strategy:

### 1. Understand Requirements

Parse the user's request for:
- Strategy type (momentum, mean-reversion, breakout, etc.)
- Asset class (equity, crypto, forex)
- Timeframe (intraday, daily, weekly)
- Specific indicators or signals mentioned
- Risk parameters mentioned

### 2. Load Relevant Knowledge

Read knowledge files and select entries relevant to this strategy:
- Filter by tags matching strategy type, asset class, timeframe
- Prioritize high-confidence entries (confidence > 0.7)
- Load both patterns (to apply) and anti-patterns (to avoid)

### 3. Design Strategy

Based on requirements and knowledge:
- Select entry signal approach
- Design exit rules
- Define position sizing
- Add risk management (stops, limits)

### 4. Generate Code

Create the strategy following Lean conventions:
- Location: `algorithms/{strategy_name}/main.py`
- Import: `from AlgorithmImports import *`
- Class inherits from `QCAlgorithm`
- Implement `initialize()` and `on_data()`
- Use snake_case method names

### 5. Output

Provide:
- The complete strategy code
- Brief explanation of how knowledge was applied
- Suggested backtest command: `lp backtest algorithms/{strategy_name}`
- Reminder to run `/evolve.reflect` after viewing results

## Code Template

```python
from AlgorithmImports import *

class {StrategyName}(QCAlgorithm):
    """
    {Brief description}

    Strategy type: {type}
    Entry: {entry_description}
    Exit: {exit_description}
    Risk: {risk_description}
    """

    def initialize(self):
        self.set_start_date({year}, {month}, {day})
        self.set_end_date({year}, {month}, {day})
        self.set_cash({amount})

        # Add securities
        # Initialize indicators
        # Set up scheduling if needed

    def on_data(self, data):
        # Entry logic
        # Exit logic
        # Position management
```

## Integration with Evolve

After backtest results:
- Suggest running `/evolve.reflect` to capture learnings
- If results are particularly good/bad, prompt for specific learning capture
