# Lean Playground

> **AI-powered algorithmic trading development.** Write, backtest, and optimize trading strategies with Claude Code in a reproducible QuantConnect Lean environment.

## 🤖 AI-Powered Strategy Development

Use the `/achieve` plugin to develop and optimize strategies through natural language goals:

```
Goal: "Create a momentum strategy with Sharpe > 1.5 and drawdown < 25%"
```

The AI will automatically:
1. **Research** the codebase and strategy patterns
2. **Plan** an implementation approach
3. **Build** the strategy code
4. **Backtest** and validate against your success criteria
5. **Iterate** until goals are achieved or you're satisfied

Each iteration is logged, so you can review the optimization journey and learn from both successful and failed approaches.

**In Claude Code:**
```bash
/achieve:goal              # Start a goal session

# Manage sessions
/achieve:list-goals    # List all sessions
/achieve:cancel-goal   # Cancel active session
```

Session data is stored in `.claude/achieve-sessions/` with full history of attempts.

## ✨ What's Included

- 🤖 **AI Development** — Claude Code + BuildForce + /achieve plugin pre-installed
- 🚀 **One-command backtesting** — `lp backtest algorithms/my_strategy`
- 📚 **500+ algorithm examples** — from QuantConnect's Lean repository
- 📊 **Performance tearsheets** — Sharpe, Sortino, drawdown, equity curves
- 📈 **Free data downloads** — Binance historical data (no API key needed)
- 🔬 **Jupyter Lab** — interactive research at localhost:8888
- 🐍 **Pre-configured Python** — PyTorch, TensorFlow, scikit-learn, pandas, and more

## 🚀 Getting Started

