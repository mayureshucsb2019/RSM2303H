from trading_strategies.logger_config import setup_logger
from trading_strategies.strategy.Var_utility import (
    parse_var_env_variables, 
    calculate_var, 
    optimize_portfolio,
    calculate_units
)
from trading_strategies.models.custom_models import AuthConfig
import trading_strategies.apis.rit_apis as rit
from trading_strategies.apis.api_utility import (
    cancel_open_orders,
    fetch_current_tick,
    get_auth_config,
    fetch_securities,
    post_order
)
import asyncio, re, numpy as np

logger = setup_logger(__name__)

def calculate_fractions(portfolio: dict) -> list[float]:
    logger.info(f"Portfolio is {portfolio}")
    assets = ['US', 'BRIC', 'BOND', 'CASH']
    total_value = sum(portfolio[asset]['position'] * portfolio[asset]['last'] for asset in assets)
    
    if total_value == 0:
        return [0.0, 0.0, 0.0, 0.0]  # Avoid division by zero
    
    fractions = [(portfolio[asset]['position'] * portfolio[asset]['last']) / total_value for asset in assets]
    logger.info(f"Fractions are {fractions}, total value is {total_value}")
    return fractions, total_value

async def fetch_securities_position(auth: AuthConfig):
    current_value = {}
    securities = await fetch_securities(auth=auth)
    for security in securities:
        ticker_detail = {}
        ticker_detail['position'] = security['position']
        ticker_detail['last'] = security['last']
        current_value[security['ticker']] = ticker_detail
    return current_value

async def parse_recent_news(auth: AuthConfig):
    all_news = await rit.get_recent_news(auth=auth)
    print("news received of length",len(all_news))
    # pattern = r"tick (\d+).*?US = \$(\d+\.\d+).*?BRIC = \$(\d+\.\d+).*?BOND (\d+\.\d+)"
    pattern = r"tick (\d+).*?US = \$(\d+(?:\.\d{1,2})?).*?BRIC = \$(\d+(?:\.\d{1,2})?).*?BOND (\d+(?:\.\d{1,2})?)"
    if len(all_news) <= 1:
        return {}, 0
    match = re.search(pattern, all_news[0]['body'])
    if match:
        tick, us, bric, bond = match.groups()
        return {"tick": int(tick), "US": float(us), "BRIC":float(bric), "BOND":float(bond)}, len(all_news)
    return {}, len(all_news)

async def batch_post_order(auth: AuthConfig, quantity: int, ticker: str, action: str, order_type: str = "MARKET", price :float = 0, batch_size: int=5000):
    price_volume = []
    while quantity > 0:
        order_quantity = batch_size if quantity > batch_size else quantity
        quantity -= order_quantity
        order_response = await post_order(auth, ticker, ticker_type=order_type, quantity=order_quantity, price=price, action=action)
        if order_type == "MARKET":
            price_volume.append((order_response['vwap'],order_response['quantity']))
    if order_type == "MARKET":
        total_price_volume = sum(price * volume for price, volume in price_volume)
        total_volume = sum(volume for _, volume in price_volume)
        return (total_price_volume / total_volume if total_volume != 0 else 0, total_volume)
    return (price, quantity)

async def decide_square_off(auth: AuthConfig, current_position: dict, analyst_expectation: dict, quantity: int = 0):
    assets = ['US', 'BRIC', 'BOND']
    logger.info(current_position)
    logger.info(analyst_expectation)
    for asset in assets:
        if current_position[asset]["position"] != 0.0:
            if quantity == 0:            
                if current_position[asset]["position"] > 0 and current_position[asset]["last"] >= analyst_expectation[asset]:
                    await batch_post_order(auth, current_position[asset]["position"], asset, "SELL", "MARKET")
                    logger.info(f"Squared off by selling {asset} ")
                elif current_position[asset]["position"] < 0 and current_position[asset]["last"] <= analyst_expectation[asset]:
                    await batch_post_order(auth, current_position[asset]["position"]*-1, asset, "BUY", "MARKET")
                    logger.info(f"Squared off by buying {asset} ")
                else:
                    logger.info("Not reached expectation")
            else:
                logger.info(f"Reducing {asset} VaR")
                if current_position[asset]["position"] > 0:
                    await batch_post_order(auth, quantity, asset, "SELL", "MARKET")
                else:
                    await batch_post_order(auth, quantity, asset, "BUY", "MARKET")


