import os

from dotenv import load_dotenv  # type: ignore
from rich.console import Console
from rich.table import Table

from trading_strategies.apis.api_utility import fetch_order_book
from trading_strategies.models.custom_models import AuthConfig


def get_env_variable(name: str, type_func, required: bool = True):
    """Fetch an environment variable and cast it to the specified type."""
    load_dotenv()
    value = os.getenv(name)
    if required and (value is None or value.strip() == ""):
        raise ValueError(f"Missing required environment variable: {name}")
    return type_func(value)  # Convert to required type


def calculate_vwap(price_volume_list: list):
    """Calculate VWAP (Volume-Weighted Average Price) from a list of price-volume tuples."""
    total_volume = sum(v for _, v in price_volume_list)
    if total_volume == 0:
        return "#DIV/0!"  # Avoid division by zero
    return round(sum(p * v for p, v in price_volume_list) / total_volume, 2)


async def generate_single_market_depth_for_ticker(
    auth: AuthConfig, ticker: str, market_depth: int = 20
):
    """Fetch and generate market depth data for a single ticker."""
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


def format_vwap(value):
    """Format VWAP value to two decimal places or return error string."""
    try:
        num = float(value)  # Attempt to convert to float
        return f"{num:,.2f}"
    except (ValueError, ZeroDivisionError):
        return "#DIV/0!"


