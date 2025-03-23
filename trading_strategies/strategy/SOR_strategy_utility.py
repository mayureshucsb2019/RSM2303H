from trading_strategies.logger_config import setup_logger
from trading_strategies.strategy.strategy_utility import get_env_variable

logger = setup_logger(__name__)


def parse_SOR_env_variables():
    """Parses and returns SOR strategy-specific environment variables."""
    return {
        "auth": {
            "username": get_env_variable("SOR_USERNAME", str, True),
            "password": get_env_variable("SOR_PASSWORD", str, True),
            "server": get_env_variable("SOR_SERVER", str, True),
            "port": get_env_variable("SOR_PORT", str, True),
        },
        "SOR_TRADE_UNTIL_TICK": int(
            get_env_variable("SOR_TRADE_UNTIL_TICK", int, True)
        ),
        "SOR_MIN_VWAP_MARGIN": float(
            get_env_variable("SOR_MIN_VWAP_MARGIN", float, True)
        ),
        "SOR_SLIPPAGE_MARGIN": float(
            get_env_variable("SOR_SLIPPAGE_MARGIN", float, True)
        )
    }
