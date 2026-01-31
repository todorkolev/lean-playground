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


# ---------------------------------------------------------------------------
# lean_writer.py tests
# ---------------------------------------------------------------------------

class TestLeanWriter:
    """Tests for Lean data writer."""

    def test_resolution_from_interval(self):
        from lean_playground.lean_writer import Resolution

        assert Resolution.from_interval("1m") == Resolution.MINUTE
        assert Resolution.from_interval("1h") == Resolution.HOUR
        assert Resolution.from_interval("1d") == Resolution.DAILY
        assert Resolution.from_interval("4h") == Resolution.HOUR

    def test_write_daily_bars(self, tmp_path):
        from datetime import datetime
        from lean_playground.lean_writer import (
            LeanDataWriter,
            BarData,
            Resolution,
            AssetClass,
        )

        writer = LeanDataWriter(tmp_path)
        bars = [
            BarData(datetime(2024, 1, 1), 100.0, 105.0, 99.0, 103.0, 1000.0),
            BarData(datetime(2024, 1, 2), 103.0, 108.0, 102.0, 106.0, 1200.0),
        ]

        files = writer.write_bars(
            bars,
            symbol="BTCUSDT",
            market="binance",
            resolution=Resolution.DAILY,
            asset_class=AssetClass.CRYPTO,
        )

        assert len(files) == 1
        assert files[0].exists()
        assert "crypto/binance/daily" in str(files[0])

    def test_write_minute_bars(self, tmp_path):
        from datetime import datetime
        from lean_playground.lean_writer import (
            LeanDataWriter,
            BarData,
            Resolution,
            AssetClass,
        )

        writer = LeanDataWriter(tmp_path)
        bars = [
            BarData(datetime(2024, 1, 1, 0, 0), 100.0, 105.0, 99.0, 103.0, 1000.0),
            BarData(datetime(2024, 1, 1, 0, 1), 103.0, 108.0, 102.0, 106.0, 1200.0),
        ]

        files = writer.write_bars(
            bars,
            symbol="BTCUSDT",
            market="binance",
            resolution=Resolution.MINUTE,
            asset_class=AssetClass.CRYPTO,
        )

        assert len(files) == 1
        assert files[0].exists()
        assert "crypto/binance/minute/btcusdt" in str(files[0])


class TestBinanceClient:
    """Tests for Binance client."""

    def test_kline_intervals_valid(self):
        from lean_playground.binance_client import KLINE_INTERVALS

        assert "1m" in KLINE_INTERVALS
        assert "1h" in KLINE_INTERVALS
        assert "1d" in KLINE_INTERVALS


# ---------------------------------------------------------------------------
# analyze.py tests
# ---------------------------------------------------------------------------

class TestAnalyze:
    """Tests for the analyze module."""

    def test_load_equity_curve_valid_data(self, tmp_path):
        """Test loading equity curve from valid JSON."""
        from lean_playground.analyze import load_equity_curve

        # Create mock results file
        results = {
            "charts": {
                "Strategy Equity": {
                    "series": {
                        "Equity": {
                            "values": [
                                [1672549200, 100000, 100000, 100000, 100000],
                                [1672635600, 100000, 101000, 99000, 100500],
                                [1672722000, 100500, 102000, 100000, 101000],
                            ]
                        }
                    }
                }
            }
        }
        results_dir = tmp_path / "backtest"
        results_dir.mkdir()
        results_file = results_dir / "main-summary.json"
        results_file.write_text(json.dumps(results))

        equity = load_equity_curve(results_dir)

        assert len(equity) == 3
        assert equity.iloc[0] == 100000
        assert equity.iloc[-1] == 101000

    def test_load_equity_curve_missing_data(self, tmp_path):
        """Test error handling for missing equity data."""
        from lean_playground.analyze import load_equity_curve

        results_dir = tmp_path / "backtest"
        results_dir.mkdir()
        results_file = results_dir / "main-summary.json"
        results_file.write_text('{"charts": {}}')

        with pytest.raises(ValueError, match="Missing equity data"):
            load_equity_curve(results_dir)

    def test_load_equity_curve_empty_values(self, tmp_path):
        """Test error handling for empty equity curve."""
        from lean_playground.analyze import load_equity_curve

        results = {
            "charts": {
                "Strategy Equity": {
                    "series": {
                        "Equity": {
                            "values": []
                        }
                    }
                }
            }
        }
        results_dir = tmp_path / "backtest"
        results_dir.mkdir()
        results_file = results_dir / "main-summary.json"
        results_file.write_text(json.dumps(results))

        with pytest.raises(ValueError, match="Equity curve is empty"):
            load_equity_curve(results_dir)

    def test_equity_to_daily_returns(self):
        """Test conversion of equity to daily returns."""
        import pandas as pd
        from lean_playground.analyze import equity_to_daily_returns

        # Create equity series with known values
        dates = pd.date_range("2024-01-01", periods=5, freq="D", tz="UTC")
        equity = pd.Series([100, 102, 101, 105, 110], index=dates)

        returns = equity_to_daily_returns(equity)

        assert len(returns) == 4  # First day has no return
        assert abs(returns.iloc[0] - 0.02) < 0.001  # 2% return

    def test_equity_to_daily_returns_insufficient_data(self):
        """Test error when not enough data."""
        import pandas as pd
        from lean_playground.analyze import equity_to_daily_returns

        dates = pd.date_range("2024-01-01", periods=1, freq="D", tz="UTC")
        equity = pd.Series([100], index=dates)

        with pytest.raises(ValueError, match="Insufficient data"):
            equity_to_daily_returns(equity)

    def test_find_latest_backtest(self, tmp_path, monkeypatch):
        """Test finding the latest backtest results."""
        from lean_playground.analyze import find_latest_backtest
        import lean_playground.analyze

        # Set up mock results directory
        monkeypatch.setattr(lean_playground.analyze, "RESULTS_DIR", tmp_path)

        project_dir = tmp_path / "test_project"
        (project_dir / "20240101-120000").mkdir(parents=True)
        (project_dir / "20240102-120000").mkdir(parents=True)

        latest = find_latest_backtest("test_project")

        assert latest.name == "20240102-120000"

    def test_find_latest_backtest_no_results(self, tmp_path, monkeypatch):
        """Test error when no results exist."""
        from lean_playground.analyze import find_latest_backtest
        import lean_playground.analyze

        monkeypatch.setattr(lean_playground.analyze, "RESULTS_DIR", tmp_path)

        with pytest.raises(FileNotFoundError, match="No results found"):
            find_latest_backtest("nonexistent")

    def test_resolve_project_name(self):
        """Test project path resolution."""
        from lean_playground.analyze import resolve_project_name

        assert resolve_project_name("sr_levels") == "sr_levels"
        assert resolve_project_name("algorithms/sr_levels") == "sr_levels"
        # Nested paths are preserved after removing "algorithms/" prefix
        assert resolve_project_name("algorithms/nested/project") == "nested/project"

    def test_load_statistics(self, tmp_path):
        """Test loading statistics from results."""
        from lean_playground.analyze import load_statistics

        results = {
            "statistics": {
                "Sharpe Ratio": "1.5",
                "Net Profit": "25%",
            }
        }
        results_dir = tmp_path / "backtest"
        results_dir.mkdir()
        results_file = results_dir / "main-summary.json"
        results_file.write_text(json.dumps(results))

        stats = load_statistics(results_dir)

        assert stats["Sharpe Ratio"] == "1.5"
        assert stats["Net Profit"] == "25%"
