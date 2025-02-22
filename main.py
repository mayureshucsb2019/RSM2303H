import asyncio

import trading_strategies.apis.rit_apis as rit
from trading_strategies.apis.api_utility import get_auth_config

from trading_strategies.strategy.LT3_strategy import (
    limit_square_off_ticker_randomized_price,
    run_l3_strategy,
)
from trading_strategies.strategy.LT3_strategy_utility import parse_lt3_env_variables
from trading_strategies.strategy.strategy_utility import (
    display_market_depth_table,
    generate_single_market_depth_for_ticker,
)


async def main():
    # APIs to fetch case info, trader info, news, and limits
    print(await rit.get_case_status(auth=get_auth_config()))
    # print(await rit.get_trader_info(auth=get_auth_config()))
    # print(await rit.get_recent_news(after=0, auth=get_auth_config()))
    # print(await rit.get_trading_limits(auth=get_auth_config()))

    # APIs to fetch information about the assets
    # print(await rit.get_assets(auth=get_auth_config()))
    # print(await rit.get_assets_history(auth=get_auth_config()))

    # APIs to fetch information about securities
    # print(await rit.get_securities(auth=get_auth_config()))
    # print(await rit.get_securities(ticker="CRZY_A", auth=get_auth_config()))
    # print(await rit.get_order_book(ticker="CRZY", auth=get_auth_config()))
    # print(await rit.get_security_history(ticker="CRZY", auth=get_auth_config()))
    # print(await rit.get_time_and_sales(ticker="CRZY", auth=get_auth_config()))

    # print(await rit.get_orders(auth=get_auth_config()))
    # create_order = await rit.create_order(
    #     ticker="CRZY",
    #     ticker_type="MARKET",
    #     quantity=10000,
    #     action="SELL",
    #     price=12.0,
    #     auth=get_auth_config(),
    # )
    # print(create_order)
    # print(
    #     await rit.get_order_details(id=create_order["order_id"], auth=get_auth_config())
    # )
    # print(await rit.cancel_order(id=create_order["order_id"], auth=get_auth_config()))

    # tenders = await rit.get_active_tenders(auth=get_auth_config())
    # for tender in tenders:
    #     print(tender)
    #     print(
    #         await rit.accept_tender(
    #             id=tender["tender_id"], price=tender["price"], auth=get_auth_config()
    #         )
    #     )
    #     print(await rit.decline_tender(id=tender["tender_id"], auth=get_auth_config()))

    # CUSTOM APIS ######################################################################

    # print(await custom_api.get_current_tick(auth=get_auth_config()))
    # print(await custom_api.get_trading_period(auth=get_auth_config()))
    # print(await custom_api.get_trading_status(auth=get_auth_config()))

    # print(await custom_api.cancel_all_open_order(auth=get_auth_config()))
    # print(await custom_api.cancel_all_open_order_for_ticker("CRZY", auth=get_auth_config()))

    # print(await custom_api.market_square_off_ticker("CRZY", auth=get_auth_config()))
    # print(await custom_api.market_square_off_all_tickers(auth=get_auth_config()))

    await run_l3_strategy(
        limit_square_off_ticker_randomized_price, parse_lt3_env_variables()
    )

    # ticker = "CRZY"
    # bid, ask = await generate_single_market_depth_for_ticker(auth=get_auth_config(), ticker=ticker)
    # display_market_depth_table(ticker=ticker, bid_data=bid, ask_data=ask)
    # while True:
    #     await generate_integrated_global_orderbook(auth=get_auth_config(), tickers=["CRZY_A", "CRZY_M"])
    #     await asyncio.sleep(1)
    # while True:
    #     await generate_aggregate_orderbook(auth=get_auth_config(), tickers=["CRZY_A", "CRZY_M"])
    #     await asyncio.sleep(1)
    # while True:
    #     bid, ask = await generate_single_market_depth_for_ticker(
    #         auth=get_auth_config(), ticker="CRZY"
    #     )
    #     display_market_depth_table("CRZY", bid, ask)
    #     await asyncio.sleep(0.05)


if __name__ == "__main__":
    asyncio.run(main())
