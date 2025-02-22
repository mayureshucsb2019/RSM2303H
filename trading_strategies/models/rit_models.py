from typing import Optional

from pydantic import BaseModel, conint, constr


class Error(BaseModel):
    """Model representing an error with a code and message."""

    code: str
    message: str


class TickerQuantity(BaseModel):
    """Model representing a ticker and its quantity."""

    ticker: constr(min_length=1, max_length=10)  # Example: CL
    quantity: conint(ge=0)  # Example: 10


class TickerPrice(BaseModel):
    """Model representing a ticker and its price."""

    ticker: constr(min_length=1, max_length=10)  # Example: CL
    price: float  # Example: 9.99


class Order(BaseModel):
    """Model representing an order with various attributes."""

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
    """Model representing an asset lease with various attributes."""

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
    """Model representing a success result with a description."""

    success: bool  # Example: true
    description: Optional[
        str
    ]  # Placeholder result to indicate an operation was successful.


# Additional Enums for readability
class CaseStatus(str):
    """Enum representing the status of a case."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


class OrderType(str):
    """Enum representing the type of an order."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"


class SecurityType(str):
    """Enum representing the type of a security."""

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
    """Enum representing the type of an asset."""

    CONTAINER = "CONTAINER"
    PIPELINE = "PIPELINE"
    SHIP = "SHIP"
    REFINERY = "REFINERY"
    POWER_PLANT = "POWER_PLANT"
    PRODUCER = "PRODUCER"


class OrderAction(str):
    """Enum representing the action of an order."""

    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str):
    """Enum representing the status of an order."""

    OPEN = "OPEN"
    TRANSACTED = "TRANSACTED"
    CANCELLED = "CANCELLED"
