"""Jupyter Lab launcher with Lean research environment configuration.

Ensures the QuantBook config is properly set up and launches Jupyter Lab
with access to the Lean engine and market data.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from lean_playground import LEAN_DATA_DIR, LEAN_LAUNCHER_DIR, WORKSPACE_DIR

_RESEARCH_DIR = WORKSPACE_DIR / "research"
_NOTEBOOKS_CONFIG = _RESEARCH_DIR / "config.json"

_QUANTBOOK_CONFIG = {
    "data-folder": str(LEAN_DATA_DIR),
    "composer-dll-directory": str(LEAN_LAUNCHER_DIR),
    "algorithm-language": "Python",
    "messaging-handler": "QuantConnect.Messaging.Messaging",
    "job-queue-handler": "QuantConnect.Queues.JobQueue",
    "api-handler": "QuantConnect.Api.Api",
}


def ensure_notebook_config() -> Path:
    """Create or update the Notebooks/config.json for QuantBook.

    Returns:
        Path to the config file.
    """
    _RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

    if _NOTEBOOKS_CONFIG.exists():
        existing = json.loads(_NOTEBOOKS_CONFIG.read_text())
        existing.update(_QUANTBOOK_CONFIG)
        config = existing
    else:
        config = _QUANTBOOK_CONFIG

    _NOTEBOOKS_CONFIG.write_text(json.dumps(config, indent=2) + "\n")
    return _NOTEBOOKS_CONFIG


def launch_jupyter(
    *,
    port: int = 8888,
    notebook_dir: str | None = None,
) -> int:
    """Launch Jupyter Lab with the Lean research environment.

    Args:
        port: Port to serve Jupyter on. Defaults to 8888.
        notebook_dir: Directory to use as the notebook root.
            Defaults to the workspace root.

    Returns:
        The Jupyter process exit code.
    """
    ensure_notebook_config()

    effective_dir = notebook_dir or str(WORKSPACE_DIR)

    cmd = [
        "jupyter", "lab",
        f"--ip=0.0.0.0",
        f"--port={port}",
        "--no-browser",
        "--allow-root",
        f"--notebook-dir={effective_dir}",
        "--LabApp.token=",
    ]

    print(f"Starting Jupyter Lab on port {port}...")
    print(f"Notebook dir: {effective_dir}")
    print(f"QuantBook config: {_NOTEBOOKS_CONFIG}")

    env = os.environ.copy()
    env.setdefault("PYTHONPATH", "")
    if str(LEAN_LAUNCHER_DIR) not in env["PYTHONPATH"]:
        env["PYTHONPATH"] = f"{LEAN_LAUNCHER_DIR}:{env['PYTHONPATH']}"

    result = subprocess.run(cmd, env=env)
    return result.returncode
