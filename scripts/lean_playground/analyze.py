"""Backtest result analysis and tearsheet report generation.

Provides functions to load Lean backtest results and generate
HTML tearsheet reports with equity curves, drawdowns, and metrics.
"""

from datetime import datetime, timezone
from pathlib import Path
import json
import base64
from io import BytesIO

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from lean_playground import RESULTS_DIR, ALGORITHMS_DIR


def find_latest_backtest(project_name: str) -> Path:
    """Find the most recent backtest results for a project.

    Args:
        project_name: Name of the algorithm project (e.g., "sr_levels")

    Returns:
        Path to the latest results directory

    Raises:
        FileNotFoundError: If no results exist for the project
    """
    project_results_dir = RESULTS_DIR / project_name
    if not project_results_dir.exists():
        raise FileNotFoundError(f"No results found for project: {project_name}")

    # Find all timestamped directories
    backtest_dirs = [
        d for d in project_results_dir.iterdir()
        if d.is_dir() and d.name[0].isdigit()
    ]

    if not backtest_dirs:
        raise FileNotFoundError(f"No backtest results found for project: {project_name}")

    # Sort by name (timestamps sort lexicographically)
    latest = sorted(backtest_dirs, key=lambda d: d.name)[-1]
    return latest


def find_backtest(project_name: str, timestamp: str) -> Path:
    """Find a specific backtest by timestamp.

    Args:
        project_name: Name of the algorithm project
        timestamp: Backtest timestamp (e.g., "20260129-215353")

    Returns:
        Path to the results directory

    Raises:
        FileNotFoundError: If the specified backtest doesn't exist
    """
    backtest_dir = RESULTS_DIR / project_name / timestamp
    if not backtest_dir.exists():
        raise FileNotFoundError(
            f"Backtest {timestamp} not found for project: {project_name}"
        )
    return backtest_dir


def load_equity_curve(results_dir: Path) -> pd.Series:
    """Load equity curve from Lean JSON results.

    Args:
        results_dir: Path to the backtest results directory

    Returns:
        pandas Series with datetime index and equity values

    Raises:
        FileNotFoundError: If results file doesn't exist
        ValueError: If equity data is missing or malformed
    """
    # Try main-summary.json first, then main.json
    results_path = results_dir / "main-summary.json"
    if not results_path.exists():
        results_path = results_dir / "main.json"
    if not results_path.exists():
        raise FileNotFoundError(f"No results file found in: {results_dir}")

    with open(results_path) as f:
        data = json.load(f)

    try:
        values = data["charts"]["Strategy Equity"]["series"]["Equity"]["values"]
    except KeyError as e:
        raise ValueError(f"Missing equity data in results: {e}")

    if not values:
        raise ValueError("Equity curve is empty")

    # Parse [timestamp, open, high, low, close] tuples
    timestamps = []
    equity_values = []
    for row in values:
        ts = datetime.fromtimestamp(row[0], tz=timezone.utc)
        close = row[4]  # Use close price
        timestamps.append(ts)
        equity_values.append(close)

    return pd.Series(equity_values, index=pd.DatetimeIndex(timestamps), name="Equity")


def equity_to_daily_returns(equity: pd.Series) -> pd.Series:
    """Convert equity curve to daily returns series.

    Args:
        equity: Series with datetime index and equity values

    Returns:
        Series of daily percentage returns (timezone-naive for QuantStats compatibility)

    Raises:
        ValueError: If insufficient data for analysis
    """
    # Resample to daily (end of day)
    daily_equity = equity.resample("D").last().dropna()

    if len(daily_equity) < 2:
        raise ValueError("Insufficient data for analysis (need 2+ days)")

    # Calculate percentage returns
    returns = daily_equity.pct_change().dropna()
    returns.name = "returns"

    # Strip timezone for QuantStats compatibility
    # QuantStats uses timezone-naive datetime comparisons internally
    if returns.index.tz is not None:
        returns.index = returns.index.tz_localize(None)

    return returns


def load_statistics(results_dir: Path) -> dict:
    """Load backtest statistics from results.

    Args:
        results_dir: Path to the backtest results directory

    Returns:
        Dictionary of statistics
    """
    results_path = results_dir / "main-summary.json"
    if not results_path.exists():
        results_path = results_dir / "main.json"

    with open(results_path) as f:
        data = json.load(f)

    return data.get("statistics", {})


