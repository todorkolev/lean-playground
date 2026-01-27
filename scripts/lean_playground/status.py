"""Workspace status reporter.

Displays the current state of the Lean Playground workspace including
paths, data availability, and authentication status.
"""

import shutil
from pathlib import Path

from lean_playground import (
    ALGORITHM_EXAMPLES_DIR,
    ALGORITHMS_DIR,
    LEAN_DATA_DIR,
    LEAN_LAUNCHER_DLL,
    RESULTS_DIR,
    WORKSPACE_DIR,
)


def print_status() -> None:
    """Print a summary of the workspace status."""
    print("Lean Playground Status")
    print("=" * 50)

    _print_section("Engine", [
        ("Lean engine", _check_path(LEAN_LAUNCHER_DLL)),
        ("Data directory", _check_path(LEAN_DATA_DIR)),
        ("Algorithm examples", _check_algorithm_examples()),
    ])

    _print_section("Workspace", [
        ("Workspace root", str(WORKSPACE_DIR)),
        ("Algorithms", _count_projects()),
        ("Results", _check_path(RESULTS_DIR)),
    ])

    _print_section("QuantConnect CLI (optional)", [
        ("lean CLI", _check_lean_cli()),
        ("lean.json", _check_lean_json()),
    ])


def _print_section(title: str, items: list[tuple[str, str]]) -> None:
    """Print a labeled section with key-value items."""
    print(f"\n{title}:")
    for label, value in items:
        print(f"  {label:.<30} {value}")


def _check_path(path: Path) -> str:
    """Check if a path exists and return a status string."""
    if path.exists():
        return str(path)
    return f"NOT FOUND ({path})"


def _check_algorithm_examples() -> str:
    """Check algorithm examples availability."""
    if not ALGORITHM_EXAMPLES_DIR.exists():
        return "NOT FOUND (rebuild container)"
    count = sum(1 for f in ALGORITHM_EXAMPLES_DIR.glob("*.py") if not f.name.startswith("_"))
    return f"{count} algorithms at {ALGORITHM_EXAMPLES_DIR}"


def _count_projects() -> str:
    """Count algorithm projects in the workspace."""
    if not ALGORITHMS_DIR.exists():
        return "No algorithms directory"
    projects = [
        d for d in ALGORITHMS_DIR.iterdir()
        if d.is_dir() and (d / "main.py").exists()
    ]
    return f"{len(projects)} project(s) in {ALGORITHMS_DIR}"


def _check_lean_cli() -> str:
    """Check if the lean CLI is available."""
    if shutil.which("lean"):
        return "installed (use 'lean login' to authenticate)"
    return "not installed"


def _check_lean_json() -> str:
    """Check for lean.json configuration."""
    lean_json = WORKSPACE_DIR / "lean.json"
    if lean_json.exists():
        return "present (Lean CLI configured)"
    return "not present (run 'lean login && lean init' to set up)"
