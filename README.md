# Kaspa Market Maker Bot

High-performance **Kaspa market making bot** for centralized exchanges like MEXC, Gate.io, KuCoin, and BingX.  
It keeps tight **KAS/USDT quotes around the mid-price**, manages inventory, and respects exchange rate limits to safely capture spread and provide liquidity.

## Why a Kaspa Market Making Bot?
- **Kaspa is UTXO-based** and has no on-chain orderbook – real market making happens on CEXs.
- This bot uses **CEX APIs + websockets/REST** to place and manage limit orders, while you hold KAS in your exchange account or external wallet.
- Designed for **low-latency quoting**, **inventory control**, and **robust cancel/replace loops**.

## Core Features
- **Orderbook tracking**: Continuously pulls top-of-book using ccxt (websocket-ready architecture).
- **Spread calculation**: Quotes around mid-price with configurable spread in basis points.
- **Auto quoting**: Automatically sends and refreshes two-sided KAS/USDT limit orders.
- **Inventory management**: Keeps your KAS/USDT ratio near a target and avoids over-exposure.
- **Cancel/replace loop**: Cancels stale orders and replaces them with fresh quotes.
- **Rate-limit friendly**: Token-bucket rate limiter to stay within exchange API rules.
- **Metrics and logging**: Prometheus metrics + structured JSON logs for monitoring.

## Architecture Overview
```
┌────────────────┐      ┌────────────────┐      ┌────────────────────┐
│  Orderbook     │ ---> │  Quote Engine  │ ---> │  CEX Limit Orders  │
└────────────────┘      └────────────────┘      └────────────────────┘
          ▲                       │                       │
          │                       v                       │
          │        ┌────────────────────────┐             │
          │        │ Inventory & Risk Logic │ <───────────┘
          │        └────────────────────────┘
          │                    │
          v                    v
   Prometheus Metrics    Structured Logging
```

### Key Modules
- `src/config.py` – Pydantic settings for spread, size, symbol, and exchange keys.
- `src/exchanges/cex_client.py` – ccxt-based wrapper for orderbook, balances, and orders.
- `src/core/quote_engine.py` – Mid-price based quote engine with spread and skew.
- `src/core/market_maker.py` – Main market making loop (orderbook → quotes → cancel/replace).
- `src/risk/inventory.py` – Inventory-based skew factor to avoid overbuying KAS.
- `src/risk/rate_limiter.py` – Async token-bucket for API rate limiting.
- `src/services/metrics.py` – Prometheus gauges/counters for price, spread, inventory, orders.
- `src/main.py` – Async entrypoint wiring everything together.

## Getting Started

### 1. Requirements
- Python **3.11+**
- A **CEX account** with KAS markets (e.g. MEXC, Gate.io, KuCoin, BingX)
- API key/secret with trading enabled and **IP allowlist** configured

### 2. Clone & Install
```bash
git clone https://github.com/your-org/kaspa-market-maker-bot.git
cd kaspa-market-maker-bot
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment
Create a `.env` file in the project root:
```env
ENVIRONMENT=development

SYMBOL=KAS/USDT
BASE_ASSET=KAS
QUOTE_ASSET=USDT

SPREAD_BPS=8.0
ORDER_SIZE=200.0
INVENTORY_TARGET_PCT=0.5
MAX_INVENTORY_PCT=0.8

EXCHANGE__NAME=mexc        # e.g. mexc, gate, kucoin
EXCHANGE__API_KEY=your_api_key
EXCHANGE__SECRET_KEY=your_secret_key
EXCHANGE__PASSWORD=your_passphrase_if_needed
EXCHANGE__TESTNET=false

METRICS_HOST=0.0.0.0
METRICS_PORT=9301
LOG_LEVEL=INFO
```

> **Security tip:** Never commit real API keys. For production, load secrets from Vault / AWS Secrets Manager or similar.

### 4. Run the Bot
```bash
python -m src.main
```

The bot will:
- Fetch orderbook for `KAS/USDT`
- Compute mid-price and two-sided quotes
- Cancel existing MM orders
- Place fresh buy/sell limits every loop iteration

Prometheus metrics will be available at:
- `http://localhost:9301/metrics`

## Market Making Logic

- **Mid-price**: \((best\_bid + best\_ask)/2\)
- **Spread-based quotes**:
  - `bid_price = mid - (spread / 2)`
  - `ask_price = mid + (spread / 2)`
- **Inventory-based skew**:
  - If you hold *too much* KAS → widen bids / favor sells.
  - If you hold *too little* KAS → tighten bids / favor buys.
- **Cancel/replace**:
  - Before each quote cycle, the bot cancels open MM orders on the symbol.
  - It then posts new bid/ask orders at updated prices.

This design keeps quotes fresh and close to the live market while protecting your inventory profile.

## SEO: Use Cases & Keywords

This repository is ideal if you are searching for:
- **Kaspa market maker bot**
- **KAS/USDT liquidity bot**
- **Kaspa algorithmic trading on CEX**
- **Crypto market making engine for Kaspa**
- **CCXT-based Kaspa trading bot**

You can adapt the strategy to:
- KAS/BTC or other KAS pairs
- Multiple exchanges (run one bot instance per venue)
- Different spreads and order sizes per profile (aggressive vs passive MM)

## Safety & Risk Management

- Use **small size and sandbox/testnet** while validating the strategy.
- Enforce **IP allowlists** and withdrawal whitelists on your exchange accounts.
- Monitor metrics and logs for unexpected behavior (e.g. no fills, API errors).
- Start with conservative spreads and small inventory caps before scaling.

## Development & Linting
```bash
ruff check src
black src
pytest
```

## Roadmap Ideas
- Add native **websocket orderbook** streaming per-exchange.
- Support **dynamic spreads** based on realized volatility and volume.
- Add **position-based kill-switches** and PnL dashboards.
- Integrate with a **Kaspa wallet** for periodic settlement off-exchange.

## License
Use at your own risk. Trading and market making involve substantial financial risk and may not be suitable for all users. Adjust licensing and compliance to your jurisdictional requirements.