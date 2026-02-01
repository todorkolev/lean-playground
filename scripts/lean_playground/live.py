"""Direct Lean engine live trading runner.

Invokes dotnet QuantConnect.Lean.Launcher.dll with a live trading config,
bypassing the Lean CLI and its Docker requirements. Supports any brokerage
defined in Lean's modules registry.
"""

import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from lean_playground import LEAN_DATA_DIR, LEAN_LAUNCHER_DIR, LEAN_LAUNCHER_DLL, RESULTS_DIR
from lean_playground.brokerages import Brokerage, get_brokerage, list_brokerages
from lean_playground.config import write_config

# Standard live trading environment handlers (same for all brokerages)
_LIVE_ENVIRONMENT = {
    "live-mode": True,
    "setup-handler": "QuantConnect.Lean.Engine.Setup.BrokerageSetupHandler",
    "result-handler": "QuantConnect.Lean.Engine.Results.LiveTradingResultHandler",
    "data-feed-handler": "QuantConnect.Lean.Engine.DataFeeds.LiveTradingDataFeed",
    "real-time-handler": "QuantConnect.Lean.Engine.RealTime.LiveTradingRealTimeHandler",
    "transaction-handler": (
        "QuantConnect.Lean.Engine.TransactionHandlers.BrokerageTransactionHandler"
    ),
    "history-provider": [
        "QuantConnect.Lean.Engine.HistoricalData.BrokerageHistoryProvider",
        "QuantConnect.Lean.Engine.HistoricalData.SubscriptionDataReaderHistoryProvider",
    ],
}

# Base config for all live trading (same for all brokerages)
_BASE_LIVE_CONFIG = {
    "environment": "live",
    "algorithm-language": "Python",
    "close-automatically": False,  # Keep running for live trading
    "log-handler": "QuantConnect.Logging.CompositeLogHandler",
    "messaging-handler": "QuantConnect.Messaging.Messaging",
    "job-queue-handler": "QuantConnect.Queues.JobQueue",
    "api-handler": "QuantConnect.Api.Api",
    "map-file-provider": "QuantConnect.Data.Auxiliary.LocalDiskMapFileProvider",
    "factor-file-provider": "QuantConnect.Data.Auxiliary.LocalDiskFactorFileProvider",
    "data-provider": "QuantConnect.Lean.Engine.DataFeeds.DefaultDataProvider",
    "job-user-id": "0",
    "api-access-token": "",
}


