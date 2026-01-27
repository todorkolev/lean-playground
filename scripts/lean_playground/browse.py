"""Algorithm examples browser.

Lists and searches the ~500 Python algorithm examples from the Lean
repository available at /Lean/Algorithm.Python/.
"""

import ast
import re
from pathlib import Path

from lean_playground import ALGORITHM_EXAMPLES_DIR


def browse(keyword: str | None = None) -> list[dict[str, str]]:
    """List algorithm examples, optionally filtered by keyword.

    Args:
        keyword: Case-insensitive keyword to filter by filename or docstring.
            If None, returns all algorithms.

    Returns:
        A list of dicts with keys 'name', 'file', and 'description'.
    """
    if not ALGORITHM_EXAMPLES_DIR.exists():
        print(
            f"Algorithm examples not found at {ALGORITHM_EXAMPLES_DIR}.\n"
            "They are downloaded during Docker build. "
            "Rebuild the container to get them."
        )
        return []

    results = []
    for py_file in sorted(ALGORITHM_EXAMPLES_DIR.glob("*.py")):
        if py_file.name.startswith("_"):
            continue

        name = py_file.stem
        description = _extract_docstring(py_file)

        if keyword:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            if not pattern.search(name) and not pattern.search(description):
                continue

        results.append({
            "name": name,
            "file": str(py_file),
            "description": description,
        })

    return results


def print_browse_results(results: list[dict[str, str]]) -> None:
    """Print browse results in a readable format."""
    if not results:
        print("No matching algorithms found.")
        return

    name_width = max(len(r["name"]) for r in results)
    print(f"{'Algorithm':<{name_width}}  Description")
    print(f"{'-' * name_width}  {'-' * 50}")
    for r in results:
        desc = r["description"][:70] if r["description"] else ""
        print(f"{r['name']:<{name_width}}  {desc}")
    print(f"\n{len(results)} algorithm(s) found.")


def _extract_docstring(py_file: Path) -> str:
    """Extract the first line of the module or first class docstring.

    Args:
        py_file: Path to a Python source file.

    Returns:
        The first line of the docstring, or empty string if none found.
    """
    try:
        source = py_file.read_text(errors="replace")
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return ""

    # Try module-level docstring
    doc = ast.get_docstring(tree)
    if doc:
        return doc.split("\n")[0].strip()

    # Try first class docstring
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            class_doc = ast.get_docstring(node)
            if class_doc:
                return class_doc.split("\n")[0].strip()

    return ""
