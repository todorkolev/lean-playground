# Lean Playground Code Guidelines

## MCP Tools

When working with libraries, frameworks, or APIs, use the **context7** MCP tool to fetch up-to-date documentation directly into the conversation. This avoids outdated information and provides version-specific examples.

## Project Structure
- **algorithms/**: QuantConnect Lean algorithm projects (Python)
- **research/**: Standalone Jupyter research notebooks
- **data/**: Symlink to /Lean/Data (market data for Lean engine)
- **results/**: Backtest output and reports
- **scripts/**: `lp` CLI, lean_playground Python package, and tests
- **/Lean/Algorithm.Python/**: ~500 algorithm examples from the Lean repo (inside container)

## Commands

### lp CLI (no QuantConnect auth required)
```bash
lp backtest algorithms/sample_sma_crossover    # Run a backtest
lp live algorithms/my_strategy --brokerage binance  # Paper trading (21+ brokerages)
lp create algorithms/my_strategy               # Create new project from template
lp create algorithms/my_macd --from MACDTrendAlgorithm  # Create from algorithm example
lp browse                                      # List all algorithm examples
lp browse sma                                  # Search algorithm examples
lp jupyter                                     # Start Jupyter Lab
lp status                                      # Show workspace status
```

### Paper & Live Trading (21+ Brokerages)
```bash
# List all supported brokerages
lp live --list-brokerages

# Add API keys to .env file (copy from .env.example)
# Pattern: {BROKERAGE}_API_KEY, {BROKERAGE}_API_SECRET

# Paper trading (testnet, no real funds) - DEFAULT
lp live algorithms/my_strategy --brokerage binance              # Binance spot
lp live algorithms/my_strategy --brokerage binance-usdt-futures # Binance futures
lp live algorithms/my_strategy --brokerage alpaca               # Alpaca
lp live algorithms/my_strategy --brokerage bybit                # Bybit
lp live algorithms/my_strategy --cash 50000                     # Custom balance

# Live trading (real funds)
lp live algorithms/my_strategy --brokerage binance --live       # Real funds
```

### Lean CLI (requires QuantConnect subscription, optional)
```bash
lean login                   # Authenticate with QuantConnect
lean init                    # Initialize workspace with org (creates lean.json)
lean backtest algorithms/x   # Run backtest via Docker-in-Docker
lean cloud push              # Push to QuantConnect cloud
```

### Testing
```bash
pytest scripts/tests/ -v
```

## Code Style

### General
- **Doc Style**: Google-style docstrings with Args/Returns
- **Typing**: Use type annotations extensively
- **Naming**: CamelCase for classes, snake_case for methods/functions/variables
- **Imports**: Standard lib first, external packages second, internal modules last

### Lean Algorithm Conventions
- Algorithms inherit from `QCAlgorithm`
- Use `from AlgorithmImports import *` for imports
- Implement `initialize()` for setup and `on_data()` for logic
- Use snake_case method names (Lean Python API convention)
- Each algorithm project has its own directory with `main.py`

### Python Best Practices
- **Error Handling**: Try-except blocks with specific exception types
- **Testing**: Use pytest fixtures, smoke tests for environment verification

## Strategy Writing

When creating or modifying trading strategies, follow this workflow:

### 1. Project Structure
Each strategy in `algorithms/{name}/` contains:
- `main.py` - Strategy implementation
- `spec.md` - Strategy specification (keep updated as you work)
- `results.md` - Backtest results (update after each run)

### 2. Lean Code Reference
The container has Lean source code and examples:
- `/Lean/Algorithm.Python/` - ~423 Python algorithm examples (search with `lp browse`)
- `/Lean/Data/` - Market data directory (crypto, equity, forex, futures, options)
- `/Lean/Launcher/` - Lean engine launcher
- `/Lean/DownloaderDataProvider/` - Data download utilities

**For more project details, workspace capabilities, and tooling**: Read `README.md` in the workspace root.

**For API reference**: Use the **context7** MCP tool to fetch up-to-date documentation for any library (QuantConnect Lean, pandas, numpy, ta-lib, etc.).

### 3. Data Management

> **CRITICAL: NEVER download data without first checking what's available.**
> Run `lp data list` or `lp data info <SYMBOL>` BEFORE any `lp download` command.
> Downloading duplicate data wastes time and bandwidth.

**Check available data first:**
```bash
# Inspect available data
lp data list                              # List all available data
lp data list --asset crypto               # Filter by asset type
lp data list --market binance             # Filter by market/exchange
lp data list --resolution hour            # Filter by resolution

lp data info BTCUSDT                      # Details for specific symbol
lp data info BTCUSDT --market binance     # With market filter

lp status                                 # Overview of workspace and data
```

**Download parameters:**
```bash
lp download [OPTIONS]

--symbols SYMBOLS [SYMBOLS ...]   # Symbols to download (default: BTCUSDT)
--intervals INTERVALS [...]       # 1s, 1m, 5m, 15m, 30m, 1h, 4h, 1d (default: 1m 1h)
--exchange {binance}              # Exchange (default: binance)
--days DAYS                       # Days of history (default: 10)
--start-date YYYY-MM-DD           # Explicit start date
--end-date YYYY-MM-DD             # Explicit end date
--account-type TYPE               # spot, margin, usdt_future, coin_future (default: spot)
--testnet                         # Use testnet endpoints
```

**Examples:**
```bash
lp download --symbols BTCUSDT --days 30              # 30 days, 1m and 1h
lp download --symbols BTCUSDT ETHUSDT --intervals 1h 1d  # Multiple symbols, hourly+daily
lp download --symbols BTCUSDT --account-type usdt_future  # Perpetual futures data
lp download --symbols BTCUSDT --start-date 2024-01-01 --end-date 2024-06-01
```

### 4. Strategy Reference
Before writing a new strategy, search for similar algorithms in the codebase:
```bash
lp browse <keyword>                       # Search algorithm examples (e.g., "momentum", "rsi", "macd")
```
Use existing algorithms in `algorithms/` and `/Lean/Algorithm.Python/` as reference for patterns and structure.

### 5. Run Backtest
```bash
lp backtest algorithms/{name}
```

### 6. Update Results
After backtest, update `algorithms/{name}/results.md` with metrics from `results/{name}/{timestamp}/main-summary.json`.

==================

### Algorithmic Trading & Quant Principles

**Backtesting Discipline:**
- Avoid overfitting: If a strategy needs >3-5 parameters, it's likely curve-fitted
- Out-of-sample testing is mandatory - never trust in-sample results alone
- Account for realistic transaction costs, slippage, and market impact
- Beware survivorship bias - test on delisted assets when possible
- No look-ahead bias: Only use data available at decision time
- Walk-forward analysis beats single backtest periods

**Risk Management (Non-Negotiable):**
- Position sizing matters more than entry signals
- Define maximum drawdown tolerance before trading
- Correlation kills: Diversification fails when you need it most
- Tail risk is real - expect 3+ sigma events more often than normal distribution suggests
- Risk per trade: Never risk more than 1-2% of capital on a single position
- Stop losses are insurance, not failure

**Strategy Development Philosophy:**
- Simple strategies are more robust than complex ones (Occam's razor)
- Every strategy needs an economic rationale - why should this edge exist and persist?
- Regime awareness: Strategies that work in trending markets fail in mean-reverting ones
- Robustness over optimization: Prefer strategies that work "well enough" across conditions
- If it looks too good to be true, it is - Sharpe > 2 in backtests rarely survives live trading
- Alpha decays: Edges erode as more capital exploits them

**Execution Realism:**
- Backtests assume perfect fills; reality has slippage and partial fills
- Liquidity constraints: Can you actually trade the size your backtest assumes?
- Market impact: Your orders move prices, especially in less liquid markets
- Latency matters for high-frequency, less so for daily/weekly strategies

**Professional Standards:**
- Document every strategy decision and parameter choice
- Track live vs backtest performance divergence
- Kill strategies that underperform expectations - no emotional attachment
- Version control everything: code, parameters, and results
- Reproducibility: Anyone should be able to recreate your results

### Quant Trading Literature Wisdom

**From "Advances in Financial Machine Learning" by Marcos López de Prado:**
- Backtest overfitting is the #1 cause of strategy failure - use combinatorial purged cross-validation
- Feature importance > feature engineering: Understand what drives predictions
- Fractionally differentiated features preserve memory while achieving stationarity
- Meta-labeling: Separate the side of the bet from its size
- The probability of backtest overfitting increases with the number of trials
- Triple-barrier method for labeling: Profit-taking, stop-loss, and time expiration

**From "Quantitative Trading" & "Algorithmic Trading" by Ernest Chan:**
- Start small: Paper trade, then trade small size, then scale up
- Kelly criterion for position sizing - but use half-Kelly in practice for safety
- Mean reversion works on short timeframes; momentum on longer timeframes
- Cointegration > correlation for pairs trading
- Transaction costs can turn a winning strategy into a losing one
- Capacity constraints: Know your strategy's maximum capital before returns degrade

**From "Active Portfolio Management" by Grinold & Kahn:**
- Fundamental Law: IR = IC × √BR (Information Ratio = Skill × √Breadth)
- Maximize breadth: More independent bets > fewer concentrated bets
- Alpha = Volatility × IC × Score (alpha generation formula)
- Risk budgeting: Allocate risk, not just capital
- Transfer coefficient measures implementation efficiency

**From "Inside the Black Box" by Rishi Narang:**
- Alpha models, risk models, and transaction cost models are the three pillars
- Execution algorithms are strategies themselves - treat them as such
- Data quality issues cause more losses than bad models
- The best quants are skeptics of their own ideas

**From "Trading and Exchanges" by Larry Harris:**
- Understand who you're trading against - informed traders vs liquidity traders
- Market impact is a function of trade size relative to typical volume
- Bid-ask spread is the minimum cost of immediacy
- Order flow toxicity predicts adverse selection

**From "Evidence-Based Technical Analysis" by David Aronson:**
- Most technical analysis fails rigorous statistical testing
- Data mining bias: Test fewer hypotheses, use stricter significance levels
- Survivorship bias in indicator popularity - failed indicators are forgotten
- Scientific method: Hypothesis → Prediction → Test → Conclude

==================

## Engineering Wisdom

Never use mocks or fallbacks to patch the issues. Implement the intended functionality and fix the root causes of the problems. Raise errors when the code can not operate properly. Don't cover problems by silencing the exceptions. Keep the code elegant and clean.

When runnig tests, if tests fail, investigate the failures and look for root causes. The problems might be either in the source code or the tests. The end goal is to have the code run as intended, not just pass the tests.

Apply the principles from "Code Complete" by Steve McConnell:
- Tame complexity with disciplined abstractions and naming conventions.
- Quality is speed: Prevent defects during construction to ship faster.
- Plan before typing—understand requirements, sketch designs, spot risks.
- Write for people first: Clear formatting, self-explanatory identifiers, meaningful comments only where intent needs context.
- Modularize & encapsulate so changes touch the fewest files.
- Program defensively: Validate inputs, handle errors explicitly, guard against nulls and edge cases.
- Iterate & refactor relentlessly—continuous small improvements beat big-bang rewrites.

Apply the principles from "Clean Architecture" by Robert C. Martin:
- Dependency Rule: Source code dependencies point inward toward business rules.
- Core is framework-, UI-, and DB-agnostic—outer layers depend on inner, never vice-versa.
- Architecture's purpose: Keep options open and minimize long-term human effort.
- Scale SOLID upward: Reuse/Release, Common-Closure, Common-Reuse; aim for acyclic, stable-yet-abstract components.
- Push volatile details (frameworks, gateways) to the periphery.
- "Screaming Architecture": Folder names and boundaries should shout the business intent, not the technology stack.

Apply principles from "Clean Code" by Robert C. Martin:
- Code is read far more than written—optimize for clarity.
- KISS and consistent; avoid accidental complexity.
- Small, single-purpose functions & classes; eliminate duplication (DRY).
- Use intention-revealing, searchable names and uniform formatting.
- Apply SOLID at code level: Prefer polymorphism, inject dependencies.
  - Single Responsibility: Each class has one purpose.
  - Open/Closed: Open for extension, closed for modification.
  - Liskov Substitution: Derived classes must be substitutable.
  - Interface Segregation: Many client-specific interfaces over general-purpose.
  - Dependency Inversion: Depend on abstractions, not concretions.
- Boy-Scout Rule: Leave every file cleaner than found.
- Fast, independent, self-validating tests (TDD mindset).
- Prefer exceptions to error codes; separate error-handling paths.
- Prefer composition over inheritance.
- Code to interfaces, not implementations.
- Encapsulate changing parts.

Architectural Decisions Prioritization (in order):
- Reliability
- Performance
- Modularity
- Testability
- Maintainability
- Deployability

Additional Principles:
- Follow established patterns/styles.
- Design for extensibility/future changes.
- Maintain clear component boundaries.
- Use appropriate abstractions.
- Consider security in decisions.
- Plan for observability/monitoring
- Design for scalability where needed.
- Keep clean abstractions, encapsulation, separation of concerns.
- Apply Design Patterns appropriately (e.g., State for Position, Observer for events).
