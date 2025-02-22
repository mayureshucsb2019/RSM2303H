from trading_strategies.models.custom_models import AuthConfig
from trading_strategies.strategy.strategy_utility import (
    generate_single_market_depth_for_ticker,
    get_env_variable,
)


def parse_lt3_env_variables():
    return {
        "auth": {
            "username": get_env_variable("USERNAME", str, True),
            "password": get_env_variable("PASSWORD", str, True),
            "server": get_env_variable("SERVER", str, True),
            "port": get_env_variable("PORT", str, True),
        },
        "T3_MARKET_DEPTH_POINTS": get_env_variable("T3_MARKET_DEPTH_POINTS", int, True),
        "T3_MIN_PROFIT_MARGIN": get_env_variable("T3_MIN_PROFIT_MARGIN", float, True),
        "T3_TRADE_UNTIL_TICK": get_env_variable("T3_TRADE_UNTIL_TICK", int, True),
        "T3_MIN_VWAP_MARGIN": get_env_variable("T3_MIN_VWAP_MARGIN", float, True),
        "T3_STOP_LOSS_PERCENT": get_env_variable("T3_STOP_LOSS_PERCENT", float, True),
        "T3_BATCH_SIZE": get_env_variable("T3_BATCH_SIZE", int, True),
        "T3_SQUARE_OFF_BATCH_SIZE": get_env_variable(
            "T3_SQUARE_OFF_BATCH_SIZE", int, True
        ),
        "T3_NET_LIMIT": get_env_variable("T3_NET_LIMIT", int, True),
        "T3_GROSS_LIMIT": get_env_variable("T3_GROSS_LIMIT", int, True),
    }


async def generate_lt3_signal(
    auth: AuthConfig,
    ticker: str,
    price: float,
    action: str,
    quantity: int,
    margin: float,
    market_depth: int = 20,
):
    bid_data, ask_data = await generate_single_market_depth_for_ticker(
        auth, ticker, market_depth
    )

    if action == "SELL":
        for bid_price, bid_volume, cumulative_bid_vol, bid_vwap in bid_data:
            if cumulative_bid_vol >= quantity:
                return (price - margin > bid_vwap, bid_vwap)
        return (price - margin > bid_data[0][3], bid_data[0][3])

    elif action == "BUY":
        for ask_price, ask_volume, cumulative_ask_vol, ask_vwap in ask_data:
            if cumulative_ask_vol >= quantity:
                return (price + margin < ask_vwap, ask_vwap)
        return (price + margin < ask_data[0][3], ask_data[0][3])

    return (False, -1)
