import os

from dotenv import load_dotenv  # type: ignore

from trading_strategies.apis.api_utility import fetch_order_book
from trading_strategies.models.custom_models import AuthConfig


def get_env_variable(name: str, type_func, required: bool = True):
    load_dotenv()
    """Fetch an environment variable and cast it to the specified type."""
    value = os.getenv(name)
    if required and (value is None or value.strip() == ""):
        raise ValueError(f"Missing required environment variable: {name}")
    return type_func(value)  # Convert to required type


# Function to calculate VWAP (Volume-Weighted Average Price)
def calculate_vwap(price_volume_list: list):
    total_volume = sum(v for _, v in price_volume_list)
    if total_volume == 0:
        return "#DIV/0!"  # Avoid division by zero
    return round(sum(p * v for p, v in price_volume_list) / total_volume, 2)


# T3_MARKET_DEPTH_POINTS
async def generate_single_market_depth_for_ticker(
    auth: AuthConfig, ticker: str, market_depth: int = 20
):
    order_book = await fetch_order_book(ticker, auth, market_depth)
    bids = sorted(order_book["bids"], key=lambda x: x["price"], reverse=True)[
        :market_depth
    ]
    asks = sorted(order_book["asks"], key=lambda x: x["price"])[:market_depth]

    bid_data = []  # List of (price, volume, cumulative volume, VWAP)
    ask_data = []
    cumulative_bid_vol = 0
    cumulative_ask_vol = 0
    bid_vwap_list = []
    ask_vwap_list = []

    for i in range(market_depth):
        # Extract bid data
        bid_price = bids[i]["price"] if i < len(bids) else 0
        bid_volume = bids[i]["quantity"] if i < len(bids) else 0
        cumulative_bid_vol += bid_volume
        bid_vwap_list.append((bid_price, bid_volume))
        bid_vwap = calculate_vwap(bid_vwap_list)
        bid_data.append((bid_price, bid_volume, cumulative_bid_vol, bid_vwap))

        # Extract ask data
        ask_price = asks[i]["price"] if i < len(asks) else 0
        ask_volume = asks[i]["quantity"] if i < len(asks) else 0
        cumulative_ask_vol += ask_volume
        ask_vwap_list.append((ask_price, ask_volume))
        ask_vwap = calculate_vwap(ask_vwap_list)
        ask_data.append((ask_price, ask_volume, cumulative_ask_vol, ask_vwap))

    return bid_data, ask_data
