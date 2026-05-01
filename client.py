"""
Binance Futures Testnet REST API client.
Handles authentication (HMAC-SHA256 signing), request building, and HTTP communication.
All raw API interaction is isolated here — no business logic.
"""

import hashlib
import hmac
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from bot.logging_config import setup_logger

# Binance Futures Testnet base URL
BASE_URL = "https://testnet.binancefuture.com"

logger = setup_logger("trading_bot.client")


class BinanceAPIError(Exception):
    """
    Raised when the Binance API returns an error response.

    Attributes:
        code: Binance error code (negative int)
        message: Human-readable error description
    """

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error {code}: {message}")


class BinanceClient:
    """
    Lightweight wrapper around the Binance Futures Testnet REST API.

    Responsibilities:
    - Sign requests with HMAC-SHA256
    - Attach correct headers (X-MBX-APIKEY)
    - Handle HTTP errors and Binance-specific error responses
    - Log every outgoing request and incoming response
    """

    def __init__(self, api_key: str, api_secret: str):
        """
        Initialise the client with API credentials.

        Args:
            api_key: Binance Testnet API key
            api_secret: Binance Testnet API secret
        """
        if not api_key or not api_secret:
            raise ValueError("API key and secret must not be empty.")

        self._api_key = api_key
        self._api_secret = api_secret
        self._session = requests.Session()
        self._session.headers.update({
            "X-MBX-APIKEY": self._api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })
        logger.debug("BinanceClient initialised (testnet)")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _timestamp(self) -> int:
        """Return current UTC timestamp in milliseconds."""
        return int(time.time() * 1000)

    def _sign(self, params: Dict[str, Any]) -> str:
        """
        Generate HMAC-SHA256 signature for request parameters.

        Args:
            params: Query/body parameters dict (must include timestamp)

        Returns:
            Hex-encoded signature string
        """
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Parse and validate an HTTP response from Binance.

        Args:
            response: Raw requests Response object

        Returns:
            Parsed JSON body as a dict

        Raises:
            BinanceAPIError: If Binance returns a business-logic error
            requests.HTTPError: If the HTTP status is 4xx/5xx
        """
        logger.debug(f"HTTP {response.status_code} ← {response.url}")
        logger.debug(f"Response body: {response.text}")

        # Raise on HTTP-level errors (500, 401, etc.)
        response.raise_for_status()

        data = response.json()

        # Binance wraps business errors as JSON with a negative "code" field
        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            raise BinanceAPIError(code=data["code"], message=data.get("msg", "Unknown error"))

        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_server_time(self) -> int:
        """
        Fetch Binance server time (useful for clock sync debugging).

        Returns:
            Server time in milliseconds
        """
        url = f"{BASE_URL}/fapi/v1/time"
        logger.debug(f"GET {url}")
        resp = self._session.get(url, timeout=10)
        data = self._handle_response(resp)
        return data["serverTime"]

    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Fetch exchange info (trading rules, symbol specs, etc.).

        Returns:
            Full exchange info dict
        """
        url = f"{BASE_URL}/fapi/v1/exchangeInfo"
        logger.debug(f"GET {url}")
        resp = self._session.get(url, timeout=15)
        return self._handle_response(resp)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """
        Place a new order on Binance Futures Testnet.

        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            side: BUY or SELL
            order_type: MARKET, LIMIT, or STOP_MARKET
            quantity: Amount of base asset to trade
            price: Limit price (required for LIMIT orders)
            stop_price: Trigger price (required for STOP_MARKET)
            time_in_force: GTC (Good Till Cancel) for LIMIT orders

        Returns:
            Binance order response dict

        Raises:
            BinanceAPIError: On API-level errors
            requests.RequestException: On network failures
        """
        url = f"{BASE_URL}/fapi/v1/order"

        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "timestamp": self._timestamp(),
        }

        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force

        if order_type == "STOP_MARKET":
            params["stopPrice"] = stop_price

        # Sign the request
        params["signature"] = self._sign(params)

        # Log the outgoing request (mask secret in logs)
        log_params = {k: v for k, v in params.items() if k != "signature"}
        logger.info(f"Placing order → POST {url}")
        logger.info(f"Order params: {log_params}")

        try:
            resp = self._session.post(url, data=params, timeout=15)
            result = self._handle_response(resp)
            logger.info(f"Order placed successfully. Response: {result}")
            return result

        except BinanceAPIError:
            raise  # Already logged in _handle_response

        except requests.exceptions.ConnectionError as exc:
            logger.error(f"Network connection failed: {exc}")
            raise

        except requests.exceptions.Timeout as exc:
            logger.error(f"Request timed out: {exc}")
            raise

        except requests.exceptions.RequestException as exc:
            logger.error(f"Unexpected request error: {exc}")
            raise

    def get_open_orders(self, symbol: str) -> list:
        """
        Fetch all open orders for a symbol.

        Args:
            symbol: Trading pair (e.g., BTCUSDT)

        Returns:
            List of open order dicts
        """
        url = f"{BASE_URL}/fapi/v1/openOrders"
        params = {
            "symbol": symbol,
            "timestamp": self._timestamp(),
        }
        params["signature"] = self._sign(params)

        logger.debug(f"GET {url} — open orders for {symbol}")
        resp = self._session.get(url, params=params, timeout=10)
        return self._handle_response(resp)

    def get_account_balance(self) -> list:
        """
        Fetch futures account balance.

        Returns:
            List of asset balance dicts
        """
        url = f"{BASE_URL}/fapi/v2/balance"
        params = {"timestamp": self._timestamp()}
        params["signature"] = self._sign(params)

        logger.debug(f"GET {url} — account balance")
        resp = self._session.get(url, params=params, timeout=10)
        return self._handle_response(resp)
