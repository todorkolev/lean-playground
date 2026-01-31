"""Data inspection utilities for the Lean data directory.

Provides functions to scan and report on available market data,
including symbols, date ranges, resolutions, and file statistics.
"""

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import zipfile

from lean_playground import LEAN_DATA_DIR


# Asset types that contain market data (excludes metadata directories)
ASSET_TYPES = {
    "equity", "crypto", "forex", "future", "option",
    "cryptofuture", "cfd", "futureoption", "index", "indexoption",
}

# Resolutions ordered from lowest to highest frequency
RESOLUTIONS = ["daily", "hour", "minute", "second", "tick"]

# Directories to skip when scanning
SKIP_DIRS = {
    "factor_files", "map_files", "universes", "margins",
    "fundamental", "shortable", "symbol-properties", "market-hours",
}


@dataclass
class DataEntry:
    """Represents a data series for a symbol at a specific resolution."""

    asset_type: str
    market: str
    resolution: str
    symbol: str
    data_type: str  # trade, quote, openinterest
    start_date: date
    end_date: date
    file_count: int
    size_bytes: int

    @property
    def date_range_str(self) -> str:
        """Format date range as a string."""
        return f"{self.start_date} to {self.end_date}"


def _parse_date_from_filename(filename: str) -> date | None:
    """Extract date from a filename like '20231215_trade.zip'."""
    try:
        date_str = filename.split("_")[0]
        if len(date_str) == 8 and date_str.isdigit():
            return datetime.strptime(date_str, "%Y%m%d").date()
    except (ValueError, IndexError):
        pass
    return None


def _parse_date_from_csv_content(zip_path: Path) -> tuple[date | None, date | None]:
    """Extract date range from CSV content inside a zip file."""
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
            if not csv_names:
                return None, None

            # Read first and last lines to get date range
            with zf.open(csv_names[0]) as f:
                lines = f.read().decode("utf-8").strip().split("\n")
                if not lines:
                    return None, None

                first_line = lines[0]
                last_line = lines[-1]

                # Parse dates - format is either "YYYYMMDD HH:MM,..." or milliseconds
                first_date = _parse_csv_date(first_line)
                last_date = _parse_csv_date(last_line)
                return first_date, last_date
    except (zipfile.BadZipFile, OSError, UnicodeDecodeError):
        pass
    return None, None


def _parse_csv_date(line: str) -> date | None:
    """Parse date from a CSV line."""
    try:
        first_field = line.split(",")[0].strip()
        # Format: "YYYYMMDD HH:MM"
        if " " in first_field:
            date_part = first_field.split(" ")[0]
            if len(date_part) == 8 and date_part.isdigit():
                return datetime.strptime(date_part, "%Y%m%d").date()
    except (ValueError, IndexError):
        pass
    return None


def _extract_symbol_from_path(path: Path, resolution: str) -> str:
    """Extract symbol name from path based on resolution type."""
    if resolution in ("daily", "hour"):
        # File is like "btcusdt_trade.zip" or "spy.zip"
        name = path.stem
        # Remove _trade, _quote, _openinterest suffix
        for suffix in ("_trade", "_quote", "_openinterest"):
            if name.endswith(suffix):
                name = name[: -len(suffix)]
                break
        return name
    else:
        # Directory is the symbol name
        return path.name


def _extract_data_type(path: Path) -> str:
    """Extract data type (trade, quote, openinterest) from path."""
    name = path.stem if path.is_file() else ""
    if "_quote" in name:
        return "quote"
    if "_openinterest" in name:
        return "openinterest"
    return "trade"


def _scan_resolution_dir(
    asset_type: str,
    market: str,
    resolution: str,
    resolution_dir: Path,
    symbol_filter: str | None = None,
) -> list[DataEntry]:
    """Scan a resolution directory for data entries."""
    entries = []

    if resolution in ("daily", "hour"):
        # Single zip files per symbol
        for zip_file in resolution_dir.glob("*.zip"):
            symbol = _extract_symbol_from_path(zip_file, resolution)
            if symbol_filter and symbol.lower() != symbol_filter.lower():
                continue

            data_type = _extract_data_type(zip_file)
            start_date, end_date = _parse_date_from_csv_content(zip_file)

            if start_date and end_date:
                entries.append(
                    DataEntry(
                        asset_type=asset_type,
                        market=market,
                        resolution=resolution,
                        symbol=symbol,
                        data_type=data_type,
                        start_date=start_date,
                        end_date=end_date,
                        file_count=1,
                        size_bytes=zip_file.stat().st_size,
                    )
                )
    else:
        # Directory per symbol with date-named zip files
        for symbol_dir in resolution_dir.iterdir():
            if not symbol_dir.is_dir():
                continue
            if symbol_dir.name in SKIP_DIRS:
                continue

            symbol = symbol_dir.name
            if symbol_filter and symbol.lower() != symbol_filter.lower():
                continue

            # Group files by data type
            files_by_type: dict[str, list[Path]] = {}
            for zip_file in symbol_dir.glob("*.zip"):
                data_type = _extract_data_type(zip_file)
                if data_type not in files_by_type:
                    files_by_type[data_type] = []
                files_by_type[data_type].append(zip_file)

            for data_type, files in files_by_type.items():
                dates = []
                total_size = 0
                for f in files:
                    file_date = _parse_date_from_filename(f.name)
                    if file_date:
                        dates.append(file_date)
                    total_size += f.stat().st_size

                if dates:
                    entries.append(
                        DataEntry(
                            asset_type=asset_type,
                            market=market,
                            resolution=resolution,
                            symbol=symbol,
                            data_type=data_type,
                            start_date=min(dates),
                            end_date=max(dates),
                            file_count=len(files),
                            size_bytes=total_size,
                        )
                    )

    return entries


