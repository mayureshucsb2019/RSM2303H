import asyncio
import threading

import trading_strategies.apis.rit_apis as rit
from trading_strategies.apis.api_utility import (
    accept_tender,
    fetch_active_tenders,
    fetch_current_tick,
    fetch_securities,
    post_order,
)
from trading_strategies.logger_config import setup_logger
from trading_strategies.models.custom_models import AuthConfig
from trading_strategies.strategy.SOR_strategy_utility import parse_SOR_env_variables

logger = setup_logger(__name__)
last_tender_price = 0
current_tick = 0
max_tick = 0
slippage_margin = 0


async def generate_sor_signal(
    auth: AuthConfig,
    ticker: str,
    price: float,
    action: str,
    quantity: int,
    vwap_margin: float,
    tender_id: int,
):
    securities_data = await fetch_securities(auth)
    
    # Compute Global VWAP
    total_volume = sum(security["volume"] for security in securities_data)
    global_vwap = sum(security["volume"] * security["last"] for security in securities_data) / total_volume

    # Evaluate execution condition
    price_threshold = price + vwap_margin if action == "BUY" else price - vwap_margin
    if (action == "BUY" and price_threshold < global_vwap) or (action == "SELL" and price_threshold > global_vwap):
        logger.info(f"Tender accepted: {ticker} {price} {action} {quantity}, global_vwap: {global_vwap}")
        return await accept_tender(auth=auth, id=tender_id, price=price)

    logger.info(f"Waiting for better conditions: {ticker} {price} {action} {quantity}, global_vwap: {global_vwap}")
    return {"success": False}


async def smart_order_routing(auth: AuthConfig, block_quantity: int = 1500):
    global last_tender_price, current_tick, max_tick, slippage_margin
    logger.info("STARTING SMART ORDER ROUTING")
    
    while True:
        try:
            securities_data = await fetch_securities(auth)
            current_position = next((s["position"] for s in securities_data), 0)
            last_A = next((s["last"] for s in securities_data if s["ticker"].endswith("A")), 0)
            last_M = next((s["last"] for s in securities_data if s["ticker"].endswith("M")), 0)
            
            if current_position == 0:
                logger.info("NO POSITION TO ROUTE")
                await asyncio.sleep(1)
                continue
            
            logger.info("#### ROUTING NOW ...")
            logger.info(f"tick {current_tick}: tender price: {last_tender_price}, slippage {slippage_margin}, last_A {last_A}, last_M {last_M}")
            squareoff_action = "SELL" if current_position > 0 else "BUY"
            quantity = min(abs(current_position), block_quantity)
            ticker = "THOR_A" if (squareoff_action == "SELL" and last_A > last_M) or (squareoff_action == "BUY" and last_A < last_M) else "THOR_M"
            
            logger.info(f"squareoff details {squareoff_action} {quantity} of {ticker}")
            
            price_condition = (
                (squareoff_action == "SELL" and ticker == "THOR_A" and last_A > last_tender_price + slippage_margin) or
                (squareoff_action == "SELL" and ticker == "THOR_M" and last_M > last_tender_price + slippage_margin) or
                (squareoff_action == "BUY" and ticker == "THOR_A" and last_A < last_tender_price - slippage_margin) or
                (squareoff_action == "BUY" and ticker == "THOR_M" and last_M < last_tender_price - slippage_margin) or
                (current_tick > max_tick - 10)
            )
            
            if price_condition:
                await post_order(auth, ticker, "MARKET", quantity, squareoff_action)
            else:
                logger.info("Price is not profitable.......")
            await asyncio.sleep(0.03)        
        except Exception as e:
            logger.error(f"Unable to get current tick {e}, redo loop")
            await asyncio.sleep(0.03)
            continue

def run_async_in_thread(auth):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(smart_order_routing(auth))
    loop.close()


async def SOR():
    global max_tick, last_tender_price, current_tick, slippage_margin
    sor_config = parse_SOR_env_variables()
    max_tick = sor_config["SOR_TRADE_UNTIL_TICK"]
    slippage_margin = sor_config["SOR_SLIPPAGE_MARGIN"]
    auth = AuthConfig(**sor_config["auth"])

    # Create and start a new thread
    threading.Thread(target=run_async_in_thread, args=(auth,), daemon=True).start()

    logger.info(sor_config)
    logger.info(await rit.get_case_status(auth=auth))

    while True:
        try:
            current_tick = await fetch_current_tick(auth)
            logger.info(f"Current tick is {current_tick}")
            
            # Fetch new tenders if current_tick is within allowed range
            tender_response = {"success": False}
            if current_tick <= max_tick:
                logger.info("Looking for new tenders")
                tender_response = await fetch_active_tenders(auth)
                if tender_response:
                    logger.info(f"Details of tender received: \n{tender_response}")
                    for tender in tender_response:
                        logger.info(tender)
                        last_tender_price = tender["price"]
                        tender_response = await generate_sor_signal(
                            auth=auth,
                            ticker=tender["ticker"],
                            price=tender["price"],
                            action=tender["action"],
                            quantity=tender["quantity"],
                            vwap_margin=sor_config["SOR_MIN_VWAP_MARGIN"],
                            tender_id=tender["tender_id"],
                        )
                    if tender_response["success"]:
                        logger.info("Tender accepted now sleeping tender check for 30 seconds to square off")
                        await asyncio.sleep(30)
            else:
                # End of period - Sleep briefly
                await asyncio.sleep(1)
                continue

        except Exception as e:
            logger.error(f"Error {e}, retrying...")
        await asyncio.sleep(1)
