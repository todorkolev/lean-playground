"""Smoke tests to verify the Lean playground environment."""

import os
import py_compile

import pytest


ALGORITHMS_DIR = "algorithms"


def test_ml_imports():
    """Verify that core ML packages are available."""
    import numpy as np
    import pandas as pd
    import sklearn
    import torch

    assert np.__version__
    assert pd.__version__
    assert sklearn.__version__
    assert torch.__version__


def _discover_algorithm_directories():
    """Find all algorithm directories containing main.py."""
    if not os.path.isdir(ALGORITHMS_DIR):
        return []
    return [
        name
        for name in sorted(os.listdir(ALGORITHMS_DIR))
        if os.path.isfile(os.path.join(ALGORITHMS_DIR, name, "main.py"))
    ]


@pytest.mark.parametrize("algo_name", _discover_algorithm_directories())
def test_algorithm_syntax(algo_name):
    """Verify each algorithm file has valid Python syntax."""
    filepath = os.path.join(ALGORITHMS_DIR, algo_name, "main.py")
    py_compile.compile(filepath, doraise=True)
