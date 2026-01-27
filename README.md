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
data/                      # Local market data
results/                   # Backtest results
scripts/                   # Utility scripts
lean.json                  # Lean engine configuration
```

Reference algorithms from the Lean repo are available inside the container at `/Lean/Algorithm.Python/`.

## Quick Start

### DevContainer (Recommended)

Open in VS Code and use "Reopen in Container". The devcontainer provides:
- QuantConnect Lean engine (Python + .NET)
- Lean CLI for backtesting and project management
- JupyterLab on port 8888
- Full ML stack (PyTorch, JAX, scikit-learn, XGBoost)
- AI tools (Claude Code, Augment, Aider)
- Code quality tools (Black, isort, Pylint)
- Docker-in-Docker for running backtests

### Initialize Workspace

```bash
# Download sample market data
lean init
```

### Running a Backtest

```bash
lean backtest algorithms/sample_sma_crossover
```

### Research Environment

```bash
./scripts/start_jupyter.sh
# Open http://localhost:8888/lab
```

## Creating a New Algorithm

1. Create a project using the Lean CLI:
   ```bash
   lean create-project algorithms/my_strategy --language python
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
   lean backtest algorithms/my_strategy
   ```

### Using Reference Algorithms

The container includes ~450 Python algorithm examples from the Lean repo:

```bash
# Browse reference algorithms
ls /Lean/Algorithm.Python/

# Copy one into a new project
lean create-project algorithms/macd_trend --language python
cp /Lean/Algorithm.Python/MACDTrendAlgorithm.py algorithms/macd_trend/main.py
lean backtest algorithms/macd_trend
```

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
