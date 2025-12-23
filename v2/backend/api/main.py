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
from agent.advanced_decision_maker import make_advanced_trading_decision


# ==================== MODELS ====================

class UserRegisterRequest(BaseModel):
    privy_id: str
    wallet_address: str

class FundUserRequest(BaseModel):
    privy_id: str
    amount: Optional[float] = None

class AgentStartRequest(BaseModel):
    assets: List[str] = ["BTC", "ETH"]
    risk_profile: str = "medium"
    interval_seconds: int = 60

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
        self.assets: List[str] = []
        self.risk_profile: str = "medium"
        self.interval_seconds: int = 60
        self.trade_history: List[Dict] = []
        self.last_decisions: Dict[str, Dict] = {}
        self.task: Optional[asyncio.Task] = None

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
    
    addr = wallet_address or settings.hyperliquid_wallet_address
    if not addr:
        raise HTTPException(status_code=400, detail="No wallet address provided")
    
    state = client.get_account_state(addr)
    
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
    
    agent_state.assets = request.assets
    agent_state.risk_profile = request.risk_profile
    agent_state.interval_seconds = request.interval_seconds
    agent_state.running = True
    agent_state.paused = False
    
    # Start the trading loop
    agent_state.task = asyncio.create_task(trading_loop())
    
    await broadcast_update({"type": "agent_started", "data": {
        "assets": request.assets,
        "risk_profile": request.risk_profile
    }})
    
    return {
        "status": "started",
        "assets": request.assets,
        "risk_profile": request.risk_profile,
        "interval_seconds": request.interval_seconds
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
        "last_decisions": agent_state.last_decisions,
        "trade_count": len(agent_state.trade_history)
    }


@app.get("/agent/decisions")
async def get_last_decisions():
    """Get the last trading decisions for each asset"""
    return {"decisions": agent_state.last_decisions}


# ==================== TRADING LOOP ====================

async def trading_loop():
    """Main trading loop - runs continuously when agent is active"""
    client = get_client()
    
    while agent_state.running:
        if agent_state.paused:
            await asyncio.sleep(1)
            continue
        
        for asset in agent_state.assets:
            if not agent_state.running:
                break
                
            try:
                # Get historical data from Hyperliquid
                price_data = client.get_candles(asset, "1h", 50)
                
                if price_data.empty:
                    print(f"No price data for {asset}, skipping")
                    continue
                
                # Get portfolio value
                portfolio_value = client.get_balance()
                
                # Make trading decision using your AI
                decision = make_advanced_trading_decision(
                    asset=asset,
                    price_data=price_data,
                    portfolio_value=portfolio_value,
                    risk_profile=agent_state.risk_profile
                )
                
                # Store decision
                agent_state.last_decisions[asset] = {
                    **decision,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Broadcast decision
                await broadcast_update({
                    "type": "decision",
                    "asset": asset,
                    "data": decision
                })
                
                # Execute if not HOLD
                if decision["decision"] != "HOLD":
                    # Calculate position size
                    position_size = decision.get("position_size", portfolio_value * 0.01)
                    current_price = price_data['close'].iloc[-1]
                    size_in_asset = position_size / current_price
                    
                    # Place order
                    is_buy = decision["decision"] == "BUY"
                    result = client.place_market_order(asset, is_buy, size_in_asset)
                    
                    # Record trade
                    trade_record = {
                        "asset": asset,
                        "decision": decision["decision"],
                        "size": size_in_asset,
                        "price": current_price,
                        "result": result,
                        "analysis": decision,
                        "timestamp": datetime.now().isoformat()
                    }
                    agent_state.trade_history.append(trade_record)
                    
                    # Broadcast trade
                    await broadcast_update({"type": "trade", "data": trade_record})
                
            except Exception as e:
                print(f"Error processing {asset}: {e}")
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
