"""Smoke tests to verify the Lean playground environment."""

import py_compile


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


def test_sample_algorithm_syntax():
    """Verify the sample algorithm file has valid Python syntax."""
    py_compile.compile("algorithms/sample_sma_crossover/main.py", doraise=True)
