"""Generic brokerage registry using Lean's modules JSON.

Loads brokerage definitions from Lean CLI's modules-1.14.json and provides
a unified interface for configuring any supported brokerage.
"""

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from lean_playground import WORKSPACE_DIR

# Load .env file from workspace root
_env_file = WORKSPACE_DIR / ".env"
if _env_file.exists():
    load_dotenv(_env_file)

LEAN_MODULES_PATH = Path("/opt/miniconda3/lib/python3.11/site-packages/lean/modules-1.14.json")


@dataclass
class BrokerageConfig:
    """Configuration key for a brokerage."""

    id: str
    env_var: str
    required: bool = True
    is_secret: bool = False
    help_text: str = ""
    default: str | None = None


@dataclass
class Brokerage:
    """Brokerage definition loaded from Lean modules."""

    id: str
    display_name: str
    brokerage_class: str
    data_queue_handler: str
    configs: list[BrokerageConfig] = field(default_factory=list)
    supports_testnet: bool = False
    testnet_config_id: str | None = None
    exchange_name: str | None = None  # For brokerages with variants (e.g., Binance spot/futures)
    exchange_name_config_id: str | None = None  # Config key for exchange name

    def get_env_prefix(self) -> str:
        """Get environment variable prefix for this brokerage."""
        # Convert "binance" -> "BINANCE", "interactive-brokers" -> "IB"
        name = self.id.upper().replace("-", "_")
        # Common abbreviations
        abbreviations = {
            "INTERACTIVE_BROKERS": "IB",
            "COINBASE_ADVANCED_TRADE": "COINBASE",
            "TRADING_TECHNOLOGIES": "TT",
            "CHARLES_SCHWAB": "SCHWAB",
        }
        return abbreviations.get(name, name)

    def get_config_from_env(self) -> dict[str, str]:
        """Load brokerage config from environment variables.

        Returns:
            Dict of {config_id: value} for all found configs.

        Raises:
            ValueError: If required config is missing.
        """
        result = {}
        missing = []
        prefix = self.get_env_prefix()

        # Add exchange name if this is a variant brokerage
        if self.exchange_name and self.exchange_name_config_id:
            result[self.exchange_name_config_id] = self.exchange_name

        for config in self.configs:
            # Try environment variable
            value = os.environ.get(config.env_var)

            # Try with prefix if not found
            if not value:
                value = os.environ.get(f"{prefix}_{config.env_var}")

            # Use default if available
            if not value and config.default:
                value = config.default

            if value:
                result[config.id] = value
            elif config.required:
                missing.append(f"{prefix}_{config.env_var}")

        if missing:
            raise ValueError(
                f"Missing required environment variables for {self.display_name}:\n"
                + "\n".join(f"  - {var}" for var in missing)
                + f"\n\nSet these in your .env file or export them."
            )

        return result


def _config_id_to_env_var(config_id: str) -> str:
    """Convert config ID to environment variable name.

    Examples:
        binance-api-key -> API_KEY
        ib-account -> ACCOUNT
        alpaca-api-key -> API_KEY
    """
    # Remove brokerage prefix (everything before first hyphen after brokerage name)
    parts = config_id.split("-")

    # Skip known brokerage prefixes
    prefixes = {"binance", "binanceus", "ib", "alpaca", "bybit", "kraken",
                "oanda", "tradier", "coinbase", "schwab", "tt", "dydx"}

    # Find where the actual config name starts
    start_idx = 0
    for i, part in enumerate(parts):
        if part.lower() in prefixes:
            start_idx = i + 1
        else:
            break

    # Join remaining parts as env var name
    env_name = "_".join(parts[start_idx:]).upper()
    return env_name or config_id.upper().replace("-", "_")


def _load_modules_json() -> dict:
    """Load Lean's modules JSON file."""
    if not LEAN_MODULES_PATH.exists():
        raise FileNotFoundError(
            f"Lean modules file not found at {LEAN_MODULES_PATH}. "
            "Ensure you are running inside the Lean devcontainer."
        )

    with open(LEAN_MODULES_PATH) as f:
        return json.load(f)


