from fastapi import FastAPI, Query, HTTPException
import httpx

app = FastAPI(title="Ninja API Forge - Injective Spot APIs")

# 链上基础数据（你已经跑通）
INJ_LCD = "https://sentry.lcd.injective.network:443"

# 交易/订单簿数据：Injective Indexer（你刚验证 spot/v1/markets 可用）
INJ_INDEXER = "https://sentry.exchange.grpc-web.injective.network"


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/upstream/health")
async def upstream_health():
    url = f"{INJ_LCD}/cosmos/base/tendermint/v1beta1/blocks/latest"
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
        height = data.get("block", {}).get("header", {}).get("height")
        return {"upstream": "injective_lcd", "ok": True, "latest_height": height}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"upstream error: {e}")


@app.get("/spot/markets")
async def spot_markets(limit: int = Query(20, ge=1, le=200)):
    """
    现货市场列表（清洗后输出）
    """
    url = f"{INJ_INDEXER}/api/exchange/spot/v1/markets"
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"upstream error: {e}")

    markets = data.get("markets", [])
    cleaned = []
    for m in markets[:limit]:
        cleaned.append(
            {
                "market_id": m.get("marketId"),
                "ticker": m.get("ticker"),
                "status": m.get("marketStatus"),
                "base_denom": m.get("baseDenom"),
                "quote_denom": m.get("quoteDenom"),
                "min_price_tick_size": m.get("minPriceTickSize"),
                "min_quantity_tick_size": m.get("minQuantityTickSize"),
            }
        )

    return {"source": "injective_indexer", "count": len(cleaned), "items": cleaned}


@app.get("/orderbook")
async def orderbook(
    market_id: str = Query(..., description="spot marketId (e.g. from /spot/markets)"),
    depth: int = Query(20, ge=1, le=200, description="levels to return"),
):
    """
    Orderbook 深度快照（核心活动交付接口）
    上游：spot/v2/orderbook/{marketId}
    输出：统一成 bids / asks，方便其他开发者直接接入
    """
    url = f"{INJ_INDEXER}/api/exchange/spot/v2/orderbook/{market_id}"

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"upstream error: {e}")

    ob = data.get("orderbook", {})
    buys = ob.get("buys", [])   # 买单（可能存在）
    sells = ob.get("sells", []) # 卖单（你刚刚看到的就是 sells）

    def norm(levels):
        out = []
        for lvl in levels[:depth]:
            out.append(
                {
                    "price": str(lvl.get("price")),
                    "quantity": str(lvl.get("quantity")),
                    "timestamp": lvl.get("timestamp"),
                }
            )
        return out

    return {
        "source": "injective_indexer",
        "market_id": market_id,
        "depth": depth,
        "bids": norm(buys),
        "asks": norm(sells),
        "meta": {
            "sequence": ob.get("sequence"),
            "timestamp": ob.get("timestamp"),
            "height": ob.get("height"),
        },
    }

