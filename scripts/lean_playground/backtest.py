"""Direct Lean engine backtest runner.

Invokes dotnet QuantConnect.Lean.Launcher.dll with a generated config,
bypassing the Lean CLI and its authentication requirements.
"""

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from lean_playground import LEAN_LAUNCHER_DIR, LEAN_LAUNCHER_DLL, RESULTS_DIR
from lean_playground.config import build_backtest_config, write_config


def run_backtest(project_path: Path) -> int:
    """Run a backtest for the given algorithm project.

    Args:
        project_path: Path to the algorithm project directory.
            Must contain a main.py file.

    Returns:
        The engine process exit code (0 = success).

    Raises:
        FileNotFoundError: If project_path or main.py does not exist.
        RuntimeError: If the Lean engine DLL is not found.
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

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    project_name = project_path.name
    results_dir = RESULTS_DIR / project_name / timestamp
    results_dir.mkdir(parents=True, exist_ok=True)

    config = build_backtest_config(algorithm_file, results_dir)
    config_path = write_config(config)

    print(f"Project:  {project_name}")
    print(f"Algorithm: {algorithm_file}")
    print(f"Results:  {results_dir}")
    print(f"Config:   {config_path}")
    print("-" * 60)

    try:
        result = subprocess.run(
            ["dotnet", str(LEAN_LAUNCHER_DLL), "--config", str(config_path)],
            cwd=str(LEAN_LAUNCHER_DIR),
        )
        return result.returncode
    finally:
        _cleanup_config(config_path)


def _cleanup_config(config_path: Path) -> None:
    """Remove the temporary config file, ignoring errors."""
    try:
        config_path.unlink(missing_ok=True)
    except OSError:
        pass


def main() -> None:
    """CLI entry point for standalone usage: python -m lean_playground.backtest <project>."""
    if len(sys.argv) != 2:
        print("Usage: python -m lean_playground.backtest <project_path>", file=sys.stderr)
        sys.exit(2)

    project_path = Path(sys.argv[1])
    exit_code = run_backtest(project_path)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
