import asyncio
import base64
import os
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

from trading_strategies.models.custom_models import AuthConfig


def get_auth_config() -> AuthConfig:
    # Load environment variables
    load_dotenv()

    """Reads authentication config from environment and validates credentials."""
    server = os.getenv("SERVER", "http://localhost")
    port = int(os.getenv("PORT"))
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")

    # Check if credentials are provided
    if not username or not password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check if port is within valid range (1-65535)
    if not (1 <= port <= 65535):
        raise HTTPException(status_code=400, detail="Invalid port number")

    return AuthConfig(
        username=username,
        password=password,
        server=server,
        port=port,
    )


async def query_api(
    method: str,
    endpoint: str,
    auth: AuthConfig,
    params: Optional[Dict[str, Any]] = None,
) -> Any:
    """Generic function to query the trading API with different HTTP methods."""

    url = f"http://{auth.server}:{auth.port}{endpoint}"
    auth_str = f"{auth.username}:{auth.password}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()
    headers = {"accept": "application/json", "authorization": f"Basic {encoded_auth}"}

    async with httpx.AsyncClient() as client:
        try:
            if method.lower() == "get":
                response = await client.get(url, headers=headers, params=params)
            elif method.lower() == "post":
                response = await client.post(url, headers=headers, params=params)
            elif method.lower() == "delete":
                response = await client.delete(url, headers=headers, params=params)
            elif method.lower() == "put":
                response = await client.put(url, headers=headers, params=params)
            else:
                raise ValueError("Unsupported HTTP method.")

            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except httpx.RequestError as e:
            print(f"Request error: {str(e)}")  # Log the request error
            raise HTTPException(
                status_code=500, detail=f"Error querying {endpoint}: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {str(e)}")  # Log the HTTP error
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error querying {endpoint}: {str(e)}",
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


async def market_square_off_ticker(
    position: int, ticker: str, auth: AuthConfig, batch_size: Optional[int] = 10000
):
    action = "SELL" if position > 0 else "BUY"
    position = abs(position)
    endpoint = "/v1/orders"
    params = {
        "ticker": ticker,
        "type": "MARKET",
        "action": action,
    }
    while position != 0:
        quantity = batch_size if position > batch_size else position
        params["quantity"] = quantity
        try:
            await query_api("post", endpoint, auth, params=params)
            position -= quantity
            await asyncio.sleep(0.1)
        except Exception as e:
            print(
                f"Error occured when market_square_off {action} {ticker} {quantity}, current:{position} {e}"
            )
            await asyncio.sleep(0.1)
    return


async def cancel_open_orders(open_orders: list, auth: AuthConfig):
    while open_orders:
        for i, order in enumerate(open_orders):
            try:
                # Attempt to cancel the order
                endpoint = f"/v1/orders/{order['order_id']}"
                await query_api("delete", endpoint, auth)
                await asyncio.sleep(0.1)
                print(f"Cancelled {i} {order['order_id']} of {len(open_orders)} orders")
            except Exception as e:
                print(
                    f"An error occurred while cancelling the order {i} {order['order_id']} of {len(open_orders)} orders: {e}"
                )
        while True:
            try:
                await asyncio.sleep(0.1)
                params = {"status": "OPEN"}
                endpoint = "/v1/orders"
                open_orders = await query_api("get", endpoint, auth, params=params)
                # print("New open orders", open_orders)
                break
            except Exception as e:
                print(f"An error occurred while fetching OPEN orders: {e}")
    return


async def fetch_current_tick(auth: AuthConfig):
    """Fetches the current tick by querying the case API."""
    try:
        case_data = await query_api("get", "/v1/case", auth)
        return case_data.get("tick")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tick: {str(e)}")


async def fetch_active_tenders(auth: AuthConfig):
    """Gets a list of all active tenders."""
    try:
        return await query_api("get", "/v1/tenders", auth)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch tenders: {str(e)}"
        )


async def cancel_all_open_order(auth: AuthConfig):
    """Fetches the OPEN orders and cancels them till all are cancelled.
    If exception happens, it logs it and keeps on trying.
    """
    # TODO @Mayuresh If error happens do to rate limiting then try again
    open_orders = await query_api("get", "/v1/orders", auth, params={"status": "OPEN"})
    # print(f"Open orders are {[order["order_id"] for order in open_orders]}")
    return await cancel_open_orders(open_orders, auth)
    # print("Cancelled all open orders")


async def market_square_off_all_tickers(auth: AuthConfig, batch_size: int = 10000):
    "Fetches the list of securities and then squares them off at the MARKET"
    endpoint = "/v1/securities"
    # TODO @Mayuresh If error happens do to rate limiting then try again
    securities_data = await query_api("get", endpoint, auth)
    for security in securities_data:
        await market_square_off_ticker(
            security["position"], security["ticker"], auth=auth, batch_size=batch_size
        )
    print(f"Trade for all tickers squared off")
    return


async def fetch_securities(
    auth: AuthConfig,
    ticker: Optional[str] = None,
):
    """Fetches the securities by querying the securities API."""
    params = {"ticker": ticker}
    endpoint = "/v1/securities"
    return await query_api("get", endpoint, auth, params=params)


async def accept_tender(id: int, price: float, auth: AuthConfig):
    """Accept the tender."""
    endpoint = f"/v1/tenders/{id}"
    params = {"price": price}
    return await query_api("post", endpoint, auth, params=params)


async def fetch_order_book(ticker: str, auth: AuthConfig, limit: Optional[int] = 20):
    """Fetches the order book of a security by querying the securities/book API."""
    # Construct the query parameters
    params = {"ticker": ticker}
    if limit is not None:
        params["limit"] = limit
    endpoint = "/v1/securities/book"
    return await query_api("get", endpoint, auth, params=params)


async def is_tender_processed(
    auth: AuthConfig, ticker: str, quantity: int, initial_position: int
):
    """Asynchronously checks if a tender has been processed."""
    processing_count = 0
    while processing_count < 10:
        try:
            securities_data = await fetch_securities(auth, ticker)
            print(
                f"Checking if tender processed, quantity:{quantity} difference:{abs(initial_position - securities_data[0]['position'])} initial_position:{initial_position} current_position:{securities_data[0]['position']} "
            )
        except Exception as e:
            print(f"An error occurred while querying security {ticker}: {e}")
        if abs(initial_position - securities_data[0]["position"]) >= int(
            0.5 * abs(quantity)
        ):
            print(f"Tender has been processed")
            return True
        await asyncio.sleep(0.1)
        processing_count += 1
    print(f"Tender wasn't processed")
    return False


async def post_order(
    auth: AuthConfig,
    ticker: str,
    ticker_type: str,
    quantity: int,
    action: str,
    price: Optional[float] = None,  # Optional, required if type is LIMIT
    dry_run: Optional[float] = None,  # Optional, only for MARKET type
):
    """Insert a new order."""
    endpoint = "/v1/orders"
    params = {
        "ticker": ticker,
        "type": ticker_type,
        "quantity": quantity,
        "action": action,
    }
    if ticker_type == "LIMIT" and price is not None:
        params["price"] = price
    if ticker_type == "MARKET" and dry_run is not None:
        params["dry_run"] = dry_run
    return await query_api("post", endpoint, auth, params=params)
