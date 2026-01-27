# Lean Playground

A QuantConnect Lean algorithmic trading research and development playground with ML capabilities.

No QuantConnect subscription required. Works locally out of the box.

## Project Structure

```
algorithms/                # Lean algorithm projects
  sample_sma_crossover/    # Sample: SMA crossover strategy
    main.py                # Algorithm implementation
    research.ipynb         # Strategy research notebook
notebooks/                 # Standalone research notebooks
  getting_started.ipynb    # Intro to QuantConnect research
data/                      # Symlink to /Lean/Data (market data)
results/                   # Backtest output and reports
scripts/                   # lp CLI and lean_playground package
  lp                       # Entry point
  lean_playground/         # Python package
tests/                     # Smoke and integration tests
```

Algorithm examples from the Lean repo (~500 Python examples) are available inside the container at `/Lean/Algorithm.Python/`.

## Quick Start

### DevContainer (Recommended)

Open in VS Code and use "Reopen in Container". The devcontainer provides:
- QuantConnect Lean engine (Python + .NET)
- `lp` CLI for backtesting and project management (no auth required)
- ~500 Python algorithm examples from the Lean repo
- JupyterLab on port 8888
- Full ML stack (PyTorch, JAX, scikit-learn, XGBoost)
- AI tools (Claude Code, Augment, Aider)
- Code quality tools (Black, isort, Pylint)
- Optional: Lean CLI for QuantConnect cloud features (requires subscription)

### Running a Backtest

```bash
lp backtest algorithms/sample_sma_crossover
```

### Research Environment

```bash
lp jupyter
# Open http://localhost:8888/lab
```

## Creating a New Algorithm

1. Create a project:
   ```bash
   lp create algorithms/my_strategy
   ```

2. Edit `algorithms/my_strategy/main.py` with your strategy:
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

### Using Algorithm Examples

The container includes ~500 Python algorithm examples from the Lean repo:

```bash
# Browse all algorithm examples
lp browse

# Search by keyword
lp browse macd

# Create a project from an algorithm example
lp create algorithms/macd_trend --from MACDTrendAlgorithm

# Run it
lp backtest algorithms/macd_trend
```

## QuantConnect Cloud (Optional)

If you have a QuantConnect subscription, you can use the Lean CLI for cloud features:

```bash
# Authenticate
lean login

# Initialize workspace for your organization
lean init

# Push to cloud, download data, run live trading, etc.
lean cloud push
lean data download
```

The `lp` commands work independently and do not require authentication.

## ML Stack

This playground includes a full ML stack pre-installed in the container:
- **Deep Learning**: PyTorch, JAX, TensorFlow
- **Classical ML**: scikit-learn, XGBoost, LightGBM
- **Streaming ML**: River
- **Quantitative Finance**: QuantLib, zipline, pyfolio
- **Scientific Computing**: NumPy, SciPy, Pandas, StatsModels
- **Visualization**: Matplotlib, Seaborn, Plotly

## License

MIT License
