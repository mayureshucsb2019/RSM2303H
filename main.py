import asyncio


async def main():
    print(await rit.get_case_status(auth=get_auth_config()))
    print(await rit.get_trader_info(auth=get_auth_config()))
    print(await rit.get_recent_news(after=0, auth=get_auth_config()))
    print(await rit.get_assets(auth=get_auth_config()))

    print(await rit.get_assets(auth=get_auth_config()))
    print(await rit.get_assets_history(auth=get_auth_config()))

    print(await rit.get_securities(auth=get_auth_config()))
    print(await rit.get_securities(ticker="CRZY", auth=get_auth_config()))
    print(await rit.get_order_book(ticker="CRZY", auth=get_auth_config()))
    print(await rit.get_security_history(ticker="CRZY", auth=get_auth_config()))
    print(await rit.get_time_and_sales(ticker="CRZY", auth=get_auth_config()))

    print(await rit.get_orders(auth=get_auth_config()))
    create_order = await rit.create_order(
        ticker="CRZY",
        ticker_type="LIMIT",
        quantity=10,
        action="SELL",
        price=12.0,
        auth=get_auth_config(),
    )
    print(create_order)
    print(
        await rit.get_order_details(id=create_order["order_id"], auth=get_auth_config())
    )
    print(await rit.cancel_order(id=create_order["order_id"], auth=get_auth_config()))

    tenders = await rit.get_active_tenders(auth=get_auth_config())
    for tender in tenders:
        print(tender)
        print(
            await rit.accept_tender(
                id=tender["tender_id"], price=tender["price"], auth=get_auth_config()
            )
        )
        print(await rit.decline_tender(id=tender["tender_id"], auth=get_auth_config()))


if __name__ == "__main__":
    asyncio.run(main())
