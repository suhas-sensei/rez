"""
FastAPI Backend for Rez Trading Agent
Endpoints for agent control, portfolio, trades, and user management
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import json

from config import settings
from trading.hyperliquid_client import HyperliquidClient, get_client, get_historical_data
from services.funding import get_funding_service, FundingService
from indicators.quant_indicator_calculator import calculate_indicators
from agent.decision_maker import make_trading_decision


# ==================== MODELS ====================

class UserRegisterRequest(BaseModel):
    privy_id: str
    wallet_address: str

class FundUserRequest(BaseModel):
    privy_id: str
    amount: Optional[float] = None

class AgentStartRequest(BaseModel):
    assets: List[str] = ["ETH"]  # ETH only for now
    risk_profile: str = "low"
    interval_seconds: int = 30  # Faster trading
    betting_amount: float = 10.0  # Hyperliquid minimum is $10

class PlaceOrderRequest(BaseModel):
    asset: str
    side: str  # "buy" or "sell"
    size: float
    order_type: str = "market"  # "market" or "limit"
    price: Optional[float] = None


# ==================== APP SETUP ====================

app = FastAPI(
    title="Rez Trading Agent API",
    description="AI-powered trading agent on Hyperliquid",
    version="2.0.0"
)

# Debug: Print settings on startup
print(f"[STARTUP] Hyperliquid Wallet: {settings.hyperliquid_wallet_address}")
print(f"[STARTUP] Testnet: {settings.hyperliquid_testnet}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== AGENT STATE ====================

class AgentState:
    def __init__(self):
        self.running = False
        self.paused = False
        self.assets: List[str] = ["ETH"]
        self.risk_profile: str = "low"
        self.interval_seconds: int = 30
        self.betting_amount: float = 10.0  # Hyperliquid minimum is $10
        self.trade_history: List[Dict] = []
        self.last_decisions: Dict[str, Dict] = {}
        self.task: Optional[asyncio.Task] = None
        # Track open position for P&L calculation
        self.open_position: Optional[Dict] = None  # {asset, side, size, entry_price, entry_time}
        self.realized_pnl: float = 0.0  # Total realized P&L

agent_state = AgentState()

# WebSocket connections for real-time updates
websocket_connections: List[WebSocket] = []


# ==================== WEBSOCKET ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)


async def broadcast_update(data: Dict):
    """Send update to all connected WebSocket clients"""
    message = json.dumps(data, default=str)
    for ws in websocket_connections:
        try:
            await ws.send_text(message)
        except:
            pass


# ==================== HEALTH ====================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "testnet": settings.hyperliquid_testnet
    }


# ==================== USER & FUNDING ====================

@app.post("/users/register")
async def register_user(request: UserRegisterRequest):
    """Register a new user from Privy authentication"""
    funding_service = get_funding_service()
    result = funding_service.register_user(request.privy_id, request.wallet_address)
    return result


@app.post("/users/fund")
async def fund_user(request: FundUserRequest):
    """Fund a user's wallet with testnet tokens"""
    funding_service = get_funding_service()
    result = funding_service.fund_user(request.privy_id, request.amount)
    return result


@app.get("/users/{privy_id}/funding-status")
async def get_funding_status(privy_id: str):
    """Get funding status for a user"""
    funding_service = get_funding_service()
    return funding_service.get_user_funding_status(privy_id)


@app.post("/users/register-and-fund")
async def register_and_fund_user(request: UserRegisterRequest):
    """Register a new user and automatically fund their wallet"""
    funding_service = get_funding_service()
    
    # Register
    reg_result = funding_service.register_user(request.privy_id, request.wallet_address)
    
    # Fund if new user
    if reg_result.get("status") == "created":
        fund_result = funding_service.fund_user(request.privy_id)
        return {
            "registration": reg_result,
            "funding": fund_result
        }
    
    return {
        "registration": reg_result,
        "funding": {"status": "skipped", "message": "User already exists"}
    }


# ==================== PORTFOLIO ====================

