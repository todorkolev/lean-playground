# Lean Playground

A QuantConnect Lean algorithmic trading research and development playground with ML capabilities.

## Project Structure

```
algorithms/                # Lean algorithm projects
  sample_sma_crossover/    # Sample: SMA crossover strategy
    main.py                # Algorithm implementation
    research.ipynb         # Strategy research notebook
research/                  # Standalone research notebooks
  getting_started.ipynb    # Intro to QuantConnect research
data/                      # Local market data (download separately)
results/                   # Backtest results
scripts/                   # Utility scripts
lean.json                  # Lean engine configuration
```

## Quick Start

### DevContainer (Recommended)

Open in VS Code and use "Reopen in Container". The devcontainer provides:
- QuantConnect Lean engine (Python + .NET)
- JupyterLab on port 8888
- Full ML stack (PyTorch, JAX, scikit-learn, XGBoost)
- AI tools (Claude Code, Augment, Aider)
- Code quality tools (Black, isort, Pylint)

### Running a Backtest

```bash
# Download sample data first
./scripts/download_data.sh

# Run a backtest
lean backtest algorithms/sample_sma_crossover

# Or use the script
./scripts/run_backtest.sh algorithms/sample_sma_crossover
```

### Research Environment

```bash
./scripts/start_jupyter.sh
# Open http://localhost:8888/lab
```

## Creating a New Algorithm

1. Create a directory under `algorithms/`:
   ```bash
   mkdir algorithms/my_strategy
   ```

2. Create `main.py` with a `QCAlgorithm` subclass:
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
   lean backtest algorithms/my_strategy
   ```

## ML Stack

This playground includes a full ML stack pre-installed in the container:
- **Deep Learning**: PyTorch, JAX
- **Classical ML**: scikit-learn, XGBoost
- **Streaming ML**: River
- **Scientific Computing**: NumPy, SciPy, Pandas, StatsModels
- **Visualization**: Matplotlib, Seaborn, Plotly

## License

MIT License
