# 📈 Binance Futures Testnet Trading Bot

A clean, production-structured Python CLI application for placing orders on the **Binance Futures Testnet (USDT-M)**. Built with proper separation of concerns, structured logging, and robust input validation.

---

## ✨ Features

- ✅ Place **MARKET** and **LIMIT** orders on Binance Futures Testnet
- ✅ Support for both **BUY** and **SELL** sides
- ✅ **STOP_MARKET** orders (bonus order type)
- ✅ Full **CLI interface** via [Typer](https://typer.tiangolo.com/) with `--help` support
- ✅ **Rich terminal output** — coloured tables, panels, status indicators
- ✅ **Structured logging** to daily log files (`logs/trading_bot_YYYYMMDD.log`)
- ✅ Layered validation with helpful error messages
- ✅ Clean architecture: separate `client`, `orders`, `validators`, and `logging_config` modules
- ✅ View account **balance** and **open orders**

---

## 🗂️ Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package marker
│   ├── client.py            # Binance REST API client (signing, HTTP, error handling)
│   ├── orders.py            # Order placement logic + Rich output formatting
│   ├── validators.py        # All input validation rules
│   └── logging_config.py    # Logging setup (file + console handlers)
├── logs/
│   └── trading_bot_YYYYMMDD.log   # Auto-created daily log files
├── cli.py                   # CLI entry point (Typer commands)
├── .env.example             # Template for API credentials
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/trading_bot.git
cd trading_bot
```

### 2. Create & Activate a Virtual Environment

```bash
# Create
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — Mac / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Binance Testnet API Credentials

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Sign up / log in (GitHub login works)
3. Navigate to **API Key** in the top-right menu
4. Click **Generate** — copy both the **API Key** and **Secret Key**

### 5. Configure API Keys

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

Open `.env` in any text editor and replace the placeholder values:

```
BINANCE_API_KEY=paste_your_api_key_here
BINANCE_API_SECRET=paste_your_api_secret_here
```

> ⚠️ **Never commit `.env` to GitHub!** It is already listed in `.gitignore`.

---

## 🖥️ Usage

### Get Help

```bash
python cli.py --help
python cli.py place-order --help
```

---

### Place a MARKET Order

Buy 0.001 BTC at market price:

```bash
python cli.py place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

Sell 0.01 ETH at market price:

```bash
python cli.py place-order --symbol ETHUSDT --side SELL --type MARKET --quantity 0.01
```

---

### Place a LIMIT Order

Buy 0.001 BTC when price drops to $90,000:

```bash
python cli.py place-order --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 90000
```

Sell 0.01 ETH at $3,200:

```bash
python cli.py place-order --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3200
```

---

### Place a STOP_MARKET Order *(Bonus)*

Sell 0.001 BTC if price falls to $80,000 (stop-loss):

```bash
python cli.py place-order --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 80000
```

---

### Check Account Balance

```bash
python cli.py balance
```

---

### View Open Orders

```bash
python cli.py open-orders --symbol BTCUSDT
```

---

## 📋 Example Terminal Output

```
╭─────────────────────────────────────────────────────╮
│     📈 Binance Futures Testnet — Trading Bot        │
╰─────────────────────────────────────────────────────╯

╭─ 📋 Order Request Summary ─────────────────────────╮
│ Symbol      │ BTCUSDT                               │
│ Side        │ BUY                                   │
│ Order Type  │ MARKET                                │
│ Quantity    │ 0.001                                 │
╰─────────────────────────────────────────────────────╯

╭─ ✅ Order Response ────────────────────────────────╮
│ Order ID      │ 4961234567                         │
│ Symbol        │ BTCUSDT                            │
│ Side          │ BUY                                │
│ Type          │ MARKET                             │
│ Status        │ FILLED                             │
│ Quantity      │ 0.001                              │
│ Executed Qty  │ 0.001                              │
│ Avg Fill Price│ 97423.10                           │
╰─────────────────────────────────────────────────────╯

╭─────────────────────────────────────────────────────╮
│  ✓ Order placed successfully!                       │
│  Order ID: 4961234567  |  Status: FILLED            │
╰─────────────────────────────────────────────────────╯
```

---

## 📝 Logging

Logs are written automatically to `logs/trading_bot_YYYYMMDD.log`.

Every log entry includes:
- Timestamp
- Log level (DEBUG / INFO / WARNING / ERROR)
- Module name
- Message

**Example log entries:**

```
2025-05-01 10:12:03 | INFO     | trading_bot.cli    | CLI input validated | symbol=BTCUSDT side=BUY type=MARKET qty=0.001
2025-05-01 10:12:03 | INFO     | trading_bot.client | Placing order → POST https://testnet.binancefuture.com/fapi/v1/order
2025-05-01 10:12:04 | INFO     | trading_bot.client | Order placed successfully. Response: {'orderId': 4961234567, 'status': 'FILLED', ...}
2025-05-01 10:12:04 | INFO     | trading_bot.orders | Order success | OrderID=4961234567 | Status=FILLED
```

Sample log files are included in the `logs/` directory.

---

## ⚠️ Validation Rules

| Field | Rules |
|-------|-------|
| `symbol` | Must end with `USDT`, letters only (e.g., `BTCUSDT`) |
| `side` | Must be `BUY` or `SELL` (case-insensitive) |
| `type` | Must be `MARKET`, `LIMIT`, or `STOP_MARKET` |
| `quantity` | Must be a positive number |
| `price` | Required for `LIMIT`; must not be provided for `MARKET` |
| `stop-price` | Required for `STOP_MARKET` |

---

## 🔧 Assumptions

1. **Testnet only** — all orders go to `https://testnet.binancefuture.com`. No real funds are used.
2. **USDT-M Futures** — only USDT-margined pairs are supported (symbols must end in `USDT`).
3. **Time in force** — LIMIT orders use `GTC` (Good Till Cancelled) by default.
4. **Credentials via `.env`** — API keys are loaded from a `.env` file in the project root using `python-dotenv`.
5. **Quantity precision** — quantities are rounded to 3 decimal places. Some symbols require different precision; consult exchange info if an order is rejected.

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | 2.31.0 | HTTP REST calls to Binance API |
| `python-dotenv` | 1.0.1 | Load API keys from `.env` file |
| `typer` | 0.12.3 | CLI argument parsing |
| `rich` | 13.7.1 | Coloured terminal output and tables |

---

## 🔒 Security

- API keys are **never** hardcoded in source code
- API keys are loaded from a `.env` file which is excluded from git via `.gitignore`
- Request signatures use **HMAC-SHA256** as required by Binance
- The **secret key is never logged** — only sanitised params appear in log files

---

*Built for Binance Futures Testnet (USDT-M) — no real funds at risk.*
