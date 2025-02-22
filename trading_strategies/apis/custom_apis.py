from typing import Optional

from fastapi import APIRouter, Depends

from trading_strategies.apis.api_utility import cancel_all_open_order as caoo
from trading_strategies.apis.api_utility import (
    cancel_open_orders,
    fetch_current_tick,
    get_auth_config,
)
from trading_strategies.apis.api_utility import market_square_off_all_tickers as msoat
from trading_strategies.apis.api_utility import market_square_off_ticker as msot
from trading_strategies.apis.api_utility import query_api
from trading_strategies.models.custom_models import AuthConfig

router = APIRouter()


@router.get("/tick")
async def get_current_tick(auth: AuthConfig = Depends(get_auth_config)):
    """Fetches the current tick by querying the case API."""
    return await fetch_current_tick(auth=auth)


@router.get("/period")
async def get_trading_period(auth: AuthConfig = Depends(get_auth_config)):
    """Fetches the current period by querying the case API."""
    try:
        case_data = await query_api("get", "/v1/case", auth)  # Direct API call
    except Exception:
        return None
    return case_data["period"]


@router.get("/status")
async def get_trading_status(auth: AuthConfig = Depends(get_auth_config)):
    """Fetches the current trading status by querying the case API."""
    try:
        case_data = await query_api("get", "/v1/case", auth)  # Direct API call
    except Exception:
        return None
    return case_data["status"]


@router.delete("/all_orders")
async def cancel_all_open_order(auth: AuthConfig = Depends(get_auth_config)):
    """Fetches the OPEN orders and cancels them till all are cancelled.
    If exception happens, it logs it and keeps on trying.
    """
    return await caoo(auth)


@router.delete("/all_orders/{ticker}")
async def cancel_all_open_order_for_ticker(
    ticker: str, auth: AuthConfig = Depends(get_auth_config)
):
    """Fetches the OPEN orders for a specific ticker and cancels them till all are cancelled.
    If exception happens, it logs it and keeps on trying.
    """
    # TODO @Mayuresh If error happens do to rate limiting then try again
    open_orders = await query_api("get", "/v1/orders", auth, params={"status": "OPEN"})
    filtered_orders = [order for order in open_orders if order["ticker"] == ticker]
    # print(f"Open orders for ticker {ticker} are {filtered_orders}")
    await cancel_open_orders(filtered_orders, auth)
    print(f"Cancelled all open orders for ticker {ticker}")
    return True


@router.post("/market_square_off")
async def market_square_off_all_tickers(
    batch_size: Optional[int] = 10000, auth: AuthConfig = Depends(get_auth_config)
):
    """Fetches the list of securities and then squares them off at the MARKET."""
    return await msoat(auth, batch_size=batch_size)


@router.post("/market_square_off/{ticker}")
async def market_square_off_ticker(
    ticker: str,
    batch_size: Optional[int] = 10000,
    auth: AuthConfig = Depends(get_auth_config),
):
    """Fetches the current ticker position and squares off."""
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker parameter is required.")

    securities_params = {"ticker": ticker}
    endpoint = "/v1/securities"
    # TODO @Mayuresh If error happens do to rate limiting then try again
    securities_data = await query_api("get", endpoint, auth, params=securities_params)
    await msot(int(securities_data[0]["position"]), ticker, auth=auth)
    print(
        f"Trade for {ticker} squared off with for initial position: {securities_data[0]['position']}"
    )