async def Var(risk_value: float = 20000):
    """Runs the Var strategy by continuously monitoring and acting on new News."""
    auth = AuthConfig(**parse_var_env_variables()["auth"])
    case_status = await rit.get_case_status(auth)
    case_status = case_status["status"]
    current_value = {}
    # Given volatilities (converted to decimals) US BRIC BOND
    volatilities = np.array([1.31, 1.61, 0.55, 0]) / 100

    # Correlation matrix including CASH (CASH has no volatility and no correlation with other assets)
    correlation_matrix = np.array([
        [1.000, 0.480, 0.068, 0.0],  # US
        [0.480, 1.000, 0.005, 0.0],  # BRIC
        [0.068, 0.005, 1.000, 0.0],  # BOND
        [0.0, 0.0, 0.0, 1.000]       # CASH (no volatility or correlation with other assets)
    ])

    # Portfolio value
    portfolio_value = 1000000
    number_of_news = 0
    value_at_risk = 0

    while True:
        try:
            case_status = (await rit.get_case_status(auth))["status"]
            if case_status != "ACTIVE":
                logger.info(f"Case is NOT ACTIVE: {case_status}")
                number_of_news = 0
                value_at_risk = 0
                await asyncio.sleep(1)
                continue
            current_value.update(await fetch_securities_position(auth))
            logger.info(f"Current value: {current_value}")
            analyst_expectation, new_news_length = await parse_recent_news(auth=auth)
            logger.info(f"Analyst expectation {analyst_expectation}")
            # make a new transaction only if new news arrives
            if new_news_length > number_of_news:
                number_of_news = new_news_length
                expected_returns = np.array([
                    (analyst_expectation['US'] - current_value['US']['last']) / current_value['US']['last'],
                    (analyst_expectation['BRIC'] - current_value['BRIC']['last']) / current_value['BRIC']['last'],
                    (analyst_expectation['BOND'] - current_value['BOND']['last']) / current_value['BOND']['last']
                ])
                logger.info(f"Expected returns after news is {expected_returns}")

                # Calculate both "go long" and "short sell" returns
                long_returns = expected_returns
                short_returns = -expected_returns  # Short selling flips the expected return

                # Combine long and short returns, then find the maximum return
                max_return_index = np.argmax(np.concatenate([long_returns, short_returns]))

                # Determine which ticker corresponds to the maximum return
                tickers = ['US', 'BRIC', 'BOND']
                max_action = 'BUY' if max_return_index < 3 else 'SELL'
                square_off_action = 'SELL' if max_action == "BUY" else 'BUY'
                max_return_ticker = tickers[max_return_index % 3]

                units_to_transact = calculate_units(price_per_unit=current_value[max_return_ticker]['last'],volatility=volatilities[max_return_index % 3])
                if max_action == "BUY":
                    logger.info(f"Possible units by cash {current_value['CASH']['position']//current_value[max_return_ticker]['last']} -- by VaR {units_to_transact} -- 95% {int(units_to_transact*0.95)}")                    
                    units_to_transact = int(min(int(units_to_transact*0.95),current_value['CASH']['position']//current_value[max_return_ticker]['last']))
                else:
                    units_to_transact = int(units_to_transact * 0.95)
                
                logger.info(f"{units_to_transact} units to {max_action} of {max_return_ticker} at {current_value[max_return_ticker]['last']} with volatility {volatilities[max_return_index % 3]}")
                transaction_response = await batch_post_order(auth=auth,quantity=units_to_transact, ticker=max_return_ticker, action=max_action)
                logger.info(f"Transaction details {transaction_response}")
                # await batch_post_order(auth=auth,quantity=units_to_transact, ticker=max_return_ticker, action=square_off_action, order_type="LIMIT", price=analyst_expectation[max_return_ticker])
                        
            current_tick = await fetch_current_tick(auth=auth)
            current_value['tick'] = current_tick
            logger.info(f"Current tick is {current_tick}")
            current_value.update(await fetch_securities_position(auth))
            logger.info(f"Current values are: {current_value}")
            asset_fractions, total_value = calculate_fractions(current_value)            
            value_at_risk = calculate_var(volatilities=volatilities, correlation_matrix=correlation_matrix, portfolio_weights=np.array(asset_fractions), portfolio_value=total_value, confidence_level=0.99)
            logger.info(f"Value at risk is: {value_at_risk}")
            if value_at_risk >= 19500:
                await decide_square_off(auth=auth, current_position=current_value, analyst_expectation=analyst_expectation, quantity=100)
            await decide_square_off(auth=auth, current_position=current_value, analyst_expectation=analyst_expectation)
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"{e}, redo loop")
            await asyncio.sleep(0.2)