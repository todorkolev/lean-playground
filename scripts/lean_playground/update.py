"""Update from upstream repository.

Syncs the local fork with the upstream lean-playground repository.
"""

import subprocess
import sys
from pathlib import Path

from lean_playground import SCRIPTS_DIR


def update_from_upstream(merge: bool = False) -> int:
    """Sync with upstream repository using rebase or merge.

    Args:
        merge: If True, use merge mode. If False (default), use rebase mode.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    script_path = SCRIPTS_DIR / "pull-from-upstream.sh"

    if not script_path.exists():
        print(f"Error: Update script not found: {script_path}", file=sys.stderr)
        return 1

    cmd = [str(script_path)]
    if merge:
        cmd.append("--merge")

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running update: {e}", file=sys.stderr)
        return 1
