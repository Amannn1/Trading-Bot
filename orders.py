"""
Order placement logic for the trading bot.
Acts as the service layer between the CLI and the raw API client.
Formats, prints, and returns structured order results.
"""

from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from bot.client import BinanceClient, BinanceAPIError
from bot.logging_config import setup_logger

logger = setup_logger("trading_bot.orders")
console = Console()


def _build_summary_table(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
    stop_price: Optional[float],
) -> Table:
    """Build a Rich table summarising the order request before sending."""
    table = Table(title="📋 Order Request Summary", box=box.ROUNDED, show_header=False)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value", style="white")

    table.add_row("Symbol", symbol)
    table.add_row("Side", f"[green]BUY[/green]" if side == "BUY" else f"[red]SELL[/red]")
    table.add_row("Order Type", order_type)
    table.add_row("Quantity", str(quantity))

    if price is not None:
        table.add_row("Limit Price", f"${price:,.2f}")
    if stop_price is not None:
        table.add_row("Stop Price", f"${stop_price:,.2f}")

    return table


def _build_response_table(response: Dict[str, Any]) -> Table:
    """Build a Rich table showing the Binance order response fields."""
    table = Table(title="✅ Order Response", box=box.ROUNDED, show_header=False)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value", style="white")

    fields = [
        ("Order ID", "orderId"),
        ("Client Order ID", "clientOrderId"),
        ("Symbol", "symbol"),
        ("Side", "side"),
        ("Type", "type"),
        ("Status", "status"),
        ("Quantity", "origQty"),
        ("Executed Qty", "executedQty"),
        ("Avg Fill Price", "avgPrice"),
        ("Price", "price"),
        ("Stop Price", "stopPrice"),
        ("Time In Force", "timeInForce"),
    ]

    for label, key in fields:
        value = response.get(key)
        if value is not None and value != "" and value != "0" and value != "0.00000000":
            # Highlight status with colour
            if key == "status":
                if value in ("FILLED", "NEW"):
                    value = f"[green]{value}[/green]"
                elif value in ("CANCELED", "REJECTED", "EXPIRED"):
                    value = f"[red]{value}[/red]"
                else:
                    value = f"[yellow]{value}[/yellow]"
            table.add_row(label, str(value))

    return table


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """
    Orchestrate order placement: print summary → call API → print result.

    Args:
        client: Authenticated BinanceClient instance
        symbol: Trading pair (e.g., BTCUSDT)
        side: BUY or SELL
        order_type: MARKET, LIMIT, or STOP_MARKET
        quantity: Amount of base asset
        price: Limit price (LIMIT orders only)
        stop_price: Trigger price (STOP_MARKET orders only)

    Returns:
        Order response dict on success, None on failure
    """
    # Print request summary to console
    summary_table = _build_summary_table(symbol, side, order_type, quantity, price, stop_price)
    console.print(summary_table)
    console.print()

    logger.info(
        f"Initiating {order_type} {side} order | "
        f"Symbol={symbol} | Qty={quantity} | Price={price} | StopPrice={stop_price}"
    )

    try:
        response = client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )

        # Print response table
        response_table = _build_response_table(response)
        console.print(response_table)
        console.print()

        # Success banner
        order_id = response.get("orderId", "N/A")
        status = response.get("status", "N/A")
        console.print(
            Panel(
                f"[bold green]✓ Order placed successfully![/bold green]\n"
                f"Order ID: [cyan]{order_id}[/cyan]  |  Status: [cyan]{status}[/cyan]",
                style="green",
            )
        )

        logger.info(f"Order success | OrderID={order_id} | Status={status}")
        return response

    except BinanceAPIError as exc:
        logger.error(f"Binance API error during order placement: code={exc.code} msg={exc.message}")
        console.print(
            Panel(
                f"[bold red]✗ Order failed — Binance API Error[/bold red]\n"
                f"Code: [yellow]{exc.code}[/yellow]\n"
                f"Message: {exc.message}",
                style="red",
            )
        )
        return None

    except Exception as exc:
        logger.error(f"Unexpected error during order placement: {exc}", exc_info=True)
        console.print(
            Panel(
                f"[bold red]✗ Unexpected error[/bold red]\n{exc}",
                style="red",
            )
        )
        return None