def scan_data_directory(
    asset_type: str | None = None,
    market: str | None = None,
    resolution: str | None = None,
    symbol: str | None = None,
) -> list[DataEntry]:
    """Scan the Lean data directory and return matching entries.

    Args:
        asset_type: Filter by asset type (equity, crypto, forex, etc.)
        market: Filter by market (usa, binance, oanda, etc.)
        resolution: Filter by resolution (daily, hour, minute, etc.)
        symbol: Filter by symbol name

    Returns:
        List of DataEntry objects matching the filters
    """
    if not LEAN_DATA_DIR.exists():
        return []

    entries = []

    # Determine which asset types to scan
    asset_dirs = []
    if asset_type:
        asset_path = LEAN_DATA_DIR / asset_type.lower()
        if asset_path.exists():
            asset_dirs.append((asset_type.lower(), asset_path))
    else:
        for d in LEAN_DATA_DIR.iterdir():
            if d.is_dir() and d.name.lower() in ASSET_TYPES:
                asset_dirs.append((d.name.lower(), d))

    for asset_name, asset_dir in asset_dirs:
        # Scan markets
        for market_dir in asset_dir.iterdir():
            if not market_dir.is_dir():
                continue
            if market_dir.name in SKIP_DIRS:
                continue

            market_name = market_dir.name.lower()
            if market and market_name != market.lower():
                continue

            # Scan resolutions
            for res_dir in market_dir.iterdir():
                if not res_dir.is_dir():
                    continue
                if res_dir.name in SKIP_DIRS:
                    continue

                res_name = res_dir.name.lower()
                if res_name not in RESOLUTIONS:
                    continue
                if resolution and res_name != resolution.lower():
                    continue

                entries.extend(
                    _scan_resolution_dir(
                        asset_name, market_name, res_name, res_dir, symbol
                    )
                )

    # Sort by asset, market, symbol, resolution
    resolution_order = {r: i for i, r in enumerate(RESOLUTIONS)}
    entries.sort(
        key=lambda e: (
            e.asset_type,
            e.market,
            e.symbol,
            resolution_order.get(e.resolution, 99),
            e.data_type,
        )
    )

    return entries


def get_symbol_info(
    symbol: str,
    asset_type: str | None = None,
    market: str | None = None,
) -> list[DataEntry]:
    """Get detailed information for a specific symbol.

    Args:
        symbol: Symbol name to look up
        asset_type: Filter by asset type
        market: Filter by market

    Returns:
        List of DataEntry objects for the symbol
    """
    return scan_data_directory(
        asset_type=asset_type,
        market=market,
        symbol=symbol,
    )


def _format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def format_data_list(entries: list[DataEntry]) -> str:
    """Format entries as a table for display.

    Args:
        entries: List of DataEntry objects

    Returns:
        Formatted table string
    """
    if not entries:
        return "No data found."

    # Column headers
    headers = ["Asset", "Market", "Resolution", "Symbol", "Type", "Date Range", "Files", "Size"]

    # Build rows
    rows = []
    for e in entries:
        rows.append(
            [
                e.asset_type,
                e.market,
                e.resolution,
                e.symbol,
                e.data_type,
                f"{e.start_date} to {e.end_date}",
                str(e.file_count),
                _format_size(e.size_bytes),
            ]
        )

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    # Format output
    lines = []

    # Header
    header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    lines.append(header_line)
    lines.append("-" * len(header_line))

    # Rows
    for row in rows:
        lines.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))

    return "\n".join(lines)


def format_symbol_info(symbol: str, entries: list[DataEntry]) -> str:
    """Format detailed symbol information.

    Args:
        symbol: Symbol name
        entries: List of DataEntry objects for the symbol

    Returns:
        Formatted information string
    """
    if not entries:
        return f"No data found for symbol: {symbol}"

    # Group by market and asset type
    by_market: dict[tuple[str, str], list[DataEntry]] = {}
    for e in entries:
        key = (e.asset_type, e.market)
        if key not in by_market:
            by_market[key] = []
        by_market[key].append(e)

    lines = []

    for (asset_type, market_name), market_entries in by_market.items():
        lines.append(f"Symbol: {symbol.upper()}")
        lines.append(f"Asset:  {asset_type}")
        lines.append(f"Market: {market_name}")
        lines.append("")
        lines.append("Available Data:")

        # Sort by resolution
        resolution_order = {r: i for i, r in enumerate(RESOLUTIONS)}
        market_entries.sort(
            key=lambda e: (resolution_order.get(e.resolution, 99), e.data_type)
        )

        total_size = 0
        for e in market_entries:
            total_size += e.size_bytes
            file_label = "file" if e.file_count == 1 else "files"
            lines.append(
                f"  {e.resolution:8} {e.data_type:12} "
                f"{e.start_date} to {e.end_date}  "
                f"({e.file_count} {file_label}, {_format_size(e.size_bytes)})"
            )

        lines.append("")
        lines.append(f"Total Size: {_format_size(total_size)}")
        lines.append("")

    return "\n".join(lines).rstrip()
