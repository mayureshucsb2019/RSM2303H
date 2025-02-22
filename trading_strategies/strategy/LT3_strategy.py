import asyncio
import random
from typing import Awaitable, Callable

from trading_strategies.apis.api_utility import (
    accept_tender,
    cancel_all_open_order,
    fetch_active_tenders,
    fetch_current_tick,
    fetch_securities,
    is_tender_processed,
    market_square_off_all_tickers,
    post_order,
)
from trading_strategies.models.custom_models import AuthConfig
from trading_strategies.strategy.LT3_strategy_utility import generate_lt3_signal


async def limit_square_off_ticker_randomized_price(
    auth: AuthConfig,
    ticker: str,
    action: str,
    price: int,
    quantity: int,
    batch_size: int = 10000,
):
    """Squares off a ticker position with randomized price using limit orders."""
    while True:
        random_choice = random.choice([0, 0.05, 0.1, 0.15, 0.2])
        # TODO: if error happens then this computation cannot be recovered back, add new logic @mayuresh
        ticker_type = ""
        if quantity >= batch_size:
            ticker = ticker
            ticker_type = "MARKET" if random_choice == 0 else "LIMIT"
            temp_price = (
                None
                if random_choice == 0
                else price - random_choice
                if action == "BUY"
                else price + random_choice
            )
            action = action
            temp_quantity = batch_size
            quantity -= batch_size
        elif quantity > 0 and quantity < batch_size:
            ticker = ticker
            ticker_type = "MARKET" if random_choice == 0 else "LIMIT"
            temp_price = (
                None
                if random_choice == 0
                else price - random_choice
                if action == "BUY"
                else price + random_choice
            )
            action = action
            temp_quantity = quantity
            quantity = 0
        else:
            break
        try:
            await post_order(
                auth=auth,
                ticker=ticker,
                ticker_type=ticker_type,
                quantity=temp_quantity,
                action=action,
                price=temp_price,
                dry_run=0,
            )
            print(
                f"Trade for {action} {temp_quantity} {ticker} placed at  {temp_price}"
            )
        except Exception as e:
            print(
                f"An error occurred while posting the order {(ticker, ticker_type, quantity, action, price,)}: {e}"
            )
        await asyncio.sleep(0.1)


async def run_l3_strategy(
    strategy_func: Callable[[AuthConfig, str, str, int, int, int], Awaitable[None]],
    lt3_config,
):
    """Runs the LT3 strategy by continuously monitoring and acting on tenders."""
    auth = AuthConfig(**lt3_config["auth"])
    end_of_time_hit = False
    while True:
        tender_response = []
        try:
            current_tick = await fetch_current_tick(auth)
            print(f"Current tick is {current_tick}")
        except Exception as e:
            print(f"Unable to get current tick {e}, redo loop")
            await asyncio.sleep(0.2)
            continue

        if current_tick == 0:  # start of new session
            end_of_time_hit = False
        # fetch new tenders if available
        if current_tick <= lt3_config["T3_TRADE_UNTIL_TICK"]:
            tender_response = await fetch_active_tenders(auth)
        else:  # end of period
            print(
                f"Current tick is {current_tick} more than cutoff time {lt3_config['T3_TRADE_UNTIL_TICK']} end_of_time_hit:{end_of_time_hit}"
            )
            if not end_of_time_hit:
                print("End of period hit, squaring off all open positions")
                # First cancel all open orders
                await cancel_all_open_order(auth)
                # Second square of all tickers
                asyncio.create_task(
                    market_square_off_all_tickers(
                        auth, lt3_config["T3_SQUARE_OFF_BATCH_SIZE"]
                    )
                )
                end_of_time_hit = True

        if tender_response:
            print(f"Details of tender received is: \n{tender_response}")
            for tender in tender_response:
                signal_response = await generate_lt3_signal(
                    auth,
                    tender["ticker"],
                    tender["price"],
                    tender["action"],
                    tender["quantity"],
                    lt3_config["T3_MIN_VWAP_MARGIN"],
                )
                squareoff_action = "SELL" if tender["action"] == "BUY" else "BUY"
                print(f"Signal analysed: \n{signal_response}")
                if signal_response[0]:
                    securities_data = await fetch_securities(auth)
                    net_position = 0
                    gross_position = 0
                    security_position = {}
                    # Initialize security_position from securities_data
                    for security in securities_data:
                        security_position[security["ticker"]] = security["position"]

                    tender_quantity = (
                        -1 * tender["quantity"]
                        if tender["action"] == "SELL"
                        else tender["quantity"]
                    )
                    security_position[tender["ticker"]] += tender_quantity

                    for ticker, position in security_position.items():
                        net_position += position
                        gross_position += abs(position)

                    print(
                        f"net_position:{net_position} gross_position:{gross_position}"
                    )
                    if (
                        abs(net_position) > lt3_config["T3_NET_LIMIT"]
                        or gross_position > lt3_config["T3_GROSS_LIMIT"]
                    ):
                        print(f"Cannot accept this tender at this time")
                        break
                    securities_data = await fetch_securities(auth, tender["ticker"])
                    print(
                        f"Queried intial position for {ticker} is {securities_data[0]['position']}"
                    )
                    tender_response = await accept_tender(
                        auth=auth, id=tender["tender_id"], price=tender["price"]
                    )
                    print(f"Tender accepted: {tender_response}")
                    if tender_response["success"]:
                        is_tender_processed_flag = await is_tender_processed(
                            auth,
                            tender["ticker"],
                            tender["quantity"],
                            securities_data[0]["position"],
                        )
                        if is_tender_processed_flag:
                            asyncio.create_task(
                                strategy_func(
                                    auth,
                                    tender["ticker"],
                                    squareoff_action,
                                    tender["price"],
                                    tender["quantity"],
                                    lt3_config["T3_SQUARE_OFF_BATCH_SIZE"],
                                )
                            )

                else:
                    print(f"Waiting for favorable condition to accept tender")

        await asyncio.sleep(1)
