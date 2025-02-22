from typing import Optional

from fastapi import Depends, FastAPI, HTTPException

from trading_strategies.apis.api_utility import (
    accept_tender,
    fetch_active_tenders,
    fetch_order_book,
    fetch_securities,
    get_auth_config,
    post_order,
    query_api,
)
from trading_strategies.models.custom_models import AuthConfig

app = FastAPI()


@app.get("/case")
async def get_case_status(auth: AuthConfig = Depends(get_auth_config)):
    """Fetches the case status by querying the case API."""
    endpoint = "/v1/case"
    return await query_api("get", endpoint, auth)


@app.get("/trader")
async def get_trader_info(auth: AuthConfig = Depends(get_auth_config)):
    """Fetches the case status by querying the trader API."""
    endpoint = "/v1/trader"
    return await query_api("get", endpoint, auth)


@app.get("/limits")
async def get_trading_limits(auth: AuthConfig = Depends(get_auth_config)):
    """Fetches the trading limits by querying the limits API."""
    endpoint = "/v1/limits"
    return await query_api("get", endpoint, auth)


@app.get("/news")
async def get_recent_news(
    limit: Optional[int] = None,
    after: Optional[int] = None,
    auth: AuthConfig = Depends(get_auth_config),
):
    """Fetches the trading limits by querying the news API."""
    params = (
        {
            "limit": limit,
            "after": after,
        }
        if limit or after
        else {}
    )
    print("params are:", params)
    endpoint = "/v1/news"
    return await query_api("get", endpoint, auth, params=params)


@app.get("/assets")
async def get_assets(
    ticker: Optional[str] = None, auth: AuthConfig = Depends(get_auth_config)
):
    """Fetches the trading limits by querying the assets API."""
    params = {"ticker": ticker}
    endpoint = "/v1/assets"
    return await query_api("get", endpoint, auth, params=params)


@app.get("/assets/history")
async def get_assets_history(
    ticker: Optional[str] = None,
    limit: Optional[int] = None,
    period: Optional[int] = None,
    auth: AuthConfig = Depends(get_auth_config),
):
    """Fetches the trading limits by querying the assets/history API."""
    params = {"ticker": ticker, "limit": limit, "period": period}
    endpoint = "/v1/assets/history"
    return await query_api("get", endpoint, auth, params=params)


@app.get("/securities")
async def get_securities(
    ticker: Optional[str] = None, auth: AuthConfig = Depends(get_auth_config)
):
    """Fetches the securities by querying the securities API."""
    return await fetch_securities(auth, ticker=ticker)


@app.get("/securities/book")
async def get_order_book(
    ticker: str,  # Required parameter
    limit: Optional[int] = None,  # Optional parameter,
    auth: AuthConfig = Depends(get_auth_config),
):
    """Fetches the order book of a security by querying the securities/book API."""
    return await fetch_order_book(ticker=ticker, auth=auth, limit=limit)


@app.get("/securities/history")
async def get_security_history(
    ticker: str,
    period: Optional[int] = None,
    limit: Optional[int] = None,
    auth: AuthConfig = Depends(get_auth_config),  # Optional parameter
):
    """Gets the OHLC history for a security."""
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker parameter is required.")

    endpoint = "/v1/securities/history"
    params = {"ticker": ticker}

    if period is not None:
        params["period"] = period
    if limit is not None:
        params["limit"] = limit

    return await query_api("get", endpoint, auth, params=params)


@app.get("/securities/tas")
async def get_time_and_sales(
    ticker: str,  # Required parameter
    after: Optional[int] = None,  # Optional parameter
    period: Optional[int] = None,  # Optional parameter
    limit: Optional[int] = 20,  # Optional parameter with default
    auth: AuthConfig = Depends(get_auth_config),  # Optional parameter
):
    """Gets time & sales history for a security."""
    endpoint = "/v1/securities/tas"
    params = {"ticker": ticker}
    if after is not None:
        params["after"] = after
    if period is not None:
        params["period"] = period
    params["limit"] = limit  # default is 20, but can be overridden
    return await query_api("get", endpoint, auth, params=params)


@app.get("/orders")
async def get_orders(
    status: Optional[str] = "OPEN",  # Optional parameter with default
    auth: AuthConfig = Depends(get_auth_config),  # Optional parameter
):
    """Gets a list of all orders."""
    endpoint = "/v1/orders"
    params = {"status": status}
    return await query_api("get", endpoint, auth, params=params)


# POST /orders
@app.post("/orders")
async def create_order(
    ticker: str,
    ticker_type: str,
    quantity: int,
    action: str,
    price: Optional[float] = None,  # Optional, required if type is LIMIT
    dry_run: Optional[float] = None,  # Optional, only for MARKET type
    auth: AuthConfig = Depends(get_auth_config),  # Optional parameter
):
    """Insert a new order."""
    return await post_order(
        auth=auth,
        ticker=ticker,
        ticker_type=ticker_type,
        quantity=quantity,
        action=action,
        price=price,
        dry_run=dry_run,
    )


