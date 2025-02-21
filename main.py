import asyncio

import trading_strategies.rit_apis as rit
from trading_strategies.utility import get_auth_config


async def main():
    print(await rit.get_case_status(get_auth_config()))


if __name__ == "__main__":
    asyncio.run(main())
