"""
Input validation for trading bot CLI arguments.
All validation logic lives here — kept separate from business logic.
"""

from typing import Optional


class ValidationError(Exception):
    """Raised when user-supplied input fails validation."""
    pass


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalise a trading symbol.

    Rules:
    - Must be a non-empty string
    - Uppercased automatically
    - Must end with USDT (Futures USDT-M pairs)

    Args:
        symbol: Raw symbol string from user input

    Returns:
        Uppercased, validated symbol

    Raises:
        ValidationError: If symbol fails any rule
    """
    if not symbol or not symbol.strip():
        raise ValidationError("Symbol cannot be empty. Example: BTCUSDT")

    symbol = symbol.strip().upper()

    if not symbol.isalpha():
        raise ValidationError(
            f"Symbol '{symbol}' contains invalid characters. Use letters only (e.g., BTCUSDT)."
        )

    if not symbol.endswith("USDT"):
        raise ValidationError(
            f"Symbol '{symbol}' must end with USDT for Futures USDT-M (e.g., BTCUSDT, ETHUSDT)."
        )

    return symbol


def validate_side(side: str) -> str:
    """
    Validate order side (BUY or SELL).

    Args:
        side: Raw side string from user input

    Returns:
        Uppercased, validated side

    Raises:
        ValidationError: If side is not BUY or SELL
    """
    if not side or not side.strip():
        raise ValidationError("Side cannot be empty. Choose BUY or SELL.")

    side = side.strip().upper()

    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )

    return side


def validate_order_type(order_type: str) -> str:
    """
    Validate order type.

    Args:
        order_type: Raw order type string from user input

    Returns:
        Uppercased, validated order type

    Raises:
        ValidationError: If order type is not supported
    """
    if not order_type or not order_type.strip():
        raise ValidationError(
            f"Order type cannot be empty. Choose from: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )

    order_type = order_type.strip().upper()

    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. "
            f"Supported types: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )

    return order_type


def validate_quantity(quantity: float) -> float:
    """
    Validate order quantity.

    Rules:
    - Must be a positive number
    - Maximum 6 decimal places (Binance precision limit)

    Args:
        quantity: Order quantity

    Returns:
        Validated quantity

    Raises:
        ValidationError: If quantity is invalid
    """
    if quantity is None:
        raise ValidationError("Quantity is required.")

    if quantity <= 0:
        raise ValidationError(
            f"Quantity must be greater than 0. Got: {quantity}."
        )

    # Round to 3 decimal places (safe for most Futures pairs)
    quantity = round(quantity, 3)

    return quantity


def validate_price(price: Optional[float], order_type: str) -> Optional[float]:
    """
    Validate order price based on order type.

    Rules:
    - MARKET orders: price must be None (not required)
    - LIMIT / STOP_MARKET orders: price must be a positive number

    Args:
        price: Order price (can be None for MARKET)
        order_type: Already-validated order type string

    Returns:
        Validated price (or None for MARKET)

    Raises:
        ValidationError: If price rules are violated
    """
    if order_type == "MARKET":
        if price is not None:
            raise ValidationError(
                "Price should NOT be provided for MARKET orders — "
                "the exchange fills at the best available price."
            )
        return None

    # LIMIT and STOP_MARKET require a price
    if price is None:
        raise ValidationError(
            f"Price is required for {order_type} orders. Use --price <value>."
        )

    if price <= 0:
        raise ValidationError(
            f"Price must be greater than 0. Got: {price}."
        )

    price = round(price, 2)
    return price


def validate_stop_price(stop_price: Optional[float], order_type: str) -> Optional[float]:
    """
    Validate stop price for STOP_MARKET orders.

    Args:
        stop_price: Stop trigger price
        order_type: Already-validated order type string

    Returns:
        Validated stop price or None

    Raises:
        ValidationError: If stop price rules are violated
    """
    if order_type != "STOP_MARKET":
        return None

    if stop_price is None:
        raise ValidationError(
            "Stop price (--stop-price) is required for STOP_MARKET orders."
        )

    if stop_price <= 0:
        raise ValidationError(
            f"Stop price must be greater than 0. Got: {stop_price}."
        )

    return round(stop_price, 2)