def display_market_depth_table(ticker: str, bid_data, ask_data):
    """Display market depth data in a table format using rich library."""
    console = Console()
    table = Table(
        title=f"Market Depth View - {ticker}",
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("BidVWAP", justify="right")
    table.add_column("Cum Bid Vol", justify="right")
    table.add_column("Bid Volume", justify="right")
    table.add_column("Bid Price", justify="right")
    table.add_column("Ask Price", justify="right")
    table.add_column("Ask Volume", justify="right")
    table.add_column("Cum Ask Vol", justify="right")
    table.add_column("AskVWAP", justify="right")

    for bid, ask in zip(bid_data, ask_data):
        table.add_row(
            f"{format_vwap(bid[3])}",
            f"{bid[2]:,.2f}",
            f"{bid[1]:,.2f}",
            f"{bid[0]:,.2f}",
            f"{ask[0]:,.2f}",
            f"{ask[1]:,.2f}",
            f"{ask[2]:,.2f}",
            f"{format_vwap(ask[3])}",
        )

    console.print(table)


async def generate_integrated_global_orderbook(
    auth: AuthConfig, tickers: list, market_depth: int = 20
):
    """Generate an integrated global order book from multiple tickers."""
    global_bid_data = []  # List to hold all bid data across tickers
    global_ask_data = []  # List to hold all ask data across tickers

    # Loop through each ticker and fetch its order book
    for ticker in tickers:
        bid_data, ask_data = await generate_single_market_depth_for_ticker(
            auth=auth, ticker=ticker, market_depth=market_depth
        )

        # Combine bid data
        for price, volume, cum_volume, vwap in bid_data:
            global_bid_data.append((price, volume, cum_volume, vwap, ticker))

        # Combine ask data
        for price, volume, cum_volume, vwap in ask_data:
            global_ask_data.append((price, volume, cum_volume, vwap, ticker))

    # Now we need to sort the global bid and ask data
    global_bid_data = sorted(global_bid_data, key=lambda x: x[0], reverse=True)
    global_ask_data = sorted(global_ask_data, key=lambda x: x[0])

    # Calculate cumulative volumes and VWAP for the global order book
    integrated_bid_data = []
    integrated_ask_data = []
    cumulative_bid_vol = 0
    cumulative_ask_vol = 0
    bid_vwap_list = []
    ask_vwap_list = []

    for price, volume, _, _, ticker in global_bid_data:
        cumulative_bid_vol += volume
        bid_vwap_list.append((price, volume))
        bid_vwap = calculate_vwap(bid_vwap_list)
        integrated_bid_data.append(
            (price, volume, cumulative_bid_vol, bid_vwap, ticker)
        )

    for price, volume, _, _, ticker in global_ask_data:
        cumulative_ask_vol += volume
        ask_vwap_list.append((price, volume))
        ask_vwap = calculate_vwap(ask_vwap_list)
        integrated_ask_data.append(
            (price, volume, cumulative_ask_vol, ask_vwap, ticker)
        )

    # Display the final integrated global order book
    display_global_orderbook(integrated_bid_data, integrated_ask_data)

    return integrated_bid_data, integrated_ask_data


def display_global_orderbook(bid_data, ask_data):
    """Display the integrated global order book in a table format using rich library."""
    console = Console()
    table = Table(
        title="Integrated Global Order Book",
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Ticker", justify="left")
    table.add_column("BidVWAP", justify="right")
    table.add_column("Cum Bid Vol", justify="right")
    table.add_column("Bid Volume", justify="right")
    table.add_column("Bid Price", justify="right")
    table.add_column("Ask Price", justify="right")
    table.add_column("Ask Volume", justify="right")
    table.add_column("Cum Ask Vol", justify="right")
    table.add_column("AskVWAP", justify="right")
    table.add_column("Ticker", justify="right")

    # Assuming bid_data and ask_data have the ticker as the last element
    for (bid_price, bid_volume, cum_bid_vol, bid_vwap, ticker_bid), (
        ask_price,
        ask_volume,
        cum_ask_vol,
        ask_vwap,
        ticker_ask,
    ) in zip(bid_data, ask_data):
        table.add_row(
            ticker_bid,
            f"{format_vwap(bid_vwap)}",
            f"{cum_bid_vol:,.2f}",
            f"{bid_volume:,.2f}",
            f"{bid_price:,.2f}",
            f"{ask_price:,.2f}",
            f"{ask_volume:,.2f}",
            f"{cum_ask_vol:,.2f}",
            f"{format_vwap(ask_vwap)}",
            ticker_ask,
        )

    console.print(table)


async def generate_aggregate_orderbook(
    auth: AuthConfig, tickers: list, market_depth: int = 20
):
    """Generate an aggregated order book from multiple tickers."""
    # Initialize global aggregates
    global_bid_data = []
    global_ask_data = []
    cumulative_bid_volume = 0
    cumulative_ask_volume = 0
    bid_vwap_list = []
    ask_vwap_list = []

    tickers_combined = ""

    # Process each ticker to generate individual order books
    for ticker in tickers:
        tickers_combined += ticker + "-"
        bid_data, ask_data = await generate_single_market_depth_for_ticker(
            auth=auth, ticker=ticker, market_depth=market_depth
        )

        # Aggregate bid data
        for bid_price, bid_volume, cum_bid_vol, bid_vwap in bid_data:
            cumulative_bid_volume += bid_volume
            bid_vwap_list.append((bid_price, bid_volume))
            bid_vwap = calculate_vwap(bid_vwap_list)
            global_bid_data.append(
                (bid_vwap, cumulative_bid_volume, bid_volume, bid_price)
            )

        # Aggregate ask data
        for ask_price, ask_volume, cum_ask_vol, ask_vwap in ask_data:
            cumulative_ask_volume += ask_volume
            ask_vwap_list.append((ask_price, ask_volume))
            ask_vwap = calculate_vwap(ask_vwap_list)
            global_ask_data.append(
                (ask_price, ask_volume, cumulative_ask_volume, ask_vwap)
            )

    # Sort aggregated bid data (by bidVWAP descending)
    global_bid_data.sort(
        key=lambda x: x[3], reverse=True
    )  # Sorting by bid price (4th element)

    # Sort aggregated ask data (by askVWAP ascending)
    global_ask_data.sort(key=lambda x: x[3])  # Sorting by ask price (1st element)

    # Display aggregated market depth tables
    display_market_depth_table(
        ticker=tickers_combined, bid_data=global_bid_data, ask_data=global_ask_data
    )

    return global_bid_data, global_ask_data
