"""
CLI entry point for the Binance Futures Testnet Trading Bot.
Uses Typer for clean argument parsing and Rich for formatted output.

Usage examples:
python cli.py place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
python cli.py place-order --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3000
python cli.py place-order --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 80000
python cli.py balance
python cli.py open-orders --symbol BTCUSDT
"""

import os
from typing import Optional

import typer
from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bot.client import BinanceAPIError, BinanceClient
from bot.logging_config import setup_logger
from bot.orders import place_order
from bot.validators import (
    ValidationError,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

load_dotenv()

app = typer.Typer(
    name="trading-bot",
    help="📈 Binance Futures Testnet Trading Bot — place orders from the command line.",
    add_completion=False,
)

console = Console()
logger = setup_logger("trading_bot.cli")


def _get_client() -> BinanceClient:
    """Build a BinanceClient from environment variables."""
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        console.print(
            Panel(
                "[bold red]Missing API credentials![/bold red]\n\n"
                "Create a [cyan].env[/cyan] file in the project root with:\n\n"
                "[yellow]BINANCE_API_KEY=your_key_here[/yellow]\n"
                "[yellow]BINANCE_API_SECRET=your_secret_here[/yellow]\n\n"
                "Get keys from: [link=https://testnet.binancefuture.com]https://testnet.binancefuture.com[/link]",
                style="red",
                title="Configuration Error",
            )
        )
        raise typer.Exit(code=1)

    return BinanceClient(api_key=api_key, api_secret=api_secret)


@app.command("place-order")
def cmd_place_order(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair, e.g. BTCUSDT"),
    side: str = typer.Option(..., "--side", help="BUY or SELL"),
    order_type: str = typer.Option(..., "--type", "-t", help="MARKET, LIMIT, or STOP_MARKET"),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Amount of base asset to trade"),
    price: Optional[float] = typer.Option(None, "--price", "-p", help="Limit price (required for LIMIT orders)"),
    stop_price: Optional[float] = typer.Option(None, "--stop-price", help="Stop trigger price (for STOP_MARKET)"),
) -> None:
    """Place a MARKET, LIMIT, or STOP_MARKET order on Binance Futures Testnet."""
    console.print(
        Panel(
            "[bold blue]📈 Binance Futures Testnet — Trading Bot[/bold blue]",
            style="blue",
        )
    )

    try:
        symbol = validate_symbol(symbol)
        side = validate_side(side)
        order_type = validate_order_type(order_type)
        quantity = validate_quantity(quantity)
        price = validate_price(price, order_type)
        stop_price = validate_stop_price(stop_price, order_type)
    except ValidationError as exc:
        logger.warning(f"Validation failed: {exc}")
        console.print(f"\n[bold red]❌ Validation Error:[/bold red] {exc}\n")
        raise typer.Exit(code=1)

    logger.info(
        f"CLI input validated | symbol={symbol} side={side} type={order_type} "
        f"qty={quantity} price={price} stop_price={stop_price}"
    )

    client = _get_client()
    result = place_order(
        client=client,
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )

    if result is None:
        raise typer.Exit(code=1)


@app.command("balance")
def cmd_balance() -> None:
    """Show your Binance Futures Testnet account balance."""
    console.print(Panel("[bold blue]💰 Account Balance[/bold blue]", style="blue"))

    client = _get_client()

    try:
        balances = client.get_account_balance()
        table = Table(title="Account Balances", box=box.ROUNDED)
        table.add_column("Asset", style="cyan")
        table.add_column("Wallet Balance", style="white")
        table.add_column("Unrealised PnL", style="white")
        table.add_column("Available Balance", style="green")

        rows_added = 0
        for b in balances:
            wallet = float(b.get("balance", 0))
            unrealised = float(b.get("crossUnPnl", 0))
            available = float(b.get("availableBalance", 0))
            if wallet > 0 or available > 0:
                table.add_row(
                    b.get("asset", ""),
                    f"{wallet:,.4f}",
                    f"{unrealised:,.4f}",
                    f"{available:,.4f}",
                )
                rows_added += 1

        if rows_added == 0:
            console.print("[yellow]No non-zero balances found.[/yellow]")
            return

        console.print(table)
    except BinanceAPIError as exc:
        logger.error(f"Failed to fetch balance: {exc}")
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(code=1)


@app.command("open-orders")
def cmd_open_orders(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair, e.g. BTCUSDT"),
) -> None:
    """List all open orders for a symbol."""
    try:
        symbol = validate_symbol(symbol)
    except ValidationError as exc:
        console.print(f"[red]Validation Error: {exc}[/red]")
        raise typer.Exit(code=1)

    console.print(Panel(f"[bold blue]📂 Open Orders — {symbol}[/bold blue]", style="blue"))

    client = _get_client()

    try:
        orders = client.get_open_orders(symbol)
        if not orders:
            console.print(f"[yellow]No open orders found for {symbol}.[/yellow]")
            return

        table = Table(title=f"Open Orders: {symbol}", box=box.ROUNDED)
        table.add_column("Order ID", style="cyan")
        table.add_column("Side", style="white")
        table.add_column("Type", style="white")
        table.add_column("Qty", style="white")
        table.add_column("Price", style="white")
        table.add_column("Status", style="white")

        for o in orders:
            side_value = o.get("side", "")
            side_str = f"[green]{side_value}[/green]" if side_value == "BUY" else f"[red]{side_value}[/red]"
            table.add_row(
                str(o.get("orderId", "")),
                side_str,
                str(o.get("type", "")),
                str(o.get("origQty", "")),
                str(o.get("price", "")),
                str(o.get("status", "")),
            )

        console.print(table)
    except BinanceAPIError as exc:
        logger.error(f"Failed to fetch open orders: {exc}")
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