def calculate_metrics(returns: pd.Series, stats: dict) -> dict:
    """Calculate performance metrics from returns.

    Args:
        returns: Daily returns series
        stats: Statistics from backtest results

    Returns:
        Dictionary of calculated metrics
    """
    # Calculate cumulative returns
    cum_returns = (1 + returns).cumprod() - 1

    # Calculate drawdown
    wealth = (1 + returns).cumprod()
    peak = wealth.cummax()
    drawdown = (wealth - peak) / peak

    # Basic metrics
    total_return = cum_returns.iloc[-1] if len(cum_returns) > 0 else 0
    max_drawdown = drawdown.min()
    avg_return = returns.mean()
    volatility = returns.std() * np.sqrt(252)  # Annualized

    # Sharpe ratio (assuming 0 risk-free rate)
    sharpe = (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0

    # Sortino ratio (downside deviation)
    downside = returns[returns < 0]
    downside_std = downside.std() * np.sqrt(252) if len(downside) > 0 else 0
    sortino = (returns.mean() * 252) / downside_std if downside_std > 0 else 0

    # Win rate
    win_rate = (returns > 0).sum() / len(returns) * 100 if len(returns) > 0 else 0

    return {
        "Total Return": f"{total_return * 100:.2f}%",
        "Max Drawdown": f"{max_drawdown * 100:.2f}%",
        "Sharpe Ratio": f"{sharpe:.3f}",
        "Sortino Ratio": f"{sortino:.3f}",
        "Volatility (Ann.)": f"{volatility * 100:.2f}%",
        "Win Rate (days)": f"{win_rate:.1f}%",
        "Avg Daily Return": f"{avg_return * 100:.4f}%",
        # From backtest stats
        "Net Profit": stats.get("Net Profit", "N/A"),
        "Total Orders": stats.get("Total Orders", "N/A"),
        "Avg Win": stats.get("Average Win", "N/A"),
        "Avg Loss": stats.get("Average Loss", "N/A"),
        "Win Rate (trades)": stats.get("Win Rate", "N/A"),
    }


def create_charts(equity: pd.Series, returns: pd.Series) -> tuple[str, str, str]:
    """Create equity curve, drawdown, and monthly returns charts.

    Args:
        equity: Equity curve series
        returns: Daily returns series

    Returns:
        Tuple of (equity_chart_b64, drawdown_chart_b64, monthly_chart_b64)
    """
    # Calculate drawdown
    wealth = (1 + returns).cumprod()
    peak = wealth.cummax()
    drawdown = (wealth - peak) / peak * 100

    # Style configuration
    plt.style.use('seaborn-v0_8-whitegrid')

    # 1. Equity Curve
    fig1, ax1 = plt.subplots(figsize=(12, 4))
    ax1.plot(equity.index, equity.values, color='#2E86AB', linewidth=1.5)
    ax1.fill_between(equity.index, equity.values, alpha=0.3, color='#2E86AB')
    ax1.set_title('Equity Curve', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Equity ($)', fontsize=10)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    ax1.grid(True, alpha=0.3)
    plt.tight_layout()

    buf1 = BytesIO()
    fig1.savefig(buf1, format='png', dpi=100, bbox_inches='tight')
    buf1.seek(0)
    equity_b64 = base64.b64encode(buf1.read()).decode('utf-8')
    plt.close(fig1)

    # 2. Drawdown Chart
    fig2, ax2 = plt.subplots(figsize=(12, 3))
    ax2.fill_between(drawdown.index, drawdown.values, 0, color='#E63946', alpha=0.7)
    ax2.set_title('Underwater (Drawdown)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Drawdown (%)', fontsize=10)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()

    buf2 = BytesIO()
    fig2.savefig(buf2, format='png', dpi=100, bbox_inches='tight')
    buf2.seek(0)
    drawdown_b64 = base64.b64encode(buf2.read()).decode('utf-8')
    plt.close(fig2)

    # 3. Monthly Returns Heatmap
    monthly = returns.resample('M').apply(lambda x: (1 + x).prod() - 1) * 100
    monthly_df = pd.DataFrame({
        'Year': monthly.index.year,
        'Month': monthly.index.month,
        'Return': monthly.values
    })

    if len(monthly_df) > 0:
        pivot = monthly_df.pivot(index='Year', columns='Month', values='Return')
        pivot.columns = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][:len(pivot.columns)]

        fig3, ax3 = plt.subplots(figsize=(12, max(3, len(pivot) * 0.5)))
        cmap = plt.cm.RdYlGn
        im = ax3.imshow(pivot.values, cmap=cmap, aspect='auto', vmin=-20, vmax=20)

        # Add text annotations
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                val = pivot.iloc[i, j]
                if not np.isnan(val):
                    color = 'white' if abs(val) > 10 else 'black'
                    ax3.text(j, i, f'{val:.1f}%', ha='center', va='center', color=color, fontsize=9)

        ax3.set_xticks(range(len(pivot.columns)))
        ax3.set_xticklabels(pivot.columns)
        ax3.set_yticks(range(len(pivot.index)))
        ax3.set_yticklabels(pivot.index)
        ax3.set_title('Monthly Returns (%)', fontsize=14, fontweight='bold')

        cbar = plt.colorbar(im, ax=ax3, shrink=0.8)
        cbar.set_label('Return %')
        plt.tight_layout()

        buf3 = BytesIO()
        fig3.savefig(buf3, format='png', dpi=100, bbox_inches='tight')
        buf3.seek(0)
        monthly_b64 = base64.b64encode(buf3.read()).decode('utf-8')
        plt.close(fig3)
    else:
        monthly_b64 = ""

    return equity_b64, drawdown_b64, monthly_b64


def generate_tearsheet(
    returns: pd.Series,
    output_path: Path,
    equity: pd.Series,
    stats: dict,
    benchmark: pd.Series | str | None = None,
    title: str = "Strategy Performance",
) -> Path:
    """Generate HTML tearsheet with charts and metrics.

    Args:
        returns: Daily returns series
        output_path: Path for the output HTML file
        equity: Equity curve series
        stats: Statistics from backtest results
        benchmark: Optional benchmark (not currently used)
        title: Report title

    Returns:
        Path to the generated HTML file
    """
    # Calculate metrics
    metrics = calculate_metrics(returns, stats)

    # Create charts
    equity_b64, drawdown_b64, monthly_b64 = create_charts(equity, returns)

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #2E86AB;
            padding-bottom: 10px;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .metric {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-label {{
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .metric-value {{
            color: #333;
            font-size: 24px;
            font-weight: bold;
            margin-top: 5px;
        }}
        .chart {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chart img {{
            width: 100%;
            height: auto;
        }}
        .generated {{
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>

    <div class="metrics">
        {''.join(f'<div class="metric"><div class="metric-label">{k}</div><div class="metric-value">{v}</div></div>' for k, v in metrics.items())}
    </div>

    <div class="chart">
        <img src="data:image/png;base64,{equity_b64}" alt="Equity Curve">
    </div>

    <div class="chart">
        <img src="data:image/png;base64,{drawdown_b64}" alt="Drawdown">
    </div>

    {'<div class="chart"><img src="data:image/png;base64,' + monthly_b64 + '" alt="Monthly Returns"></div>' if monthly_b64 else ''}

    <div class="generated">
        Generated by lp analyze | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>
"""

    output_path.write_text(html)
    return output_path


def resolve_project_name(project: str) -> str:
    """Resolve project path to project name.

    Args:
        project: Project path or name (e.g., "algorithms/sr_levels" or "sr_levels")

    Returns:
        Project name (e.g., "sr_levels")
    """
    project_path = Path(project)

    # If it looks like a path, extract the name
    if project_path.parts:
        # Remove "algorithms/" prefix if present
        if project_path.parts[0] == "algorithms":
            return str(Path(*project_path.parts[1:]))
        return project_path.name

    return project


def analyze_backtest(
    project: str,
    backtest_timestamp: str | None = None,
    benchmark: str | None = None,
    open_browser: bool = False,
) -> Path:
    """Main entry point: analyze backtest and generate report.

    Args:
        project: Project path or name (e.g., "algorithms/sr_levels" or "sr_levels")
        backtest_timestamp: Optional specific backtest timestamp
        benchmark: Optional benchmark ticker (e.g., "BTC-USD")
        open_browser: Ignored (browser not available in container)

    Returns:
        Path to the generated HTML report

    Raises:
        FileNotFoundError: If project or backtest doesn't exist
        ValueError: If results data is invalid
    """
    project_name = resolve_project_name(project)

    # Find the backtest results
    if backtest_timestamp:
        results_dir = find_backtest(project_name, backtest_timestamp)
    else:
        results_dir = find_latest_backtest(project_name)

    print(f"Analyzing backtest: {results_dir}")

    # Load and transform data
    equity = load_equity_curve(results_dir)
    returns = equity_to_daily_returns(equity)

    # Get statistics for title
    stats = load_statistics(results_dir)
    sharpe = stats.get("Sharpe Ratio", "N/A")
    net_profit = stats.get("Net Profit", "N/A")
    title = f"{project_name} | Sharpe: {sharpe} | Net Profit: {net_profit}"

    # Generate report
    output_path = results_dir / "tearsheet.html"
    generate_tearsheet(returns, output_path, equity=equity, stats=stats, benchmark=benchmark, title=title)

    print(f"Report saved: {output_path}")

    # Start HTTP server to serve the report
    import subprocess

    port = 9000
    url = f"http://localhost:{port}/tearsheet.html"

    # Start server in background
    server = subprocess.Popen(
        ["python3", "-m", "http.server", str(port)],
        cwd=str(results_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print()
    print(f"View report: {url}")
    print()

    try:
        input("Press Enter to stop the server...")
    except KeyboardInterrupt:
        pass
    finally:
        server.terminate()
        server.wait()
        print("Server stopped.")

    return output_path
