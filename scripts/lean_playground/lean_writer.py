"""Write data in QuantConnect Lean format.

Lean data format specification:
- Minute/Second: crypto/{market}/minute/{symbol}/{YYYYMMDD}_trade.zip
  CSV: milliseconds_since_midnight,open,high,low,close,volume
- Hour/Daily: crypto/{market}/{resolution}/{symbol}_trade.zip
  CSV: YYYYMMDD HH:MM,open,high,low,close,volume
- Futures: cryptofuture/{market}/... with same structure
"""

import csv
import io
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


class Resolution(Enum):
    """Supported data resolutions."""

    TICK = "tick"
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAILY = "daily"

    @classmethod
    def from_interval(cls, interval: str) -> "Resolution":
        """Convert interval string to Resolution."""
        mapping = {
            "1s": cls.SECOND,
            "1m": cls.MINUTE,
            "3m": cls.MINUTE,
            "5m": cls.MINUTE,
            "15m": cls.MINUTE,
            "30m": cls.MINUTE,
            "1h": cls.HOUR,
            "2h": cls.HOUR,
            "4h": cls.HOUR,
            "6h": cls.HOUR,
            "8h": cls.HOUR,
            "12h": cls.HOUR,
            "1d": cls.DAILY,
            "3d": cls.DAILY,
            "1w": cls.DAILY,
            "1M": cls.DAILY,
        }
        if interval not in mapping:
            raise ValueError(f"Unsupported interval: {interval}")
        return mapping[interval]


class AssetClass(Enum):
    """Supported asset classes."""

    CRYPTO = "crypto"
    CRYPTO_FUTURE = "cryptofuture"


@dataclass
class BarData:
    """OHLCV bar data."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class LeanDataWriter:
    """Write market data in QuantConnect Lean format."""

    def __init__(self, data_dir: Path):
        """Initialize writer with Lean data directory.

        Args:
            data_dir: Path to Lean data directory (e.g., /Lean/Data)
        """
        self._data_dir = Path(data_dir)

    def write_bars(
        self,
        bars: List[BarData],
        symbol: str,
        market: str,
        resolution: Resolution,
        asset_class: AssetClass = AssetClass.CRYPTO,
    ) -> List[Path]:
        """Write bar data in Lean format.

        Args:
            bars: List of BarData objects
            symbol: Trading symbol (e.g., btcusdt)
            market: Market/exchange name (e.g., binance)
            resolution: Data resolution
            asset_class: Asset class (crypto or cryptofuture)

        Returns:
            List of paths to written ZIP files
        """
        if not bars:
            return []

        symbol_lower = symbol.lower()
        market_lower = market.lower()

        if resolution in (Resolution.MINUTE, Resolution.SECOND):
            return self._write_intraday_bars(
                bars, symbol_lower, market_lower, resolution, asset_class
            )
        else:
            return self._write_aggregated_bars(
                bars, symbol_lower, market_lower, resolution, asset_class
            )

    def _write_intraday_bars(
        self,
        bars: List[BarData],
        symbol: str,
        market: str,
        resolution: Resolution,
        asset_class: AssetClass,
    ) -> List[Path]:
        """Write minute/second data as daily ZIP files."""
        # Group bars by date
        daily_bars: Dict[str, List[BarData]] = defaultdict(list)
        for bar in bars:
            date_str = bar.timestamp.strftime("%Y%m%d")
            daily_bars[date_str].append(bar)

        written_files = []
        for date_str, day_bars in daily_bars.items():
            output_dir = (
                self._data_dir
                / asset_class.value
                / market
                / resolution.value
                / symbol
            )
            output_dir.mkdir(parents=True, exist_ok=True)

            zip_path = output_dir / f"{date_str}_trade.zip"
            csv_name = f"{date_str}_{symbol}_{resolution.value}_trade.csv"

            csv_content = self._format_intraday_csv(day_bars)
            self._write_zip(zip_path, csv_name, csv_content)
            written_files.append(zip_path)

        return written_files

    def _write_aggregated_bars(
        self,
        bars: List[BarData],
        symbol: str,
        market: str,
        resolution: Resolution,
        asset_class: AssetClass,
    ) -> List[Path]:
        """Write hour/daily data as single ZIP file."""
        output_dir = self._data_dir / asset_class.value / market / resolution.value
        output_dir.mkdir(parents=True, exist_ok=True)

        zip_path = output_dir / f"{symbol}_trade.zip"
        csv_name = f"{symbol}.csv"

        csv_content = self._format_aggregated_csv(bars)
        self._write_zip(zip_path, csv_name, csv_content)

        return [zip_path]

    def _format_intraday_csv(self, bars: List[BarData]) -> str:
        """Format bars as intraday CSV (milliseconds since midnight)."""
        output = io.StringIO()
        writer = csv.writer(output)

        for bar in sorted(bars, key=lambda b: b.timestamp):
            # Calculate milliseconds since midnight
            midnight = bar.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            ms_since_midnight = int((bar.timestamp - midnight).total_seconds() * 1000)

            writer.writerow(
                [
                    ms_since_midnight,
                    bar.open,
                    bar.high,
                    bar.low,
                    bar.close,
                    bar.volume,
                ]
            )

        return output.getvalue()

    def _format_aggregated_csv(self, bars: List[BarData]) -> str:
        """Format bars as aggregated CSV (YYYYMMDD HH:MM)."""
        output = io.StringIO()
        writer = csv.writer(output)

        for bar in sorted(bars, key=lambda b: b.timestamp):
            time_str = bar.timestamp.strftime("%Y%m%d %H:%M")
            writer.writerow(
                [
                    time_str,
                    bar.open,
                    bar.high,
                    bar.low,
                    bar.close,
                    bar.volume,
                ]
            )

        return output.getvalue()

    def _write_zip(self, zip_path: Path, csv_name: str, csv_content: str) -> None:
        """Write CSV content to a ZIP file."""
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(csv_name, csv_content)


def convert_nautilus_bars(
    nautilus_bars: List,
    interval: Optional[str] = None,
) -> List[BarData]:
    """Convert Nautilus Trader bars to BarData.

    Args:
        nautilus_bars: List of Nautilus Bar objects
        interval: Original interval string (for resolution detection)

    Returns:
        List of BarData objects
    """
    result = []
    for bar in nautilus_bars:
        timestamp = pd.to_datetime(bar.ts_event, unit="ns", utc=True).to_pydatetime()
        result.append(
            BarData(
                timestamp=timestamp.replace(tzinfo=None),
                open=float(bar.open),
                high=float(bar.high),
                low=float(bar.low),
                close=float(bar.close),
                volume=float(bar.volume),
            )
        )
    return result
