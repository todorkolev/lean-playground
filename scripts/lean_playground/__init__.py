"""Lean Playground — local-first workspace tooling for QuantConnect Lean.

Provides direct engine invocation for backtesting, project scaffolding,
and algorithm example browsing without requiring QuantConnect authentication.
"""

from pathlib import Path

LEAN_DATA_DIR = Path("/Lean/Data")
LEAN_LAUNCHER_DIR = Path("/Lean/Launcher/bin/Debug")
LEAN_LAUNCHER_DLL = LEAN_LAUNCHER_DIR / "QuantConnect.Lean.Launcher.dll"
ALGORITHM_EXAMPLES_DIR = Path("/Lean/Algorithm.Python")

# Derive workspace directory from this file's location
# scripts/lean_playground/__init__.py -> scripts -> workspace
_SCRIPT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = _SCRIPT_DIR.parent
ALGORITHMS_DIR = WORKSPACE_DIR / "algorithms"
RESULTS_DIR = WORKSPACE_DIR / "results"
