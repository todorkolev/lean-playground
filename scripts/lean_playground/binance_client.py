"""Lightweight Binance API client for downloading historical data.

Downloads OHLCV kline data from Binance public API and data archives.
No API key required for historical data.
"""

import asyncio
import io
import logging
import zipfile
from datetime import datetime, timedelta
from typing import AsyncGenerator, List, Optional, Tuple
from urllib.parse import urljoin

import aiohttp
import pandas as pd

from .lean_writer import BarData

logger = logging.getLogger(__name__)

# Binance API endpoints
BINANCE_API_BASE = "https://api.binance.com"
BINANCE_FUTURES_API_BASE = "https://fapi.binance.com"
BINANCE_DATA_ARCHIVE = "https://data.binance.vision"

# Kline intervals
KLINE_INTERVALS = {
    "1s": "1s",
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "2h": "2h",
    "4h": "4h",
    "6h": "6h",
    "8h": "8h",
    "12h": "12h",
    "1d": "1d",
    "3d": "3d",
    "1w": "1w",
    "1M": "1M",
}


class BinanceClient:
    """Lightweight Binance client for downloading kline data."""

    def __init__(
        self,
        use_futures: bool = False,
        testnet: bool = False,
    ):
        """Initialize Binance client.

        Args:
            use_futures: Whether to use USDT futures endpoints
            testnet: Whether to use testnet (not fully supported)
        """
        self._use_futures = use_futures
        self._testnet = testnet
        self._session: Optional[aiohttp.ClientSession] = None

        if use_futures:
            self._api_base = BINANCE_FUTURES_API_BASE
            self._klines_endpoint = "/fapi/v1/klines"
        else:
            self._api_base = BINANCE_API_BASE
            self._klines_endpoint = "/api/v3/klines"

    async def __aenter__(self) -> "BinanceClient":
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._session:
            await self._session.close()
            self._session = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure session is initialized."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def download_klines(
        self,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000,
    ) -> List[BarData]:
        """Download kline data from Binance API.

        Args:
            symbol: Trading symbol (e.g., BTCUSDT)
            interval: Kline interval (e.g., 1h, 1d)
            start_time: Start datetime
            end_time: End datetime
            limit: Maximum records per request

        Returns:
            List of BarData objects
        """
        if interval not in KLINE_INTERVALS:
            raise ValueError(f"Invalid interval: {interval}")

        session = await self._ensure_session()
        all_bars = []
        current_start = start_time

        while current_start < end_time:
            params = {
                "symbol": symbol.upper(),
                "interval": KLINE_INTERVALS[interval],
                "startTime": int(current_start.timestamp() * 1000),
                "endTime": int(end_time.timestamp() * 1000),
                "limit": limit,
            }

            url = f"{self._api_base}{self._klines_endpoint}"
            logger.debug(f"Fetching klines: {symbol} {interval} from {current_start}")

            try:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        text = await response.text()
                        logger.error(f"API error {response.status}: {text}")
                        break

                    data = await response.json()

                    if not data:
                        break

                    for kline in data:
                        # Kline format: [open_time, open, high, low, close, volume, ...]
                        bar = BarData(
                            timestamp=datetime.utcfromtimestamp(kline[0] / 1000),
                            open=float(kline[1]),
                            high=float(kline[2]),
                            low=float(kline[3]),
                            close=float(kline[4]),
                            volume=float(kline[5]),
                        )
                        all_bars.append(bar)

                    # Move to next batch
                    last_time = datetime.utcfromtimestamp(data[-1][0] / 1000)
                    if last_time <= current_start:
                        break
                    current_start = last_time + timedelta(milliseconds=1)

                    # Rate limiting
                    await asyncio.sleep(0.1)

            except aiohttp.ClientError as e:
                logger.error(f"Network error: {e}")
                break

        return all_bars

    async def stream_klines_by_day(
        self,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: datetime,
    ) -> AsyncGenerator[Tuple[str, List[BarData]], None]:
        """Stream kline data day by day.

        Yields tuples of (date_string, bars_for_day).
        """
        current_date = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_time.replace(hour=0, minute=0, second=0, microsecond=0)

        while current_date <= end_date:
            day_start = current_date
            day_end = min(current_date + timedelta(days=1), end_time)

            bars = await self.download_klines(
                symbol=symbol,
                interval=interval,
                start_time=day_start,
                end_time=day_end,
            )

            if bars:
                date_str = current_date.strftime("%Y%m%d")
                yield date_str, bars

            current_date += timedelta(days=1)

    async def download_from_archive(
        self,
        symbol: str,
        interval: str,
        year: int,
        month: int,
        day: Optional[int] = None,
    ) -> List[BarData]:
        """Download kline data from Binance data archive.

        The archive provides historical data without API rate limits.

        Args:
            symbol: Trading symbol
            interval: Kline interval
            year: Year
            month: Month (1-12)
            day: Day (optional, for daily files)

        Returns:
            List of BarData objects
        """
        session = await self._ensure_session()

        # Construct archive URL
        if self._use_futures:
            base_path = "/data/futures/um/daily/klines" if day else "/data/futures/um/monthly/klines"
        else:
            base_path = "/data/spot/daily/klines" if day else "/data/spot/monthly/klines"

        symbol_upper = symbol.upper()
        interval_str = KLINE_INTERVALS[interval]

        if day:
            filename = f"{symbol_upper}-{interval_str}-{year}-{month:02d}-{day:02d}.zip"
            url = f"{BINANCE_DATA_ARCHIVE}{base_path}/{symbol_upper}/{interval_str}/{filename}"
        else:
            filename = f"{symbol_upper}-{interval_str}-{year}-{month:02d}.zip"
            url = f"{BINANCE_DATA_ARCHIVE}{base_path}/{symbol_upper}/{interval_str}/{filename}"

        logger.debug(f"Downloading archive: {url}")

        try:
            async with session.get(url) as response:
                if response.status == 404:
                    logger.debug(f"Archive not found: {url}")
                    return []

                if response.status != 200:
                    logger.debug(f"Archive download failed with status {response.status}: {url}")
                    return []

                content = await response.read()

                # Verify it's a valid ZIP file
                if not content.startswith(b'PK'):
                    logger.debug(f"Invalid archive content (not a ZIP file): {url}")
                    return []

                # Parse ZIP file
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    # Get the CSV file inside
                    csv_name = zf.namelist()[0]
                    with zf.open(csv_name) as f:
                        # Read first line to check for header
                        first_line = f.readline().decode('utf-8').strip()
                        f.seek(0)  # Reset to beginning

                        # Check if first line is a header (starts with text, not number)
                        has_header = first_line.startswith('open_time') or not first_line[0].isdigit()

                        df = pd.read_csv(
                            f,
                            header=0 if has_header else None,
                            names=None if has_header else [
                                "open_time",
                                "open",
                                "high",
                                "low",
                                "close",
                                "volume",
                                "close_time",
                                "quote_volume",
                                "trades",
                                "taker_buy_base",
                                "taker_buy_quote",
                                "ignore",
                            ],
                        )

                bars = []
                for _, row in df.iterrows():
                    try:
                        # Validate timestamp is reasonable (between 2017 and 2030)
                        timestamp_ms = row["open_time"]
                        if not isinstance(timestamp_ms, (int, float)):
                            continue
                        timestamp_s = timestamp_ms / 1000
                        # Sanity check: timestamp should be between 2017 and 2030
                        if timestamp_s < 1483228800 or timestamp_s > 1893456000:
                            continue

                        bars.append(
                            BarData(
                                timestamp=datetime.utcfromtimestamp(timestamp_s),
                                open=float(row["open"]),
                                high=float(row["high"]),
                                low=float(row["low"]),
                                close=float(row["close"]),
                                volume=float(row["volume"]),
                            )
                        )
                    except (ValueError, TypeError, KeyError):
                        continue

                return bars

        except aiohttp.ClientError as e:
            logger.error(f"Network error downloading archive: {e}")
            return []
        except zipfile.BadZipFile:
            logger.debug(f"Invalid ZIP file from archive: {url}")
            return []
        except Exception as e:
            logger.debug(f"Error parsing archive {url}: {e}")
            return []

    async def download_range_from_archive(
        self,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: datetime,
        fallback_to_api: bool = True,
    ) -> List[BarData]:
        """Download kline data from archive for a date range.

        For daily+ intervals (1d, 3d, 1w, 1M), downloads monthly files directly
        since each daily file only contains 1 bar. For sub-daily intervals,
        tries daily files first, then falls back to monthly files.
        Optionally falls back to API for recent data not yet in archives.
        """
        all_bars = []
        current_date = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_time.replace(hour=0, minute=0, second=0, microsecond=0)

        # For daily+ intervals, skip daily files entirely - they only have 1 bar each
        # Monthly archives are much more efficient (12 requests/year vs 365)
        use_monthly_only = interval in ("1d", "3d", "1w", "1M")

        # Track which months we've already downloaded and days without archive data
        downloaded_months = set()
        missing_days = []

        if use_monthly_only:
            # Iterate by month instead of by day for efficiency
            current_month = current_date.replace(day=1)
            end_month = end_date.replace(day=1)

            while current_month <= end_month:
                year = current_month.year
                month = current_month.month
                month_key = (year, month)

                monthly_bars = await self.download_from_archive(
                    symbol=symbol,
                    interval=interval,
                    year=year,
                    month=month,
                )
                if monthly_bars:
                    # Filter to requested range
                    monthly_bars = [
                        b for b in monthly_bars if start_time <= b.timestamp <= end_time
                    ]
                    all_bars.extend(monthly_bars)
                    downloaded_months.add(month_key)
                    logger.info(f"  Downloaded {len(monthly_bars)} bars from monthly archive for {year}-{month:02d}")
                else:
                    # Mark all days in this month as missing
                    day = current_month
                    next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
                    while day < next_month and day <= end_date:
                        if day >= current_date:
                            missing_days.append(day)
                        day += timedelta(days=1)

                # Move to next month
                current_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
        else:
            # For sub-daily intervals, iterate by day
            while current_date <= end_date:
                year = current_date.year
                month = current_date.month
                day = current_date.day

                # Try daily file first
                bars = await self.download_from_archive(
                    symbol=symbol,
                    interval=interval,
                    year=year,
                    month=month,
                    day=day,
                )

                if bars:
                    # Filter to requested range
                    bars = [b for b in bars if start_time <= b.timestamp <= end_time]
                    all_bars.extend(bars)
                    logger.info(f"  Downloaded {len(bars)} bars from archive for {current_date.strftime('%Y-%m-%d')}")
                else:
                    # Try monthly file if we haven't already
                    month_key = (year, month)
                    if month_key not in downloaded_months:
                        monthly_bars = await self.download_from_archive(
                            symbol=symbol,
                            interval=interval,
                            year=year,
                            month=month,
                        )
                        if monthly_bars:
                            # Filter to requested range
                            monthly_bars = [
                                b for b in monthly_bars if start_time <= b.timestamp <= end_time
                            ]
                            all_bars.extend(monthly_bars)
                            downloaded_months.add(month_key)
                            logger.info(f"  Downloaded {len(monthly_bars)} bars from monthly archive for {year}-{month:02d}")
                        else:
                            # Mark this day as missing from archive
                            missing_days.append(current_date)

                current_date += timedelta(days=1)

        # Fall back to API for missing days
        if missing_days and fallback_to_api:
            if missing_days:
                logger.info(f"  Archive data not available for {len(missing_days)} day(s), falling back to API...")
                # Group consecutive missing days to minimize API calls
                if missing_days:
                    api_start = min(missing_days)
                    api_end = max(missing_days) + timedelta(days=1)
                    try:
                        api_bars = await self.download_klines(
                            symbol=symbol,
                            interval=interval,
                            start_time=api_start,
                            end_time=api_end,
                        )
                        if api_bars:
                            # Filter to requested range
                            api_bars = [b for b in api_bars if start_time <= b.timestamp <= end_time]
                            all_bars.extend(api_bars)
                            logger.info(f"  Downloaded {len(api_bars)} bars from API for missing dates")
                    except Exception as e:
                        logger.warning(f"  API fallback failed: {e}")

        # Sort by timestamp and remove duplicates
        all_bars.sort(key=lambda b: b.timestamp)
        seen = set()
        unique_bars = []
        for bar in all_bars:
            key = (bar.timestamp, bar.open, bar.close)
            if key not in seen:
                seen.add(key)
                unique_bars.append(bar)

        return unique_bars


async def download_binance_data(
    symbols: List[str],
    intervals: List[str],
    start_time: datetime,
    end_time: datetime,
    use_futures: bool = False,
    use_archive: bool = True,
) -> AsyncGenerator[Tuple[str, str, List[BarData]], None]:
    """Download data from Binance for multiple symbols and intervals.

    Args:
        symbols: List of trading symbols
        intervals: List of kline intervals
        start_time: Start datetime
        end_time: End datetime
        use_futures: Whether to download futures data
        use_archive: Whether to use data archive (recommended for historical data)

    Yields:
        Tuples of (symbol, interval, bars)
    """
    async with BinanceClient(use_futures=use_futures) as client:
        for symbol in symbols:
            for interval in intervals:
                logger.info(f"Downloading {symbol} {interval}...")

                if use_archive:
                    bars = await client.download_range_from_archive(
                        symbol=symbol,
                        interval=interval,
                        start_time=start_time,
                        end_time=end_time,
                    )
                else:
                    bars = await client.download_klines(
                        symbol=symbol,
                        interval=interval,
                        start_time=start_time,
                        end_time=end_time,
                    )

                yield symbol, interval, bars
