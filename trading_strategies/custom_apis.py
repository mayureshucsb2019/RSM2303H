import asyncio
from typing import Optional

from fastapi import APIRouter, Depends

from trading_strategies.api_utility import get_auth_config, query_api
from trading_strategies.custom_models import AuthConfig

router = APIRouter()


@router.get("/tick")
async def get_current_tick(auth: AuthConfig = Depends(get_auth_config)):
    """Fetches the current tick by querying the case API."""
    try:
        case_data = await query_api("get", "/v1/case", auth)  # Direct API call
    except Exception:
        return None
    return case_data.get("tick")  # Use .get() to avoid KeyError


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
    # TODO @Mayuresh If error happens do to rate limiting then try again
    open_orders = await query_api("get", "/v1/orders", auth, params={"status": "OPEN"})
    # print(f"Open orders are {[order["order_id"] for order in open_orders]}")
    await cancel_open_orders(open_orders, auth)
    print("Cancelled all open orders")
    return True


@router.delete("/all_orders/{ticker}")
async def cancel_all_open_order_for_ticker(
    ticker: str, auth: AuthConfig = Depends(get_auth_config)
):
    """Fetches the OPEN orders and cancels them till all are cancelled.
    If exception happens, it logs it and keeps on trying.
    """
    # TODO @Mayuresh If error happens do to rate limiting then try again
    open_orders = await query_api("get", "/v1/orders", auth, params={"status": "OPEN"})
    filtered_orders = [order for order in open_orders if order["ticker"] == ticker]
    # print(f"Open orders for ticker {ticker} are {filtered_orders}")
    await cancel_open_orders(filtered_orders, auth)
    print(f"Cancelled all open orders for ticker {ticker}")
    return True


@router.post("/market_square_off_all")
async def market_square_off_all_tickers(
    batch_size: Optional[int] = 10000, auth: AuthConfig = Depends(get_auth_config)
):
    endpoint = "/v1/securities"
    # TODO @Mayuresh If error happens do to rate limiting then try again
    securities_data = await query_api("get", endpoint, auth)
    for security in securities_data:
        await square_off_ticker(security["position"], security["ticker"], auth=auth)
    print(f"Trade for all tickers squared off")


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
    await square_off_ticker(int(securities_data[0]["position"]), ticker, auth=auth)
    print(
        f"Trade for {ticker} squared off with for initial position: {securities_data[0]['position']}"
    )


async def square_off_ticker(
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