def build_live_config(
    algorithm_file: Path,
    results_dir: Path,
    brokerage: Brokerage,
    brokerage_config: dict[str, str],
    *,
    paper: bool = True,
    cash_amount: float = 10000.0,
    cash_currency: str = "USDT",
    data_dir: Path | None = None,
    extra_python_paths: list[str] | None = None,
) -> dict:
    """Build a complete engine config for live/paper trading.

    Args:
        algorithm_file: Absolute path to the algorithm .py file.
        results_dir: Directory where live results will be written.
        brokerage: Brokerage definition object.
        brokerage_config: Dict of brokerage-specific config keys and values.
        paper: Use testnet/paper trading if True (where supported).
        cash_amount: Initial cash balance amount.
        cash_currency: Currency for initial cash.
        data_dir: Market data directory. Defaults to /Lean/Data.
        extra_python_paths: Additional Python import paths.

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

    # Build the environment config
    live_env = dict(_LIVE_ENVIRONMENT)
    live_env["live-mode-brokerage"] = brokerage.brokerage_class
    live_env["data-queue-handler"] = [brokerage.data_queue_handler]

    # Build base config
    config = dict(_BASE_LIVE_CONFIG)
    config.update({
        "algorithm-type-name": module_name,
        "algorithm-location": str(algorithm_file),
        "data-folder": str(effective_data_dir),
        "results-destination-folder": str(results_dir),
        "object-store-root": str(results_dir / "storage"),
        "composer-dll-directory": str(LEAN_LAUNCHER_DIR),
        "python-additional-paths": python_paths,
        "environments": {
            "live": live_env,
        },
    })

    # Add brokerage-specific configuration
    config.update(brokerage_config)

    # Set paper/live mode if brokerage supports it
    if brokerage.testnet_config_id:
        config[brokerage.testnet_config_id] = "paper" if paper else "live"

    # Initial cash balance
    config["live-cash-balance"] = f"{cash_currency}:{cash_amount}"

    # Algorithm ID for live trading
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    config["algorithm-id"] = f"L-{timestamp}"

    return config


def run_live(
    project_path: Path,
    brokerage_name: str = "binance",
    *,
    paper: bool = True,
    cash_amount: float = 10000.0,
    cash_currency: str = "USDT",
) -> int:
    """Run live/paper trading for the given algorithm project.

    Args:
        project_path: Path to the algorithm project directory.
            Must contain a main.py file.
        brokerage_name: Name of the brokerage (e.g., "binance", "alpaca").
        paper: Use testnet/paper trading if True.
        cash_amount: Initial cash balance amount.
        cash_currency: Currency for initial cash.

    Returns:
        The engine process exit code (0 = success).

    Raises:
        FileNotFoundError: If project_path or main.py does not exist.
        RuntimeError: If the Lean engine DLL is not found.
        ValueError: If brokerage credentials are not provided.
    """
    project_path = project_path.resolve()
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project directory not found: {project_path}")

    algorithm_file = project_path / "main.py"
    if not algorithm_file.exists():
        raise FileNotFoundError(
            f"No main.py found in {project_path}. "
            "Each algorithm project must have a main.py entry point."
        )

    if not LEAN_LAUNCHER_DLL.exists():
        raise RuntimeError(
            f"Lean engine not found at {LEAN_LAUNCHER_DLL}. "
            "Ensure you are running inside the Lean devcontainer."
        )

    # Get brokerage definition
    brokerage = get_brokerage(brokerage_name)

    # Get brokerage config from environment variables
    try:
        brokerage_config = brokerage.get_config_from_env()
    except ValueError as e:
        # Add helpful info about where to get credentials
        testnet_info = ""
        if brokerage.supports_testnet and paper:
            testnet_info = "\n\nFor paper trading, you may need testnet credentials."
        raise ValueError(str(e) + testnet_info) from None

    # Set up results directory
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    project_name = project_path.name
    mode = "paper" if paper else "live"
    results_dir = RESULTS_DIR / project_name / f"{mode}-{timestamp}"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Build config
    config = build_live_config(
        algorithm_file,
        results_dir,
        brokerage,
        brokerage_config,
        paper=paper,
        cash_amount=cash_amount,
        cash_currency=cash_currency,
    )
    config_path = write_config(config)

    # Print summary
    print(f"Project:      {project_name}")
    print(f"Algorithm:    {algorithm_file}")
    print(f"Brokerage:    {brokerage.display_name}")
    print(f"Mode:         {'Paper Trading' if paper else 'LIVE TRADING'}")
    print(f"Cash:         {cash_amount} {cash_currency}")
    print(f"Results:      {results_dir}")
    print("-" * 60)

    # Safety warning for live trading
    if not paper:
        print("\n⚠️  WARNING: LIVE TRADING MODE - Real funds will be used!")
        print("    Press Ctrl+C within 5 seconds to cancel...")
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            print("\nCancelled.")
            _cleanup_config(config_path)
            return 1
        print()

    print("Starting Lean engine... (Press Ctrl+C to stop)")
    print("-" * 60)

    process = None
    try:
        process = subprocess.Popen(
            ["dotnet", str(LEAN_LAUNCHER_DLL), "--config", str(config_path)],
            cwd=str(LEAN_LAUNCHER_DIR),
        )
        return process.wait()
    except KeyboardInterrupt:
        print("\n\nStopping live trading...")
        if process:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait()
        return 0
    finally:
        _cleanup_config(config_path)


def _cleanup_config(config_path: Path) -> None:
    """Remove the temporary config file, ignoring errors."""
    try:
        config_path.unlink(missing_ok=True)
    except OSError:
        pass


def print_available_brokerages() -> None:
    """Print list of available brokerages."""
    print("Available brokerages:\n")
    for brokerage_id, display_name in list_brokerages():
        testnet = ""
        try:
            b = get_brokerage(brokerage_id)
            if b.supports_testnet:
                testnet = " (supports paper trading)"
        except ValueError:
            pass
        print(f"  {brokerage_id:25} {display_name}{testnet}")
    print("\nUse: lp live <project> --brokerage <name>")


def main() -> None:
    """CLI entry point for standalone usage."""
    if len(sys.argv) < 2:
        print(
            "Usage: python -m lean_playground.live <project_path> --brokerage <name>",
            file=sys.stderr,
        )
        print("\nAvailable brokerages:", file=sys.stderr)
        for brokerage_id, display_name in list_brokerages():
            print(f"  {brokerage_id}: {display_name}", file=sys.stderr)
        sys.exit(2)

    if sys.argv[1] == "--list-brokerages":
        print_available_brokerages()
        sys.exit(0)

    project_path = Path(sys.argv[1])
    brokerage_name = "binance"  # Default

    # Parse simple args
    for i, arg in enumerate(sys.argv):
        if arg == "--brokerage" and i + 1 < len(sys.argv):
            brokerage_name = sys.argv[i + 1]

    exit_code = run_live(project_path, brokerage_name)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
