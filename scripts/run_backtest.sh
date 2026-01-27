#!/bin/bash
# Run a Lean backtest for a given algorithm project
# Usage: ./scripts/run_backtest.sh <project_path>
# Example: ./scripts/run_backtest.sh algorithms/sample_sma_crossover

set -euo pipefail

PROJECT_PATH="${1:?Usage: $0 <project_path>}"

if [ ! -d "$PROJECT_PATH" ]; then
    echo "Error: Project directory '$PROJECT_PATH' does not exist."
    exit 1
fi

if [ ! -f "$PROJECT_PATH/main.py" ]; then
    echo "Error: No main.py found in '$PROJECT_PATH'."
    exit 1
fi

echo "Running backtest for: $PROJECT_PATH"

if command -v lean &> /dev/null; then
    lean backtest "$PROJECT_PATH" --output "$PROJECT_PATH/backtests"
else
    echo "Error: Lean CLI not found. Install with: pip install lean"
    exit 1
fi

echo "Backtest complete. Results in: $PROJECT_PATH/backtests/"
