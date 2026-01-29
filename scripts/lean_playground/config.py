"""Engine configuration builder for direct Lean engine invocation.

Generates the config.json required by dotnet QuantConnect.Lean.Launcher.dll
to run a Python backtest without the Lean CLI or QuantConnect authentication.
"""

import json
import tempfile
from pathlib import Path

from lean_playground import LEAN_DATA_DIR, LEAN_LAUNCHER_DIR

_BACKTESTING_ENVIRONMENT = {
    "live-mode": False,
    "setup-handler": "QuantConnect.Lean.Engine.Setup.ConsoleSetupHandler",
    "result-handler": "QuantConnect.Lean.Engine.Results.BacktestingResultHandler",
    "data-feed-handler": "QuantConnect.Lean.Engine.DataFeeds.FileSystemDataFeed",
    "real-time-handler": "QuantConnect.Lean.Engine.RealTime.BacktestingRealTimeHandler",
    "transaction-handler": (
        "QuantConnect.Lean.Engine.TransactionHandlers"
        ".BacktestingTransactionHandler"
    ),
    "history-provider": (
        "QuantConnect.Lean.Engine.HistoricalData"
        ".SubscriptionDataReaderHistoryProvider"
    ),
}

_BASE_CONFIG = {
    "environment": "backtesting",
    "algorithm-language": "Python",
    "close-automatically": True,
    "log-handler": "QuantConnect.Logging.CompositeLogHandler",
    "messaging-handler": "QuantConnect.Messaging.Messaging",
    "job-queue-handler": "QuantConnect.Queues.JobQueue",
    "api-handler": "QuantConnect.Api.Api",
    "map-file-provider": "QuantConnect.Data.Auxiliary.LocalDiskMapFileProvider",
    "factor-file-provider": (
        "QuantConnect.Data.Auxiliary.LocalDiskFactorFileProvider"
    ),
    "data-provider": "QuantConnect.Lean.Engine.DataFeeds.DefaultDataProvider",
    "job-user-id": "0",
    "api-access-token": "",
    "environments": {
        "backtesting": _BACKTESTING_ENVIRONMENT,
    },
}


def build_backtest_config(
    algorithm_file: Path,
    results_dir: Path,
    *,
    data_dir: Path | None = None,
    extra_python_paths: list[str] | None = None,
    parameters: dict[str, str] | None = None,
) -> dict:
    """Build a complete engine config for a Python backtest.

    Args:
        algorithm_file: Absolute path to the algorithm .py file.
        results_dir: Directory where backtest results will be written.
        data_dir: Market data directory. Defaults to /Lean/Data.
        extra_python_paths: Additional Python import paths beyond the
            algorithm's parent directory.
        parameters: Dictionary of algorithm parameters to pass via
            self.get_parameter() in the algorithm.

    Returns:
        A dict suitable for JSON serialization as the engine config.

    Raises:
        FileNotFoundError: If the algorithm file does not exist.
        ValueError: If the algorithm file is not a .py file.
    """
    algorithm_file = algorithm_file.resolve()
    if not algorithm_file.exists():
        raise FileNotFoundError(f"Algorithm file not found: {algorithm_file}")
    if algorithm_file.suffix != ".py":
        raise ValueError(f"Expected a .py file, got: {algorithm_file}")

    effective_data_dir = data_dir or LEAN_DATA_DIR
    module_name = algorithm_file.stem
    project_dir = str(algorithm_file.parent)

    python_paths = [project_dir]
    if extra_python_paths:
        python_paths.extend(extra_python_paths)

    config = dict(_BASE_CONFIG)
    config.update({
        "algorithm-type-name": module_name,
        "algorithm-location": str(algorithm_file),
        "data-folder": str(effective_data_dir),
        "results-destination-folder": str(results_dir),
        "object-store-root": str(results_dir / "storage"),
        "composer-dll-directory": str(LEAN_LAUNCHER_DIR),
        "python-additional-paths": python_paths,
    })

    if parameters:
        config["parameters"] = parameters

    return config


def write_config(config: dict) -> Path:
    """Write an engine config dict to a temporary JSON file.

    Args:
        config: The engine configuration dictionary.

    Returns:
        Path to the written temporary config file. The caller is responsible
        for cleanup, though the OS temp directory handles eventual deletion.
    """
    fd, path = tempfile.mkstemp(suffix=".json", prefix="lp-config-")
    with open(fd, "w") as f:
        json.dump(config, f, indent=2)
    return Path(path)
