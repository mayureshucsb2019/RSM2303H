from typing import Optional

from pydantic import BaseModel, conint, constr


class Error(BaseModel):
    code: str
    message: str


class TickerQuantity(BaseModel):
    ticker: constr(min_length=1, max_length=10)  # Example: CL
    quantity: conint(ge=0)  # Example: 10


class TickerPrice(BaseModel):
    ticker: constr(min_length=1, max_length=10)  # Example: CL
    price: float  # Example: 9.99


class Order(BaseModel):
    order_id: conint(ge=0)  # Example: 1221
    period: conint(ge=0)  # Example: 1
    tick: conint(ge=0)  # Example: 10
    trader_id: constr(min_length=1)  # Example: trader49
    ticker: constr(min_length=1)  # Example: CRZY
    type: constr(regex="^(MARKET|LIMIT)$")  # Enum: [ MARKET, LIMIT ]
    quantity: conint(ge=0)  # Example: 100
    action: constr(regex="^(BUY|SELL)$")  # Enum: [ BUY, SELL ]
    price: Optional[float]  # Example: 14.21, Will be null if type is LIMIT
    quantity_filled: conint(ge=0)  # Example: 10
    vwap: Optional[float]  # Example: 14.21, null if quantity_filled is 0
    status: constr(
        regex="^(OPEN|TRANSACTED|CANCELLED)$"
    )  # Enum: [ OPEN, TRANSACTED, CANCELLED ]


class AssetLease(BaseModel):
    id: conint(ge=0)  # Lease id.
    ticker: constr(min_length=1)  # Example: CL
    type: constr(
        regex="^(CONTAINER|PIPELINE|SHIP|REFINERY|POWER_PLANT|PRODUCER)$"
    )  # Example: CONTAINER
    start_lease_period: conint(ge=0)
    start_lease_tick: conint(ge=0)
    next_lease_period: conint(ge=0)
    next_lease_tick: conint(ge=0)
    containment_usage: conint(
        ge=0
    )  # Currently utilized capacity for CONTAINER type assets.


class SuccessResult(BaseModel):
    success: bool  # Example: true
    description: Optional[
        str
    ]  # Placeholder result to indicate an operation was successful.


# Additional Enums for readability
class CaseStatus(str):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


class OrderType(str):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class SecurityType(str):
    SPOT = "SPOT"
    FUTURE = "FUTURE"
    INDEX = "INDEX"
    OPTION = "OPTION"
    STOCK = "STOCK"
    CURRENCY = "CURRENCY"
    BOND = "BOND"
    RATE = "RATE"
    FORWARD = "FORWARD"
    SWAP = "SWAP"
    SWAP_BOM = "SWAP_BOM"
    SPRE = "SPRE"


class AssetType(str):
    CONTAINER = "CONTAINER"
    PIPELINE = "PIPELINE"
    SHIP = "SHIP"
    REFINERY = "REFINERY"
    POWER_PLANT = "POWER_PLANT"
    PRODUCER = "PRODUCER"


class OrderAction(str):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str):
    OPEN = "OPEN"
    TRANSACTED = "TRANSACTED"
    CANCELLED = "CANCELLED"
