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
    global_vwap = 0
    total_volume = 0
    for security in securities_data:
        logger.info(f"securitiey is {security}")
        global_vwap += security["volume"] * security["last"]
        total_volume += security["volume"]
    global_vwap = global_vwap / total_volume

    tender_response = ""
    if (price + vwap_margin < global_vwap and action == "BUY") or (
        price - vwap_margin > global_vwap and action == "SELL"
    ):
        logger.info(
            f"tender accepted: {ticker} {price} {action} {quantity} : global_vwap:{global_vwap} {price  + vwap_margin} {price} {price  - vwap_margin}"
        )
        tender_response = await accept_tender(auth=auth, id=tender_id, price=price)

    else:
        logger.info(
            f"waiting for favorable condition: {ticker} {price} {action} {quantity} : global_vwap:{global_vwap}  {price  + vwap_margin} {price} {price  - vwap_margin}"
        )


async def smart_order_routing(auth: AuthConfig, block_quantity: int = 2000):
    global last_tender_price
    logger.info("STARTING SMART ORDER ROUTING")
    buffer_margin = 0.02
    while True:
        try:
            securities_data = await fetch_securities(auth)
            current_position = 0
            last_M = 0
            last_A = 0
            for security in securities_data:
                current_position = security["position"]
                if security["ticker"][-1] == "A":
                    last_A = security["last"]
                else:
                    last_M = security["last"]
            if current_position != 0:
                logger.info("#### ROUTING NOW ...")
                squareoff_action = "SELL" if current_position > 0 else "BUY"
                quantity = (
                    block_quantity
                    if abs(current_position) > block_quantity
                    else abs(current_position)
                )
                if squareoff_action == "SELL":
                    if last_A > last_M:
                        ticker = "THOR_A"
                    else:
                        ticker = "THOR_M"
                else:
                    if last_A < last_M:
                        ticker = "THOR_A"
                    else:
                        ticker = "THOR_M"
                logger.info(f"{squareoff_action} {quantity} of {ticker}")
                if squareoff_action == "SELL" and (
                    (ticker == "THOR_A" and last_A > last_tender_price + buffer_margin)
                    or (
                        ticker == "THOR_M"
                        and last_M > last_tender_price + buffer_margin
                    )
                ):
                    await post_order(
                        auth=auth,
                        ticker=ticker,
                        ticker_type="MARKET",
                        quantity=quantity,
                        action=squareoff_action,
                    )
                elif squareoff_action == "BUY" and (
                    (ticker == "THOR_A" and last_A < last_tender_price - buffer_margin)
                    or (
                        ticker == "THOR_M"
                        and last_M < last_tender_price - buffer_margin
                    )
                ):
                    await post_order(
                        auth=auth,
                        ticker=ticker,
                        ticker_type="MARKET",
                        quantity=quantity,
                        action=squareoff_action,
                    )
                else:
                    logger.info("Price is not profitable.......")
            else:
                logger.info("NO POSITION TO ROUTE")
        except Exception as e:
            logger.error(f"Unable to get current tick {e}, redo loop")
            asyncio.sleep(0.1)
            continue
        await asyncio.sleep(0.1)


def run_async_in_thread(auth):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(smart_order_routing(auth))
    loop.close()


async def SOR():
    sor_config = parse_SOR_env_variables()
    auth = AuthConfig(**sor_config["auth"])
    # Create and start a new thread
    thread = threading.Thread(target=run_async_in_thread, args=(auth,))
    thread.daemon = True  # Ensures thread exits when the main program does
    thread.start()

    logger.info(sor_config)
    logger.info(await rit.get_case_status(auth=auth))
    end_of_time_hit = False
    global last_tender_price
    while True:
        tender_response = []
        try:
            current_tick = await fetch_current_tick(auth)
            logger.info(f"Current tick is {current_tick}")
            await asyncio.sleep(0.2)
        except Exception as e:
            logger.error(f"Unable to get current tick {e}, redo loop")
            await asyncio.sleep(0.2)
            continue
        if current_tick == 0:  # start of new session
            end_of_time_hit = False
        # fetch new tenders if available
        if current_tick <= sor_config["SOR_TRADE_UNTIL_TICK"]:
            logger.info(f"Looking for new tenders")
            tender_response = await fetch_active_tenders(auth)
            logger.info(f"tender response: {tender_response}")
        else:  # end of period
            logger.info(
                f"Current tick is {current_tick} more than cutoff time {sor_config['SOR_TRADE_UNTIL_TICK']} end_of_time_hit:{end_of_time_hit}"
            )
            # if not end_of_time_hit:
            #     logger.info("End of period hit, squaring off all open positions")
            #     # Second square of all tickers
            #     asyncio.create_task(
            #         market_square_off_ticker(
            #             auth, SOR_config["SOR_SQUARE_OFF_BATCH_SIZE"]
            #         )
            #     )
            #     end_of_time_hit = True
            await asyncio.sleep(1)
            continue

        if tender_response:
            logger.info(f"Details of tender received is: \n{tender_response}")
            for tender in tender_response:
                logger.info(tender)
                last_tender_price = tender["price"]
                await generate_sor_signal(
                    auth=auth,
                    ticker=tender["ticker"],
                    price=tender["price"],
                    action=tender["action"],
                    quantity=tender["quantity"],
                    vwap_margin=sor_config["SOR_MIN_VWAP_MARGIN"],
                    tender_id=tender["tender_id"],
                )
        await asyncio.sleep(1)