def _extract_brokerage_class(module: dict, exchange_name: str | None = None) -> str:
    """Extract the brokerage class name from module configs."""
    for config in module.get("configurations", []):
        if config.get("id") == "live-mode-brokerage":
            # Check if this config matches the exchange_name filter
            if exchange_name:
                filters = config.get("filters", [])
                matches = True
                for f in filters:
                    cond = f.get("condition", {})
                    if cond.get("dependent-config-id") == "binance-exchange-name":
                        pattern = cond.get("pattern", "")
                        if cond.get("type") == "exact-match":
                            matches = pattern == exchange_name
                        elif cond.get("type") == "regex":
                            matches = bool(re.match(pattern, exchange_name))
                        if not matches:
                            break
                if matches:
                    return config.get("value", "")
            elif not config.get("filters"):
                # No filters, return this value
                return config.get("value", "")

    return module.get("id", "")


def _extract_data_queue_handler(module: dict, exchange_name: str | None = None) -> str:
    """Extract the data queue handler class name from module configs."""
    for config in module.get("configurations", []):
        if config.get("id") == "data-queue-handler":
            if exchange_name:
                filters = config.get("filters", [])
                matches = True
                for f in filters:
                    cond = f.get("condition", {})
                    if cond.get("dependent-config-id") == "binance-exchange-name":
                        pattern = cond.get("pattern", "")
                        if cond.get("type") == "exact-match":
                            matches = pattern == exchange_name
                        if not matches:
                            break
                if matches:
                    value = config.get("value", "")
                    # Parse JSON array if needed
                    if value.startswith("["):
                        return json.loads(value)[0]
                    return value
            elif not config.get("filters") or _is_brokerage_type_filter(config):
                value = config.get("value", "")
                if value.startswith("["):
                    return json.loads(value)[0]
                return value

    return _extract_brokerage_class(module, exchange_name)


def _is_brokerage_type_filter(config: dict) -> bool:
    """Check if config only has a type=brokerage filter (not exchange-specific)."""
    filters = config.get("filters", [])
    if not filters:
        return True
    for f in filters:
        cond = f.get("condition", {})
        if cond.get("dependent-config-id") == "type" and cond.get("pattern") in ("brokerage", "data-queue-handler"):
            continue
        return False
    return True


def _extract_input_configs(module: dict, exchange_name: str | None = None) -> list[BrokerageConfig]:
    """Extract input configuration keys from module."""
    configs = []
    seen_ids = set()

    for config in module.get("configurations", []):
        config_type = config.get("type", "")
        config_id = config.get("id", "")

        # Skip non-input configs
        if config_type not in ("input", "filter-env"):
            continue

        # Skip if already seen
        if config_id in seen_ids:
            continue

        # Skip exchange-name configs for variants (the variant choice implies the exchange name)
        if exchange_name and "exchange-name" in config_id:
            continue

        # Check if config applies to this exchange variant
        if exchange_name:
            filters = config.get("filters", [])
            matches = True
            for f in filters:
                cond = f.get("condition", {})
                dep_id = cond.get("dependent-config-id", "")
                if "exchange-name" in dep_id:
                    pattern = cond.get("pattern", "")
                    if cond.get("type") == "exact-match":
                        matches = pattern == exchange_name
                    elif cond.get("type") == "regex":
                        matches = bool(re.match(pattern, exchange_name))
                    if not matches:
                        break
            if not matches:
                continue

        seen_ids.add(config_id)

        # Determine if this is a secret
        is_secret = config.get("input-method") == "prompt-password"

        # Check if this is testnet selector
        is_testnet = "testnet" in config_id.lower() or "paper" in str(config.get("input-choices", [])).lower()

        configs.append(BrokerageConfig(
            id=config_id,
            env_var=_config_id_to_env_var(config_id),
            required=not is_testnet,  # Testnet config is optional
            is_secret=is_secret,
            help_text=config.get("help", ""),
            default="paper" if is_testnet else None,
        ))

    return configs