**Prerequisites:** **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** + **[VS Code](https://code.visualstudio.com/)** *+ [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) (VS Code will prompt you to install it if you don't have it already)*

### Option A: Private Repository

Create a private copy for your strategies — keep your trading algorithms confidential:

1. Click **[Import repository](https://github.com/new/import)** on GitHub
2. Enter `https://github.com/todorkolev/lean-playground.git` as the source
3. Name your repo and set it to **Private**
4. Clone your new private repo and open in VS Code
5. Reopen in Container (`Ctrl+Shift+P` → "Dev Containers: Reopen in Container")

### Option B: Public Fork

Fork if you want to share strategies or contribute back:

1. Click **Fork** on the [repository page](https://github.com/todorkolev/lean-playground)
2. Clone your fork and open in VS Code
3. Reopen in Container

### First Run

Once inside the container:
```bash
lp backtest algorithms/sample_sma_crossover
```

**Staying updated:** Run `lp update` periodically to sync with upstream and get new features.

## 📚 The lp CLI

The `lp` command is the primary interface. No authentication required.

| Command | Description |
|---------|-------------|
| `lp backtest <project>` | Run a backtest with the Lean engine |
| `lp live <project>` | Run live/paper trading (21+ brokerages) |
| `lp analyze <project>` | Generate tearsheet from existing results (default: latest) |
| `lp create <name>` | Create new project from template |
| `lp create <name> --from <Example>` | Create from algorithm example |
| `lp browse [keyword]` | Browse 500+ algorithm examples |
| `lp download [options]` | Download historical data from Binance |
| `lp data list` | List available market data |
| `lp data info <symbol>` | Show details for a symbol |
| `lp jupyter` | Restart Jupyter Lab |
| `lp status` | Show workspace status |
| `lp update` | Sync fork with upstream repository |

### Creating a Strategy

```bash
# Create from template
lp create algorithms/my_strategy

# Or create from an example
lp browse macd                                    # Find examples
lp create algorithms/macd_trend --from MACDTrendAlgorithm
```

Edit `algorithms/my_strategy/main.py`:

```python
from AlgorithmImports import *

class MyStrategy(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2020, 1, 1)
        self.set_cash(100_000)
        self.add_equity("SPY", Resolution.DAILY)

    def on_data(self, data):
        if not self.portfolio.invested:
            self.set_holdings("SPY", 1)
```

Run: `lp backtest algorithms/my_strategy`

### Downloading Data

```bash
# Download BTCUSDT (default: 1m and 1h, last 10 days)
lp download --symbols BTCUSDT

# Multiple symbols, custom intervals and range
lp download --symbols BTCUSDT ETHUSDT --intervals 1h 1d --days 30

# Futures data
lp download --symbols BTCUSDT --account-type usdt_future
```

**Supported intervals:** 1s, 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w

### Analyzing Results

```bash
# Generate tearsheet for latest backtest
lp analyze my_strategy

# Specific backtest by timestamp
lp analyze my_strategy --backtest 20260129-215353
```

Reports include equity curve, drawdown analysis, monthly returns heatmap, and risk metrics.

### Paper & Live Trading

Run algorithms with 21+ supported brokerages including Binance, Alpaca, Bybit, Kraken, Interactive Brokers, and more.

```bash
# List all available brokerages
lp live --list-brokerages
```

**Setup credentials:**
```bash
# Copy .env.example and add your API keys
cp .env.example .env

# Credential pattern: {BROKERAGE}_API_KEY, {BROKERAGE}_API_SECRET
# See .env.example for all supported brokerages
```

**Paper trading** (testnet, no real funds - default):
```bash
lp live algorithms/my_strategy --brokerage binance       # Binance spot
lp live algorithms/my_strategy --brokerage binance-usdt-futures  # Binance futures
lp live algorithms/my_strategy --brokerage alpaca        # Alpaca
lp live algorithms/my_strategy --brokerage bybit         # Bybit
lp live algorithms/my_strategy --cash 50000              # Custom starting balance
```

**Live trading** (real funds):
```bash
lp live algorithms/my_strategy --brokerage binance --live  # Real funds
```

Your algorithm should set the appropriate brokerage model:
```python
# For Binance spot trading
self.set_brokerage_model(BrokerageName.BINANCE, AccountType.CASH)

# For Binance futures trading
self.set_brokerage_model(BrokerageName.BINANCE_FUTURES, AccountType.MARGIN)

# For Alpaca
self.set_brokerage_model(BrokerageName.ALPACA, AccountType.MARGIN)
```

See `algorithms/binance_paper_example/` for a complete example.

## 🔄 Staying Updated

Keep your repository synchronized with upstream to get new features, examples, and fixes:

```bash
lp update              # Pull latest changes (rebase mode)
lp update --merge      # Use merge mode if others contribute to your repo
```

Works with both private imports and public forks.

## ☁️ QuantConnect Cloud (Optional)

For users with a [QuantConnect](https://www.quantconnect.com/) subscription, the Lean CLI provides cloud features:

```bash
lean login                # Authenticate
lean init                 # Initialize workspace
lean cloud push           # Push to cloud
lean data download        # Download premium data
```

The `lp` commands work independently without authentication.

## 🔧 Reference

<details>
<summary><strong>Project Structure</strong></summary>

```
algorithms/                       # Your trading strategy projects
  sample_sma_crossover/           # Sample strategy
    main.py                       # Algorithm implementation
    research.ipynb                # Research notebook
research/                         # Standalone Jupyter notebooks
data -> /Lean/Data                # Market data (symlink)
algorithm_examples -> /Lean/...   # 500+ Lean examples (symlink)
results/                          # Backtest output
scripts/                          # lp CLI and lean_playground package
```

</details>

<details>
<summary><strong>Pre-installed Packages</strong></summary>

The [quantconnect/research](https://hub.docker.com/r/quantconnect/research) base image includes:

- **Deep Learning**: PyTorch, JAX, TensorFlow
- **Classical ML**: scikit-learn, XGBoost, LightGBM
- **Streaming ML**: River
- **Quantitative Finance**: pyfolio-reloaded
- **Scientific Computing**: NumPy, SciPy, Pandas, StatsModels
- **Visualization**: Matplotlib, Seaborn, Plotly

</details>

<details>
<summary><strong>Editor Configuration</strong></summary>

VS Code is pre-configured with Python, Jupyter, and Docker extensions. Format-on-save is enabled.

Linting and formatting tools (Black, Pylint, isort) are pre-installed:
- **Black**: Auto-formats code on save
- **Pylint**: Shows linting errors inline
- **isort**: Organizes imports on save

</details>

<details>
<summary><strong>Troubleshooting</strong></summary>

**`lp backtest` fails with "Lean engine not found"**
You're running outside the devcontainer. The Lean engine is only available inside the container.

**Port 8888 already in use**
Use: `lp jupyter --port 8889`

**`lean login` or `lean init` fails**
These require a QuantConnect subscription. Use `lp` commands instead.

</details>

