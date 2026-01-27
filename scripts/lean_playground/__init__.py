"""Lean Playground — local-first workspace tooling for QuantConnect Lean.

Provides direct engine invocation for backtesting, project scaffolding,
and algorithm example browsing without requiring QuantConnect authentication.
"""

from pathlib import Path

LEAN_DATA_DIR = Path("/Lean/Data")
LEAN_LAUNCHER_DIR = Path("/Lean/Launcher/bin/Debug")
LEAN_LAUNCHER_DLL = LEAN_LAUNCHER_DIR / "QuantConnect.Lean.Launcher.dll"
ALGORITHM_EXAMPLES_DIR = Path("/Lean/Algorithm.Python")
WORKSPACE_DIR = Path("/workspaces/lean-playground")
ALGORITHMS_DIR = WORKSPACE_DIR / "algorithms"
RESULTS_DIR = WORKSPACE_DIR / "results"
