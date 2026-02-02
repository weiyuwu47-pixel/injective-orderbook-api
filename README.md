# Ninja Orderbook Snapshot API (Injective)

A lightweight developer API built for **Ninja API Forge**.  
It provides:
- **Spot markets list** (cleaned output)
- **Spot orderbook snapshot** (normalized to `bids/asks`, with `depth`)

No frontend, no smart contracts — just a backend API that other developers can plug into.

## Data Sources (Injective)
- Injective **Indexer (gRPC-Web public endpoint)**: `https://sentry.exchange.grpc-web.injective.network`
- Injective **LCD (public endpoint)**: `https://sentry.lcd.injective.network:443`

## Endpoints

### 1) Health
`GET /health`

### 2) Spot markets (cleaned)
`GET /spot/markets?limit=20`

Example:
```bash
curl "http://127.0.0.1:8000/spot/markets?limit=3"

cat > README.md << 'EOF'
# Ninja Orderbook Snapshot API (Injective)

A lightweight developer API built for **Ninja API Forge**.  
It provides:
- **Spot markets list** (cleaned output)
- **Spot orderbook snapshot** (normalized to `bids/asks`, with `depth`)

No frontend, no smart contracts — just a backend API that other developers can plug into.

## Data Sources (Injective)
- Injective **Indexer (gRPC-Web public endpoint)**: `https://sentry.exchange.grpc-web.injective.network`
- Injective **LCD (public endpoint)**: `https://sentry.lcd.injective.network:443`

## Endpoints

### 1) Health
`GET /health`

### 2) Spot markets (cleaned)
`GET /spot/markets?limit=20`

Example:
```bash
curl "http://127.0.0.1:8000/spot/markets?limit=3"