def load_brokerages() -> dict[str, Brokerage]:
    """Load all brokerage definitions from Lean's modules JSON.

    Returns:
        Dict mapping brokerage ID to Brokerage object.
    """
    data = _load_modules_json()
    brokerages = {}

    for module in data.get("modules", []):
        module_types = module.get("type", [])
        if "brokerage" not in module_types:
            continue

        module_id = module.get("id", "")
        display_name = module.get("display-id", module_id)

        # Skip paper trading (it's a special case)
        if module_id == "QuantConnectBrokerage":
            continue

        # Check for exchange variants (like Binance spot/futures)
        exchange_choices = None
        exchange_name_config_id = None
        for config in module.get("configurations", []):
            if config.get("id", "").endswith("-exchange-name"):
                exchange_choices = config.get("input-choices", [])
                exchange_name_config_id = config.get("id")
                break

        if exchange_choices:
            # Create separate brokerage entry for each variant
            for exchange_name in exchange_choices:
                variant_id = exchange_name.lower().replace(" ", "-")
                brokerage_class = _extract_brokerage_class(module, exchange_name)
                data_handler = _extract_data_queue_handler(module, exchange_name)
                configs = _extract_input_configs(module, exchange_name)

                # Check for testnet support
                supports_testnet = False
                testnet_config_id = None
                for c in configs:
                    if "testnet" in c.id.lower():
                        supports_testnet = True
                        testnet_config_id = c.id
                        break

                brokerages[variant_id] = Brokerage(
                    id=variant_id,
                    display_name=f"{display_name} ({exchange_name})",
                    brokerage_class=brokerage_class,
                    data_queue_handler=data_handler,
                    configs=configs,
                    supports_testnet=supports_testnet,
                    testnet_config_id=testnet_config_id,
                    exchange_name=exchange_name,
                    exchange_name_config_id=exchange_name_config_id,
                )
        else:
            # Single brokerage (no variants)
            brokerage_id = module_id.lower().replace("brokerage", "").strip("-")
            brokerage_class = _extract_brokerage_class(module)
            data_handler = _extract_data_queue_handler(module)
            configs = _extract_input_configs(module)

            # Check for testnet support
            supports_testnet = False
            testnet_config_id = None
            for c in configs:
                if "testnet" in c.id.lower() or "paper" in c.id.lower():
                    supports_testnet = True
                    testnet_config_id = c.id
                    break

            brokerages[brokerage_id] = Brokerage(
                id=brokerage_id,
                display_name=display_name,
                brokerage_class=brokerage_class,
                data_queue_handler=data_handler,
                configs=configs,
                supports_testnet=supports_testnet,
                testnet_config_id=testnet_config_id,
            )

    return brokerages


def get_brokerage(name: str) -> Brokerage:
    """Get a brokerage by name.

    Args:
        name: Brokerage ID (e.g., "binance", "alpaca", "interactive-brokers")

    Returns:
        Brokerage object.

    Raises:
        ValueError: If brokerage not found.
    """
    brokerages = load_brokerages()
    name_lower = name.lower()

    if name_lower in brokerages:
        return brokerages[name_lower]

    # Try partial match
    matches = [b for b in brokerages.values() if name_lower in b.id.lower()]
    if len(matches) == 1:
        return matches[0]

    # Show available options
    available = sorted(brokerages.keys())
    raise ValueError(
        f"Unknown brokerage: {name}\n\n"
        f"Available brokerages:\n"
        + "\n".join(f"  - {b}" for b in available)
    )


def list_brokerages() -> list[tuple[str, str]]:
    """List all available brokerages.

    Returns:
        List of (id, display_name) tuples.
    """
    brokerages = load_brokerages()
    return sorted((b.id, b.display_name) for b in brokerages.values())
