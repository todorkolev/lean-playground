"""Tests for the lean_playground package (lp CLI tooling)."""

import json
import os
import shutil
from pathlib import Path

import pytest

from lean_playground import (
    LEAN_DATA_DIR,
    LEAN_LAUNCHER_DLL,
    LEAN_LAUNCHER_DIR,
)
from lean_playground.config import build_backtest_config, write_config
from lean_playground.project import _to_class_name, create_project


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_algorithms(tmp_path):
    """Create a temporary algorithms directory with a sample project."""
    algo_dir = tmp_path / "algorithms" / "test_strategy"
    algo_dir.mkdir(parents=True)
    main_py = algo_dir / "main.py"
    main_py.write_text(
        "from AlgorithmImports import *\n\n"
        "class TestStrategy(QCAlgorithm):\n"
        "    def initialize(self):\n"
        "        pass\n"
        "    def on_data(self, data):\n"
        "        pass\n"
    )
    return tmp_path


# ---------------------------------------------------------------------------
# config.py tests
# ---------------------------------------------------------------------------

class TestBuildBacktestConfig:
    """Tests for build_backtest_config."""

    def test_produces_valid_config(self, tmp_algorithms):
        algo_file = tmp_algorithms / "algorithms" / "test_strategy" / "main.py"
        results_dir = tmp_algorithms / "results" / "test_strategy"

        config = build_backtest_config(algo_file, results_dir)

        assert config["environment"] == "backtesting"
        assert config["algorithm-language"] == "Python"
        assert config["algorithm-type-name"] == "main"
        assert config["algorithm-location"] == str(algo_file)
        assert config["data-folder"] == str(LEAN_DATA_DIR)
        assert config["results-destination-folder"] == str(results_dir)
        assert config["composer-dll-directory"] == str(LEAN_LAUNCHER_DIR)
        assert config["close-automatically"] is True
        assert str(algo_file.parent) in config["python-additional-paths"]

    def test_custom_data_dir(self, tmp_algorithms):
        algo_file = tmp_algorithms / "algorithms" / "test_strategy" / "main.py"
        results_dir = tmp_algorithms / "results"
        custom_data = Path("/custom/data")

        config = build_backtest_config(algo_file, results_dir, data_dir=custom_data)

        assert config["data-folder"] == str(custom_data)

    def test_extra_python_paths(self, tmp_algorithms):
        algo_file = tmp_algorithms / "algorithms" / "test_strategy" / "main.py"
        results_dir = tmp_algorithms / "results"

        config = build_backtest_config(
            algo_file,
            results_dir,
            extra_python_paths=["/extra/path"],
        )

        assert "/extra/path" in config["python-additional-paths"]

    def test_backtesting_environment_handlers(self, tmp_algorithms):
        algo_file = tmp_algorithms / "algorithms" / "test_strategy" / "main.py"
        results_dir = tmp_algorithms / "results"

        config = build_backtest_config(algo_file, results_dir)

        env = config["environments"]["backtesting"]
        assert env["live-mode"] is False
        assert "BacktestingResultHandler" in env["result-handler"]
        assert "FileSystemDataFeed" in env["data-feed-handler"]
        assert "BacktestingTransactionHandler" in env["transaction-handler"]

    def test_raises_on_missing_file(self, tmp_path):
        missing = tmp_path / "nonexistent.py"
        with pytest.raises(FileNotFoundError):
            build_backtest_config(missing, tmp_path / "results")

    def test_raises_on_non_python_file(self, tmp_path):
        txt_file = tmp_path / "algo.txt"
        txt_file.write_text("not python")
        with pytest.raises(ValueError, match="Expected a .py file"):
            build_backtest_config(txt_file, tmp_path / "results")


class TestWriteConfig:
    """Tests for write_config."""

    def test_writes_valid_json(self, tmp_algorithms):
        algo_file = tmp_algorithms / "algorithms" / "test_strategy" / "main.py"
        results_dir = tmp_algorithms / "results"
        config = build_backtest_config(algo_file, results_dir)

        path = write_config(config)

        try:
            assert path.exists()
            assert path.suffix == ".json"
            loaded = json.loads(path.read_text())
            assert loaded["algorithm-type-name"] == "main"
        finally:
            path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# project.py tests
# ---------------------------------------------------------------------------

class TestToClassName:
    """Tests for _to_class_name."""

    def test_snake_case(self):
        assert _to_class_name("my_strategy") == "MyStrategy"

    def test_kebab_case(self):
        assert _to_class_name("my-strategy") == "MyStrategy"

    def test_single_word(self):
        assert _to_class_name("strategy") == "Strategy"

    def test_mixed_separators(self):
        assert _to_class_name("my_cool-strategy") == "MyCoolStrategy"


class TestCreateProject:
    """Tests for create_project."""

    def test_creates_project_directory(self, tmp_path, monkeypatch):
        monkeypatch.setattr("lean_playground.project.ALGORITHMS_DIR", tmp_path / "algorithms")
        (tmp_path / "algorithms").mkdir()

        result = create_project("test_algo")

        assert result.exists()
        assert (result / "main.py").exists()
        assert (result / "research.ipynb").exists()

    def test_main_py_has_correct_class_name(self, tmp_path, monkeypatch):
        monkeypatch.setattr("lean_playground.project.ALGORITHMS_DIR", tmp_path / "algorithms")
        (tmp_path / "algorithms").mkdir()

        create_project("sma_crossover")

        content = (tmp_path / "algorithms" / "sma_crossover" / "main.py").read_text()
        assert "class SmaCrossover(QCAlgorithm):" in content

    def test_research_notebook_is_valid_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr("lean_playground.project.ALGORITHMS_DIR", tmp_path / "algorithms")
        (tmp_path / "algorithms").mkdir()

        create_project("test_nb")

        nb_path = tmp_path / "algorithms" / "test_nb" / "research.ipynb"
        notebook = json.loads(nb_path.read_text())
        assert notebook["nbformat"] == 4
        assert len(notebook["cells"]) >= 2

    def test_raises_on_existing_project(self, tmp_path, monkeypatch):
        monkeypatch.setattr("lean_playground.project.ALGORITHMS_DIR", tmp_path / "algorithms")
        algo_dir = tmp_path / "algorithms" / "existing"
        algo_dir.mkdir(parents=True)

        with pytest.raises(FileExistsError):
            create_project("existing")


# ---------------------------------------------------------------------------
# Engine availability (environment check)
# ---------------------------------------------------------------------------

class TestEngineAvailability:
    """Verify the Lean engine is available in the container."""

    def test_lean_engine_dll_exists(self):
        assert LEAN_LAUNCHER_DLL.exists(), (
            f"Lean engine not found at {LEAN_LAUNCHER_DLL}"
        )

    def test_lean_data_directory_exists(self):
        assert LEAN_DATA_DIR.exists(), (
            f"Lean data directory not found at {LEAN_DATA_DIR}"
        )

    def test_dotnet_available(self):
        assert shutil.which("dotnet"), "dotnet runtime not found on PATH"