@app.get("/portfolio")
async def get_portfolio(wallet_address: Optional[str] = None):
    """Get portfolio state (positions, balance)"""
    client = get_client()

    # Always use the configured Hyperliquid wallet (where the funds are)
    # The Privy wallet is for authentication only
    addr = settings.hyperliquid_wallet_address
    print(f"[DEBUG] Portfolio request - wallet address from settings: {addr}")

    if not addr:
        raise HTTPException(status_code=400, detail="No Hyperliquid wallet configured")

    # Get raw state from Hyperliquid
    raw_state = client.info.user_state(addr)
    print(f"[DEBUG] Raw state from Hyperliquid: {raw_state}")

    state = client.get_account_state(addr)
    print(f"[DEBUG] Parsed state: {state}")

    if "error" in state:
        raise HTTPException(status_code=500, detail=state["error"])

    return {
        "wallet_address": addr,
        "account_value": state.get("account_value", 0),
        "available_balance": state.get("available_balance", 0),
        "margin_used": state.get("margin_used", 0),
        "positions": state.get("positions", []),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/portfolio/positions")
async def get_positions(wallet_address: Optional[str] = None):
    """Get open positions"""
    client = get_client()
    addr = wallet_address or settings.hyperliquid_wallet_address
    return {"positions": client.get_positions(addr)}


@app.get("/portfolio/balance")
async def get_balance(wallet_address: Optional[str] = None):
    """Get account balance"""
    client = get_client()
    addr = wallet_address or settings.hyperliquid_wallet_address
    return {"balance": client.get_balance(addr)}


# ==================== MARKET DATA ====================

@app.get("/market/prices")
async def get_all_prices():
    """Get current prices for all assets"""
    client = get_client()
    return {"prices": client.get_all_prices()}


@app.get("/market/price/{asset}")
async def get_asset_price(asset: str):
    """Get current price for an asset"""
    client = get_client()
    price = client.get_price(asset)
    if price is None:
        raise HTTPException(status_code=404, detail=f"Price not found for {asset}")
    return {"asset": asset, "price": price}


@app.get("/market/candles/{asset}")
async def get_candles(asset: str, interval: str = "1h", lookback: int = 50):
    """Get historical candles for an asset"""
    client = get_client()
    df = client.get_candles(asset, interval, lookback)
    
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No candle data for {asset}")
    
    return {
        "asset": asset,
        "interval": interval,
        "candles": df.to_dict(orient="records")
    }


@app.get("/market/assets")
async def get_available_assets():
    """Get list of tradeable assets"""
    client = get_client()
    return {"assets": client.get_available_assets()}


# ==================== TRADING ====================

@app.post("/trading/order")
async def place_order(request: PlaceOrderRequest):
    """Place a trading order"""
    client = get_client()
    
    is_buy = request.side.lower() == "buy"
    
    if request.order_type == "market":
        result = client.place_market_order(request.asset, is_buy, request.size)
    else:
        if request.price is None:
            raise HTTPException(status_code=400, detail="Price required for limit orders")
        result = client.place_limit_order(request.asset, is_buy, request.size, request.price)
    
    # Record trade
    agent_state.trade_history.append({
        **result,
        "timestamp": datetime.now().isoformat()
    })
    
    # Broadcast update
    await broadcast_update({"type": "trade", "data": result})
    
    return result


@app.post("/trading/close/{asset}")
async def close_position(asset: str):
    """Close position for an asset"""
    client = get_client()
    result = client.close_position(asset)
    await broadcast_update({"type": "position_closed", "data": result})
    return result


@app.delete("/trading/orders")
async def cancel_all_orders(asset: Optional[str] = None):
    """Cancel all open orders"""
    client = get_client()
    return client.cancel_all_orders(asset)


@app.get("/trading/orders")
async def get_open_orders(wallet_address: Optional[str] = None):
    """Get open orders"""
    client = get_client()
    addr = wallet_address or settings.hyperliquid_wallet_address
    return {"orders": client.get_open_orders(addr)}


@app.get("/trading/history")
async def get_trade_history(limit: int = 50):
    """Get recent trade history from this session"""
    return {"trades": agent_state.trade_history[-limit:]}


# ==================== AGENT CONTROL ====================

@app.post("/agent/start")
async def start_agent(request: AgentStartRequest):
    """Start the trading agent"""
    if agent_state.running:
        return {"status": "already_running"}

    agent_state.assets = ["ETH"]  # Force ETH only
    agent_state.risk_profile = request.risk_profile
    agent_state.interval_seconds = request.interval_seconds
    agent_state.betting_amount = request.betting_amount
    agent_state.running = True
    agent_state.paused = False
    agent_state.open_position = None
    agent_state.realized_pnl = 0.0
    agent_state.trade_history = []  # Reset trade history on new session

    # Start the trading loop
    agent_state.task = asyncio.create_task(trading_loop())

    await broadcast_update({"type": "agent_started", "data": {
        "assets": ["ETH"],
        "risk_profile": request.risk_profile,
        "betting_amount": request.betting_amount
    }})

    return {
        "status": "started",
        "assets": ["ETH"],
        "risk_profile": request.risk_profile,
        "interval_seconds": request.interval_seconds,
        "betting_amount": request.betting_amount
    }


@app.post("/agent/stop")
async def stop_agent():
    """Stop the trading agent"""
    if not agent_state.running:
        return {"status": "not_running"}
    
    agent_state.running = False
    if agent_state.task:
        agent_state.task.cancel()
    
    await broadcast_update({"type": "agent_stopped"})
    return {"status": "stopped"}


@app.post("/agent/pause")
async def pause_agent():
    """Pause the trading agent"""
    agent_state.paused = True
    await broadcast_update({"type": "agent_paused"})
    return {"status": "paused"}


@app.post("/agent/resume")
async def resume_agent():
    """Resume the trading agent"""
    agent_state.paused = False
    await broadcast_update({"type": "agent_resumed"})
    return {"status": "resumed"}


@app.get("/agent/status")
async def get_agent_status():
    """Get current agent status"""
    return {
        "running": agent_state.running,
        "paused": agent_state.paused,
        "assets": agent_state.assets,
        "risk_profile": agent_state.risk_profile,
        "interval_seconds": agent_state.interval_seconds,
        "betting_amount": agent_state.betting_amount,
        "open_position": agent_state.open_position,
        "realized_pnl": agent_state.realized_pnl,
        "last_decisions": agent_state.last_decisions,
        "trade_count": len(agent_state.trade_history)
    }


@app.get("/agent/decisions")
async def get_last_decisions():
    """Get the last trading decisions for each asset"""
    return {"decisions": agent_state.last_decisions}


# ==================== TRADING LOOP ====================

async def trading_loop():
    """Main trading loop - ETH only, uses betting amount, tracks P&L"""
    client = get_client()
    asset = "ETH"  # Fixed to ETH only

    print(f"[AGENT] Started with betting amount: ${agent_state.betting_amount}")

    while agent_state.running:
        if agent_state.paused:
            await asyncio.sleep(1)
            continue

        try:
            # Get ETH price data
            price_data = client.get_candles(asset, "15m", 50)  # 15min candles for faster signals

            if price_data.empty:
                print(f"[AGENT] No price data for {asset}, retrying...")
                await asyncio.sleep(5)
                continue

            current_price = float(price_data['close'].iloc[-1])

            # Make trading decision using LLM
            from indicators.quant_indicator_calculator import calculate_indicators
            indicators = calculate_indicators(price_data)
            indicators['current_price'] = current_price

            decision_result = make_trading_decision(
                asset=asset,
                indicators=indicators,
                portfolio_value=agent_state.betting_amount,
                risk_profile=agent_state.risk_profile
            )

            # Convert string decision to dict format
            decision = {
                "decision": decision_result,
                "combined_signal": 0,  # LLM doesn't return signal score
                "llm_used": True
            }

            # Store decision
            agent_state.last_decisions[asset] = {
                **decision,
                "current_price": current_price,
                "timestamp": datetime.now().isoformat()
            }

            print(f"[AGENT] Decision: {decision['decision']} | Signal: {decision.get('combined_signal', 0):.3f} | Price: ${current_price:.2f}")

            # Broadcast decision
            await broadcast_update({
                "type": "decision",
                "asset": asset,
                "data": decision
            })

            # Trading logic with position tracking
            if decision["decision"] == "BUY" and agent_state.open_position is None:
                # Open new position - use betting amount
                size_in_eth = agent_state.betting_amount / current_price
                size_in_eth = round(size_in_eth, 4)  # ETH has 4 decimals

                # Check balance - must pass wallet address
                available = client.get_account_state(settings.hyperliquid_wallet_address).get("available_balance", 0)
                if agent_state.betting_amount > available:
                    print(f"[AGENT] Insufficient balance: need ${agent_state.betting_amount}, have ${available:.2f}")
                else:
                    result = client.place_market_order(asset, True, size_in_eth)
                    print(f"[AGENT] OPENED LONG: {size_in_eth:.4f} ETH @ ${current_price:.2f}")

                    # Track open position
                    agent_state.open_position = {
                        "asset": asset,
                        "side": "LONG",
                        "size": size_in_eth,
                        "entry_price": current_price,
                        "entry_value": agent_state.betting_amount,
                        "entry_time": datetime.now().isoformat()
                    }

                    # Record trade
                    trade_record = {
                        "asset": asset,
                        "decision": "BUY",
                        "side": "OPEN_LONG",
                        "size": size_in_eth,
                        "price": current_price,
                        "value": agent_state.betting_amount,
                        "pnl": None,  # No P&L on open
                        "timestamp": datetime.now().isoformat()
                    }
                    agent_state.trade_history.append(trade_record)
                    await broadcast_update({"type": "trade", "data": trade_record})

            elif decision["decision"] == "SELL" and agent_state.open_position is not None:
                # Close position and calculate P&L
                pos = agent_state.open_position
                size_in_eth = pos["size"]
                entry_price = pos["entry_price"]
                entry_value = pos["entry_value"]

                result = client.place_market_order(asset, False, size_in_eth)
                exit_value = size_in_eth * current_price
                pnl = exit_value - entry_value

                print(f"[AGENT] CLOSED LONG: {size_in_eth:.4f} ETH @ ${current_price:.2f} | P&L: ${pnl:.2f}")

                # Update realized P&L
                agent_state.realized_pnl += pnl
                agent_state.open_position = None

                # Record trade
                trade_record = {
                    "asset": asset,
                    "decision": "SELL",
                    "side": "CLOSE_LONG",
                    "size": size_in_eth,
                    "price": current_price,
                    "entry_price": entry_price,
                    "value": exit_value,
                    "pnl": pnl,
                    "timestamp": datetime.now().isoformat()
                }
                agent_state.trade_history.append(trade_record)
                await broadcast_update({"type": "trade", "data": trade_record})

            # Broadcast status update
            await broadcast_update({
                "type": "status",
                "open_position": agent_state.open_position,
                "realized_pnl": agent_state.realized_pnl,
                "current_price": current_price
            })

        except Exception as e:
            print(f"[AGENT] Error: {e}")
            import traceback
            traceback.print_exc()
            await broadcast_update({"type": "error", "asset": asset, "message": str(e)})

        # Wait for next interval
        await asyncio.sleep(agent_state.interval_seconds)


# ==================== EMERGENCY ====================

@app.post("/emergency/close-all")
async def emergency_close_all():
    """Emergency: Close all positions and stop agent"""
    client = get_client()
    
    # Stop agent
    agent_state.running = False
    if agent_state.task:
        agent_state.task.cancel()
    
    # Close all positions
    positions = client.get_positions()
    results = []
    
    for pos in positions:
        asset = pos.get("asset")
        if asset:
            result = client.close_position(asset)
            results.append({"asset": asset, "result": result})
    
    # Cancel all orders
    cancel_result = client.cancel_all_orders()
    
    await broadcast_update({"type": "emergency_close", "data": results})
    
    return {
        "status": "emergency_close_executed",
        "positions_closed": results,
        "orders_cancelled": cancel_result
    }


# ==================== RUN ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
