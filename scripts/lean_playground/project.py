"""Algorithm project scaffolding.

Creates new algorithm projects from templates or by copying
algorithm examples from the Lean repository.
"""

import json
import re
import shutil
from pathlib import Path

from lean_playground import ALGORITHMS_DIR, ALGORITHM_EXAMPLES_DIR

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _to_class_name(project_name: str) -> str:
    """Convert a snake_case or kebab-case project name to CamelCase.

    Args:
        project_name: The project directory name (e.g., "my_algo" or "my-algo").

    Returns:
        A CamelCase class name (e.g., "MyAlgo").
    """
    parts = re.split(r"[-_]+", project_name)
    return "".join(part.capitalize() for part in parts if part)


def create_project(
    name: str,
    *,
    from_reference: str | None = None,
) -> Path:
    """Create a new algorithm project.

    Args:
        name: Project name or path. If a plain name, creates under
            algorithms/. If a path like "algorithms/my_algo", uses it directly.
        from_reference: Name of an algorithm example (without .py) to copy
            from /Lean/Algorithm.Python/. If None, uses the default template.

    Returns:
        Path to the created project directory.

    Raises:
        FileExistsError: If the project directory already exists.
        FileNotFoundError: If the algorithm example is not found.
    """
    project_path = _resolve_project_path(name)

    if project_path.exists():
        raise FileExistsError(f"Project already exists: {project_path}")

    project_path.mkdir(parents=True)
    project_name = project_path.name

    if from_reference:
        _copy_algorithm_example(from_reference, project_path)
    else:
        _generate_from_template(project_name, project_path)

    _generate_research_notebook(project_name, project_path)

    print(f"Created project: {project_path}")
    print(f"  Algorithm: {project_path / 'main.py'}")
    print(f"  Notebook:  {project_path / 'research.ipynb'}")
    return project_path


def _resolve_project_path(name: str) -> Path:
    """Resolve a project name to an absolute path under algorithms/."""
    path = Path(name)
    if path.is_absolute():
        return path
    # If the name already starts with "algorithms/", use it as-is
    if path.parts and path.parts[0] == "algorithms":
        return ALGORITHMS_DIR.parent / path
    return ALGORITHMS_DIR / name


def _copy_algorithm_example(example_name: str, project_path: Path) -> None:
    """Copy an algorithm example into the project as main.py."""
    # Try exact match first, then with .py extension
    source = ALGORITHM_EXAMPLES_DIR / f"{example_name}.py"
    if not source.exists():
        source = ALGORITHM_EXAMPLES_DIR / example_name
    if not source.exists():
        available = _list_example_names()
        raise FileNotFoundError(
            f"Algorithm example not found: {example_name}\n"
            f"Available: {', '.join(available[:10])}..."
        )
    shutil.copy2(source, project_path / "main.py")


def _generate_from_template(project_name: str, project_path: Path) -> None:
    """Generate main.py from the algorithm template."""
    template_file = _TEMPLATES_DIR / "main.py.template"
    template = template_file.read_text()
    class_name = _to_class_name(project_name)
    content = template.format(class_name=class_name)
    (project_path / "main.py").write_text(content)


def _generate_research_notebook(project_name: str, project_path: Path) -> None:
    """Generate research.ipynb from the notebook template."""
    template_file = _TEMPLATES_DIR / "research.ipynb.template"
    template_text = template_file.read_text()
    content = template_text.replace("{project_name}", project_name)
    notebook = json.loads(content)
    (project_path / "research.ipynb").write_text(
        json.dumps(notebook, indent=1) + "\n"
    )


def _list_example_names() -> list[str]:
    """List available algorithm example names (without .py extension)."""
    if not ALGORITHM_EXAMPLES_DIR.exists():
        return []
    return sorted(
        f.stem
        for f in ALGORITHM_EXAMPLES_DIR.iterdir()
        if f.suffix == ".py" and f.name != "__init__.py"
    )
