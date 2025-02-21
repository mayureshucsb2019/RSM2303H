import asyncio

from trading_strategies.custom_models import AuthConfig


async def is_tender_processed(
    auth: AuthConfig, ticker: str, quantity: int, initial_position: int
):
    """Asynchronously checks if a tender has been processed."""
    processing_count = 0
    while processing_count < 5:
        try:
            securities_data = await query_securities(auth, ticker)
            print(
                f"Checking if tender processed, quantity:{quantity} difference:{abs(abs(initial_position) - abs(securities_data[0]['position']))} initial_position:{initial_position} current_position:{securities_data[0]['position']} "
            )
        except Exception as e:
            print(f"An error occurred while querying security {ticker}: {e}")
        if abs(abs(initial_position) - abs(securities_data[0]["position"])) >= int(
            0.5 * abs(quantity)
        ):
            print(f"Tender has been processed")
            return True
        await asyncio.sleep(0.1)
        processing_count += 1
    print(f"Tender wasn't processed")
    return False


async def chunk_order(
    auth: AuthConfig, order_details: OrderRequest, batch_size: int = 10000
):
    quantity = order_details.quantity
    while True:
        if quantity >= batch_size:
            order_details.quantity = batch_size
            quantity -= batch_size
        elif quantity > 0 and quantity < batch_size:
            order_details.quantity = quantity
            quantity = 0
        else:
            break
        await post_order(auth, order_details)
        await asyncio.sleep(0.1)


# Strategy
async def market_square_off_all_tickers(auth, batch_size: int = 10000):
    securities_data = await query_securities(auth)  # Fetch all tickers automatically
    for security in securities_data:
        asyncio.create_task(
            market_square_off_ticker(auth, security["ticker"], batch_size)
        )


async def market_square_off_ticker(
    auth: AuthConfig, ticker: str, batch_size: int = 10000
):
    securities_data = await query_securities(auth, ticker)
    while int(securities_data[0]["position"]) != 0:
        if securities_data[0]["position"] > 0:
            action = "SELL"
        else:
            action = "BUY"

        if abs(securities_data[0]["position"]) > batch_size:
            quantity = batch_size
        else:
            quantity = abs(securities_data[0]["position"])

        order_details = OrderRequest(
            ticker=ticker, type="MARKET", quantity=quantity, action=action, dry_run=0
        )
        await post_order(auth, order_details)
        await asyncio.sleep(0.1)
        securities_data = await query_securities(auth, ticker)
    print(f"Trade for {ticker} squared off")
