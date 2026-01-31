# Lean Playground

A local-first development environment for algorithmic trading with [QuantConnect Lean](https://github.com/QuantConnect/Lean) — the open-source algorithmic trading engine. Build, backtest, and research trading strategies in Python without a QuantConnect subscription.

## Prerequisites

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine on Linux)
2. Install [VS Code](https://code.visualstudio.com/)
3. Install the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension in VS Code

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/todorkolev/lean-playground.git
   cd lean-playground
   ```

2. Open in VS Code:
   ```bash
   code .
   ```

3. When VS Code prompts you, click **Reopen in Container** (or open the Command Palette with `Ctrl+Shift+P` and run `Dev Containers: Reopen in Container`). The first build pulls a large base image and takes several minutes.

4. Once inside the container, run the sample backtest:
   ```bash
   lp backtest algorithms/sample_sma_crossover
   ```

## Project Structure

```
algorithms/                       # Your trading strategy projects
  sample_sma_crossover/           # Sample: SMA crossover strategy
    main.py                       # Algorithm implementation
    research.ipynb                # Strategy research notebook
notebooks/                        # Standalone Jupyter research notebooks
data -> /Lean/Data                # Market data (symlink, created at startup)
algorithm_examples -> /Lean/...   # ~500 Lean algorithm examples (symlink)
results/                          # Backtest output and reports
scripts/                          # lp CLI and lean_playground package
```

## Using the lp CLI

The `lp` command is the primary interface. No authentication required.

| Command | Description |
|---|---|
| `lp backtest <project>` | Run a backtest with the Lean engine |
| `lp create <name>` | Create a new project from template |
| `lp create <name> --from <Example>` | Create from a Lean algorithm example |
| `lp browse [keyword]` | Browse ~500 algorithm examples |
| `lp download [options]` | Download historical data from exchanges |
| `lp data list [options]` | List available market data |
| `lp data info <symbol>` | Show details for a specific symbol |
| `lp jupyter` | Restart Jupyter Lab (auto-starts with container) |
| `lp status` | Show workspace and engine status |

### Creating and Running a Strategy

1. Create a project:
   ```bash
   lp create algorithms/my_strategy
   ```

2. Edit `algorithms/my_strategy/main.py`:
   ```python
   from AlgorithmImports import *

   class MyStrategy(QCAlgorithm):
       def initialize(self):
           self.set_start_date(2020, 1, 1)
           self.set_cash(100_000)
           self.add_equity("SPY", Resolution.DAILY)

       def on_data(self, data):
           pass
   ```

3. Run the backtest:
   ```bash
   lp backtest algorithms/my_strategy
   ```

### Browsing Algorithm Examples

The container includes ~500 Python algorithm examples from the [Lean repository](https://github.com/QuantConnect/Lean/tree/master/Algorithm.Python):

```bash
lp browse              # List all examples
lp browse macd         # Search by keyword
lp create algorithms/macd_trend --from MACDTrendAlgorithm
lp backtest algorithms/macd_trend
```

### Downloading Historical Data

Download OHLCV data from Binance directly to the Lean data directory:

```bash
# Download last 10 days of BTCUSDT (default: 1m and 1h intervals)
lp download --symbols BTCUSDT

# Download multiple symbols and intervals
lp download --symbols BTCUSDT ETHUSDT --intervals 1m 1h 1d --days 30

# Download specific date range
lp download --symbols BTCUSDT --start-date 2024-01-01 --end-date 2024-03-01

# Download futures data (for cryptofuture asset class)
lp download --symbols BTCUSDT --account-type usdt_future
```

**Supported intervals:** `1s`, `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `6h`, `8h`, `12h`, `1d`, `3d`, `1w`

**Data source:** Downloads from Binance's public data archive (data.binance.vision) with no API key required. The archive provides historical data without rate limits.

### Inspecting Available Data

View what market data is available in the Lean data directory:

```bash
# List all available data
lp data list

# Filter by asset type, market, or resolution
lp data list --asset crypto
lp data list --market binance
lp data list --resolution daily

# Get detailed info for a specific symbol
lp data info BTCUSDT
lp data info SPY --asset equity
```

The data directory includes sample data for equities, crypto, forex, and futures. Use `lp download` to add more data from supported exchanges.

### Research Environment

Jupyter Lab starts automatically with the container at [http://localhost:8888](http://localhost:8888). Use `QuantBook` in notebooks for interactive research with access to the Lean engine and market data.

## Pre-installed Packages

The [quantconnect/research](https://hub.docker.com/r/quantconnect/research) base image provides a broad set of data science and ML packages:

- **Deep Learning**: PyTorch, JAX, TensorFlow
- **Classical ML**: scikit-learn, XGBoost, LightGBM
- **Streaming ML**: River
- **Quantitative Finance**: pyfolio-reloaded
- **Scientific Computing**: NumPy, SciPy, Pandas, StatsModels
- **Visualization**: Matplotlib, Seaborn, Plotly

River is the only additional package installed by this project (via `requirements.txt`). Everything else comes from the base image.

## Development Tools

### AI Assistants

The container includes CLI tools for AI-assisted development:

- [Claude Code](https://claude.ai/code) (CLI + VS Code extension)
- [BuildForce](https://buildforce.dev/) (Plugin for Claude Code)
- [Augment](https://www.augmentcode.com/) (VS Code extension)

Set `ANTHROPIC_API_KEY` in your environment for Claude Code (see `.env.example`) or use your Claude subscription to login.

### Editor Configuration

VS Code is pre-configured with extensions for Python, Jupyter, and Docker. Format-on-save and import organization are enabled via Pylance.

Standalone linters and formatters (Black, Pylint, isort) are not pre-installed. Add them if needed:
```bash
uv pip install black pylint isort
```

## QuantConnect Cloud (Optional)

For users with a [QuantConnect](https://www.quantconnect.com/) subscription, the Lean CLI provides cloud features:

```bash
lean login                # Authenticate
lean init                 # Initialize workspace
lean cloud push           # Push to QuantConnect cloud
lean data download        # Download market data
```

The `lp` commands work independently and do not require authentication.

## Troubleshooting

**`lp backtest` fails with "Lean engine not found"**
You are likely running outside the devcontainer. The Lean engine is only available inside the container.

**Port 8888 already in use**
Use an alternative port: `lp jupyter --port 8889`

**`lean login` or `lean init` fails**
These commands require a QuantConnect subscription. Use `lp` commands instead for local-only workflows.

## License

MIT License