# GET /orders/{id}
@app.get("/orders/{id}")
async def get_order_details(
    id: int, auth: AuthConfig = Depends(get_auth_config)  # Optional parameter
):
    """Gets the details of a specific order."""
    endpoint = f"/v1/orders/{id}"
    return await query_api("get", endpoint, auth)


# DELETE /orders/{id}
@app.delete("/orders/{id}")
async def cancel_order(
    id: int, auth: AuthConfig = Depends(get_auth_config)  # Optional parameter
):
    """Cancel an open order."""
    endpoint = f"/v1/orders/{id}"
    return await query_api("delete", endpoint, auth)


# GET /tenders
@app.get("/tenders")
async def get_active_tenders(auth: AuthConfig = Depends(get_auth_config)):
    """Gets a list of all active tenders."""
    return await fetch_active_tenders(auth=auth)


# POST /tenders/{id}
@app.post("/tenders/{id}")
async def accept_tender(
    id: int, price: float, auth: AuthConfig = Depends(get_auth_config)
):
    """Accept the tender."""
    return await accept_tender(id=id, price=price, auth=auth)


# DELETE /tenders/{id}
@app.delete("/tenders/{id}")
async def decline_tender(id: int, auth: AuthConfig = Depends(get_auth_config)):
    """Decline the tender."""
    endpoint = f"/v1/tenders/{id}"
    return await query_api("delete", endpoint, auth)


# GET /leases
@app.get("/leases")
async def list_leases(auth: AuthConfig = Depends(get_auth_config)):
    """List of all assets currently being leased or being used."""
    endpoint = "/v1/leases"
    return await query_api("get", endpoint, auth)


# POST /leases
@app.post("/leases")
async def lease_asset(
    ticker: str,
    from1: Optional[str] = None,
    quantity1: Optional[int] = None,
    from2: Optional[str] = None,
    quantity2: Optional[int] = None,
    from3: Optional[str] = None,
    quantity3: Optional[int] = None,
    auth: AuthConfig = Depends(get_auth_config),
):
    """Lease or use an asset."""
    endpoint = "/v1/leases"
    params = {"ticker": ticker}
    if from1 and quantity1 is not None:
        params["from1"] = from1
        params["quantity1"] = quantity1
    if from2 and quantity2 is not None:
        params["from2"] = from2
        params["quantity2"] = quantity2
    if from3 and quantity3 is not None:
        params["from3"] = from3
        params["quantity3"] = quantity3
    return await query_api("post", endpoint, auth, params=params)


# GET /leases/{id}
@app.get("/leases/{id}")
async def get_lease_details(id: int, auth: AuthConfig = Depends(get_auth_config)):
    """Gets the details of a specific lease."""
    endpoint = f"/v1/leases/{id}"
    return await query_api("get", endpoint, auth)


# POST /leases/{id}
@app.post("/leases/{id}")
async def use_leased_asset(
    id: int,
    from1: str,
    quantity1: int,
    from2: Optional[str] = None,
    quantity2: Optional[int] = None,
    from3: Optional[str] = None,
    quantity3: Optional[int] = None,
    auth: AuthConfig = Depends(get_auth_config),
):
    """Use a leased asset."""
    endpoint = f"/v1/leases/{id}"
    params = {"from1": from1, "quantity1": quantity1}
    if from2 and quantity2 is not None:
        params["from2"] = from2
        params["quantity2"] = quantity2
    if from3 and quantity3 is not None:
        params["from3"] = from3
        params["quantity3"] = quantity3
    return await query_api("post", endpoint, auth, params=params)


# DELETE /leases/{id}
@app.delete("/leases/{id}")
async def unlease_asset(id: int, auth: AuthConfig = Depends(get_auth_config)):
    """Unlease an asset."""
    endpoint = f"/v1/leases/{id}"
    return await query_api("delete", endpoint, auth)


# POST /commands/cancel
@app.post("/commands/cancel")
async def bulk_cancel_orders(
    all: Optional[int] = None,
    ticker: Optional[str] = None,
    ids: Optional[str] = None,
    auth: AuthConfig = Depends(get_auth_config),
):
    """Bulk cancel open orders."""
    endpoint = "/v1/commands/cancel"
    params = {}
    if all is not None:
        params["all"] = all
    elif ticker is not None:
        params["ticker"] = ticker
    elif ids is not None:
        params["ids"] = ids
    else:
        raise HTTPException(
            status_code=400,
            detail="One of 'all', 'ticker', or 'ids' must be specified.",
        )

    return await query_api("post", endpoint, auth, params=params)
