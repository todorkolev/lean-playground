"""Download historical data from exchanges to Lean format.

Downloads OHLCV data from Binance and writes it in QuantConnect Lean
format for use with the Lean engine.

Examples:
    # Download last 10 days of BTCUSDT hourly and daily data
    download_data(["BTCUSDT"], ["1h", "1d"])

    # Download specific date range
    download_data(["BTCUSDT", "ETHUSDT"], ["1m"], start_date="2024-01-01")

    # Download futures data
    download_data(["BTCUSDT"], ["1h"], account_type="usdt_future")
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from . import LEAN_DATA_DIR
from .binance_client import download_binance_data
from .lean_writer import AssetClass, LeanDataWriter, Resolution

logger = logging.getLogger(__name__)


async def download_data(
    symbols: List[str],
    intervals: List[str],
    exchange: str = "binance",
    days: int = 10,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account_type: str = "spot",
    testnet: bool = False,
    data_dir: Optional[Path] = None,
    use_archive: bool = True,
) -> Dict[str, List[Path]]:
    """Download historical data and write in Lean format.

    Args:
        symbols: List of trading symbols (e.g., ["BTCUSDT", "ETHUSDT"])
        intervals: List of intervals (e.g., ["1m", "1h", "1d"])
        exchange: Exchange to download from (currently only "binance" supported)
        days: Number of days of data to download (if no dates specified)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        account_type: Account type ("spot" or "usdt_future")
        testnet: Whether to use testnet (not fully supported)
        data_dir: Override Lean data directory
        use_archive: Use Binance data archive (recommended for historical data)

    Returns:
        Dictionary mapping symbols to list of written file paths
    """
    if exchange.lower() != "binance":
        raise ValueError(f"Only 'binance' exchange is currently supported, got: {exchange}")

    # Determine date range
    if start_date:
        start_time = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_time = datetime.utcnow() - timedelta(days=days)

    if end_date:
        end_time = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_time = datetime.utcnow()

    if start_time > end_time:
        raise ValueError("Start date must be before or equal to end date")

    # Set up data directory
    output_dir = data_dir or LEAN_DATA_DIR
    writer = LeanDataWriter(output_dir)

    # Determine asset class based on account type
    use_futures = account_type in ("usdt_future", "coin_future")
    if use_futures:
        asset_class = AssetClass.CRYPTO_FUTURE
    else:
        asset_class = AssetClass.CRYPTO

    logger.info(f"Downloading data from {exchange}")
    logger.info(f"  Symbols: {', '.join(symbols)}")
    logger.info(f"  Intervals: {', '.join(intervals)}")
    logger.info(f"  Date range: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}")
    logger.info(f"  Account type: {account_type}")
    logger.info(f"  Output: {output_dir}")
    if use_archive:
        logger.info("  Using Binance data archive (no API rate limits)")

    # Download and write data
    result: Dict[str, List[Path]] = {symbol: [] for symbol in symbols}

    async for symbol, interval, bars in download_binance_data(
        symbols=symbols,
        intervals=intervals,
        start_time=start_time,
        end_time=end_time,
        use_futures=use_futures,
        use_archive=use_archive,
    ):
        if not bars:
            logger.warning(f"  No data downloaded for {symbol} {interval}")
            continue

        logger.info(f"  Downloaded {len(bars)} bars for {symbol} {interval}")

        try:
            # Determine resolution
            resolution = Resolution.from_interval(interval)

            # Write to Lean format
            written_files = writer.write_bars(
                bars,
                symbol=symbol,
                market=exchange.lower(),
                resolution=resolution,
                asset_class=asset_class,
            )

            result[symbol].extend(written_files)
            logger.info(f"  Wrote {len(written_files)} file(s) for {symbol} {interval}")

        except Exception as e:
            logger.error(f"  Error writing {symbol} {interval}: {e}")
            continue

    return result


def download_data_sync(
    symbols: List[str],
    intervals: List[str],
    **kwargs,
) -> Dict[str, List[Path]]:
    """Synchronous wrapper for download_data.

    Args:
        symbols: List of trading symbols
        intervals: List of intervals
        **kwargs: Additional arguments passed to download_data

    Returns:
        Dictionary mapping symbols to list of written file paths
    """
    return asyncio.run(download_data(symbols, intervals, **kwargs))
