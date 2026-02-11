# Ninja API Forge (Injective Spot API Gateway)

This is a lightweight backend service built with **FastAPI**. It wraps Injective upstream endpoints (LCD + Indexer) into a more consistent and developer-friendly REST API.

You can think of it as a gateway/adapter layer:

**Injective upstream data → normalize/clean → serve as stable APIs for other developers**

---

## What you can do with it

- ✅ Check whether the service itself is running (service health)
- ✅ Check whether Injective upstream is reachable (upstream health + latest block height)
- ✅ Fetch Injective spot market list (cleaned fields)
- ✅ Fetch an orderbook depth snapshot for a given market (unified `bids/asks` + `depth`)

> Note: This project does **not** include a frontend and does **not** include smart contracts. It only provides developer-friendly backend APIs.

---

## Upstreams

This service depends on two public endpoints:

- **Injective LCD (on-chain base data)**
  - `https://sentry.lcd.injective.network:443`
  - Purpose: query latest block height (used by upstream health)

- **Injective Indexer / Exchange API (trading & orderbook data)**
  - `https://sentry.exchange.grpc-web.injective.network`
  - Purpose: market list and orderbook snapshots (core data source)

---

## Requirements

- Python 3.10+ (recommended)
- Dependencies:
  - fastapi
  - uvicorn
  - httpx

---

## Install & Run

### 1) Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Start the service (development mode)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

After startup, you can open:

- Swagger Docs: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

---

## API Reference

**Convention:** if the upstream is unavailable, times out, or returns non-2xx responses, this service will return **502 Bad Gateway**, meaning “failed to fetch from upstream”.

---

### 1) `GET /health` — Service health check

**Purpose**  
Confirms that the FastAPI service process is running (does not call upstream).

**Request example**
```bash
curl http://127.0.0.1:8000/health
```

**Response example**
```json
{ "ok": true }
```

---

### 2) `GET /upstream/health` — Upstream health check (LCD)

**Purpose**  
Confirms that Injective LCD is reachable, and returns `latest_height`.  
Useful to quickly tell whether the problem is your local service or the upstream/network.

**Request example**
```bash
curl http://127.0.0.1:8000/upstream/health
```

**Response example**
```json
{
  "upstream": "injective_lcd",
  "ok": true,
  "latest_height": "12345678"
}
```

**Errors**
- `502`: LCD upstream is unavailable / timeout / JSON parse error, etc.

---

### 3) `GET /spot/markets` — Spot market list (cleaned output)

**Purpose**  
Fetches the Injective spot market list and cleans the upstream fields into a more usable structure.  
Typically you will use this endpoint to get a `market_id`, then use that `market_id` to query the orderbook via `/orderbook`.

**Query params**
- `limit` — number of markets to return  
  - Type: int  
  - Default: 20  
  - Range: 1 ~ 200  

**Request example**
```bash
curl "http://127.0.0.1:8000/spot/markets?limit=5"
```

**Response fields**
- `source`: data source (this endpoint uses the indexer)
- `count`: number of markets returned
- `items`: market list; each item includes:
  - `market_id`: unique market ID (required for querying `/orderbook`)
  - `ticker`: human-readable pair name (e.g. `INJ/USDT`)
  - `status`: market status (whether tradable)
  - `base_denom`: base asset denom (the asset you receive)
  - `quote_denom`: quote asset denom (the asset you pay with)
  - `min_price_tick_size`: minimum price tick size (min quote step)
  - `min_quantity_tick_size`: minimum quantity tick size (min size step)

**Response example (shape)**
```json
{
  "source": "injective_indexer",
  "count": 2,
  "items": [
    {
      "market_id": "xxx",
      "ticker": "INJ/USDT",
      "status": "active",
      "base_denom": "inj",
      "quote_denom": "uusdt",
      "min_price_tick_size": "0.0001",
      "min_quantity_tick_size": "0.01"
    }
  ]
}
```

**Errors**
- `422`: `limit` out of range or invalid type
- `502`: indexer upstream is unavailable / timeout / non-2xx response, etc.

---

### 4) `GET /orderbook` — Orderbook depth snapshot (core endpoint)

**Purpose**  
Fetches an orderbook snapshot for a spot market and unifies the upstream structure as:

- `bids`: bid side levels (buy orders)
- `asks`: ask side levels (sell orders)

Supports `depth` to control how many levels to return.

**Query params**
- `market_id` (required): spot market ID  
  - Source: from `/spot/markets` response
- `depth`: number of levels to return for both `bids` and `asks`  
  - Type: int  
  - Default: 20  
  - Range: 1 ~ 200  

**Two-step example**

1) Get a `market_id` first:
```bash
curl "http://127.0.0.1:8000/spot/markets?limit=20"
```

From the response, pick one `market_id`, for example:
```text
0x0511ddc4e6586f3bfe1acb2dd905f8b8a82c97e1edaef654b12ca7e6031ca0fa
```

2) Query orderbook by `market_id`:
```bash
curl "http://127.0.0.1:8000/orderbook?market_id=0x0511ddc4e6586f3bfe1acb2dd905f8b8a82c97e1edaef654b12ca7e6031ca0fa&depth=20"
```

**Response fields**
- `source`: data source (indexer)
- `market_id`: echoes the requested market_id
- `depth`: how many levels returned
- `bids`: bid levels (by price levels)
- `asks`: ask levels (by price levels)
- Each level contains:
  - `price`: price (string to avoid float precision loss)
  - `quantity`: quantity (string to avoid float precision loss)
  - `timestamp`: level timestamp (provided by upstream)
- `meta`: snapshot metadata
  - `sequence`: sequence number (useful for update order / dedup)
  - `timestamp`: snapshot timestamp
  - `height`: chain height (if provided by upstream)

**Response example (shape)**
```json
{
  "source": "injective_indexer",
  "market_id": "xxx",
  "depth": 20,
  "bids": [
    { "price": "12.34", "quantity": "5.67", "timestamp": 1700000000 }
  ],
  "asks": [
    { "price": "12.35", "quantity": "1.23", "timestamp": 1700000000 }
  ],
  "meta": {
    "sequence": "123",
    "timestamp": 1700000000,
    "height": "12345678"
  }
}
```

**Errors**
- `422`: missing `market_id` or `depth` out of range
- `502`: indexer upstream is unavailable / timeout / non-2xx response, etc.

---

## Design Notes

- This project is a **gateway/adapter layer**: it normalizes upstream field names and output structure to reduce integration effort.
- `price` / `quantity` are returned as **strings** to avoid decimal precision issues.
- `limit` / `depth` have max caps to protect the service and upstream, and prevent abuse.

