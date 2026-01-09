"""
Hyperliquid Client
Handles all interactions with Hyperliquid testnet/mainnet:
- Market data (prices, candles)
- Order execution (market, limit)
- Account state (positions, balances)
"""
from typing import Optional, Dict, List, Any
from eth_account import Account
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
import pandas as pd
from datetime import datetime
from config import settings


class HyperliquidClient:
    """
    Unified client for Hyperliquid DEX operations
    """

    def __init__(self, private_key: Optional[str] = None, wallet_address: Optional[str] = None, testnet: bool = True):
        """
        Initialize Hyperliquid client
        
        Args:
            private_key: Wallet private key for signing transactions
            wallet_address: Wallet address (public key)
            testnet: Use testnet (True) or mainnet (False)
        """
        self.testnet = testnet
        self.api_url = constants.TESTNET_API_URL if testnet else constants.MAINNET_API_URL
        
        # Use provided keys or fall back to settings
        self.private_key = private_key or settings.hyperliquid_private_key
        self.wallet_address = wallet_address or settings.hyperliquid_wallet_address
        
        # Initialize Info client (read-only, no auth needed)
        self.info = Info(self.api_url, skip_ws=True)
        
        # Initialize Exchange client (for trading, needs auth)
        self.exchange = None
        if self.private_key:
            try:
                wallet = Account.from_key(self.private_key)
                self.exchange = Exchange(wallet, self.api_url)
                self.wallet_address = wallet.address
            except Exception as e:
                print(f"Warning: Could not initialize Exchange client: {e}")

    # ==================== MARKET DATA ====================

    def get_all_prices(self) -> Dict[str, float]:
        """Get current mid prices for all assets"""
        try:
            all_mids = self.info.all_mids()
            return {asset: float(price) for asset, price in all_mids.items()}
        except Exception as e:
            print(f"Error fetching prices: {e}")
            return {}

    def get_price(self, asset: str) -> Optional[float]:
        """Get current price for a single asset"""
        prices = self.get_all_prices()
        return prices.get(asset.upper())

    def get_candles(self, asset: str, interval: str = "1h", lookback: int = 50) -> pd.DataFrame:
        """
        Get historical OHLCV candles for an asset

        Args:
            asset: Asset symbol (e.g., "BTC", "ETH")
            interval: Candle interval ("1m", "5m", "15m", "1h", "4h", "1d")
            lookback: Number of candles to fetch

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            # Hyperliquid uses asset names directly (BTC, ETH, etc.)
            import time

            # Calculate time range based on interval
            interval_seconds = {
                "1m": 60, "5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400
            }.get(interval, 3600)

            end_time = int(time.time() * 1000)
            start_time = end_time - (lookback * interval_seconds * 1000)

            # candles_snapshot takes (coin, interval, startTime, endTime)
            candles = self.info.candles_snapshot(asset.upper(), interval, start_time, end_time)
            
            if not candles or len(candles) == 0:
                print(f"No candle data for {asset}")
                return pd.DataFrame()

            df = pd.DataFrame(candles)
            
            # Rename columns to standard format
            df = df.rename(columns={
                't': 'timestamp',
                'o': 'open',
                'h': 'high',
                'l': 'low',
                'c': 'close',
                'v': 'volume'
            })
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Ensure numeric types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df.sort_values('timestamp').reset_index(drop=True)
            
        except Exception as e:
            print(f"Error fetching candles for {asset}: {e}")
            return pd.DataFrame()

    def get_orderbook(self, asset: str) -> Dict[str, Any]:
        """Get current orderbook for an asset"""
        try:
            return self.info.l2_snapshot(asset.upper())
        except Exception as e:
            print(f"Error fetching orderbook: {e}")
            return {}

    # ==================== ACCOUNT STATE ====================

    def get_account_state(self, address: Optional[str] = None) -> Dict[str, Any]:
        """
        Get full account state including balances and positions

        Returns dict with:
            - account_value: Total account value in USD
            - margin_used: Margin currently in use
            - available_balance: Available for trading
            - positions: List of open positions
        """
        addr = address or self.wallet_address
        if not addr:
            return {"error": "No wallet address configured"}

        try:
            state = self.info.user_state(addr)
            print(f"[DEBUG] Raw user_state response: {state}")

            margin_summary = state.get("marginSummary", {})
            positions = state.get("assetPositions", [])

            # Try multiple possible field names for account value
            account_value = 0.0
            if margin_summary:
                account_value = float(margin_summary.get("accountValue", 0) or 0)

            # Try multiple possible field names for withdrawable/available balance
            available = 0.0
            if "withdrawable" in state:
                available = float(state.get("withdrawable", 0) or 0)
            elif "crossMarginSummary" in state:
                cross_margin = state.get("crossMarginSummary", {})
                available = float(cross_margin.get("accountValue", 0) or 0)

            # If account_value is still 0, try using available as fallback
            if account_value == 0 and available > 0:
                account_value = available

            # Parse positions
            parsed_positions = []
            for pos in positions:
                position_data = pos.get("position", {})
                if position_data:
                    parsed_positions.append({
                        "asset": position_data.get("coin", ""),
                        "size": float(position_data.get("szi", 0) or 0),
                        "entry_price": float(position_data.get("entryPx", 0) or 0),
                        "unrealized_pnl": float(position_data.get("unrealizedPnl", 0) or 0),
                        "leverage": float(position_data.get("leverage", {}).get("value", 1) if isinstance(position_data.get("leverage"), dict) else 1),
                        "liquidation_price": position_data.get("liquidationPx")
                    })

            print(f"[DEBUG] Parsed account_value: {account_value}, available: {available}")

            return {
                "account_value": account_value,
                "margin_used": float(margin_summary.get("totalMarginUsed", 0) or 0),
                "available_balance": available,
                "positions": parsed_positions
            }

        except Exception as e:
            print(f"Error fetching account state: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def get_balance(self, address: Optional[str] = None) -> float:
        """Get account balance (total value in USD)"""
        state = self.get_account_state(address)
        return state.get("account_value", 0.0)

    def get_positions(self, address: Optional[str] = None) -> List[Dict]:
        """Get list of open positions"""
        state = self.get_account_state(address)
        return state.get("positions", [])

    def get_position(self, asset: str, address: Optional[str] = None) -> Optional[Dict]:
        """Get position for a specific asset"""
        positions = self.get_positions(address)
        for pos in positions:
            if pos.get("asset", "").upper() == asset.upper():
                return pos
        return None

    # ==================== ORDER EXECUTION ====================

    def place_market_order(self, asset: str, is_buy: bool, size: float, slippage: float = 0.03) -> Dict[str, Any]:
        """
        Place a market order using aggressive limit order (better for testnet)

        Args:
            asset: Asset symbol (e.g., "BTC")
            is_buy: True for buy/long, False for sell/short
            size: Position size in asset units
            slippage: Acceptable slippage (default 3% for testnet wide spreads)

        Returns:
            Order result dict
        """
        if not self.exchange:
            return {"status": "error", "message": "Exchange client not initialized (no private key)"}

        try:
            # Get current price and use aggressive limit order (works better on testnet)
            current_price = self.get_price(asset)
            if not current_price:
                return {"status": "error", "message": f"Could not get price for {asset}"}

            # Use aggressive price with slippage
            if is_buy:
                limit_price = current_price * (1 + slippage)  # Pay up to 3% more
            else:
                limit_price = current_price * (1 - slippage)  # Accept 3% less

            # Round price to appropriate precision
            limit_price = round(limit_price, 1)

            print(f"[TRADE] Placing {'BUY' if is_buy else 'SELL'} order: {size} {asset} @ ${limit_price} (market: ${current_price})")

            # Use IOC (Immediate or Cancel) limit order - acts like market order
            order_type = {"limit": {"tif": "Ioc"}}
            result = self.exchange.order(asset.upper(), is_buy, size, limit_price, order_type)

            print(f"[TRADE] Order result: {result}")

            return {
                "status": "ok" if result.get("status") == "ok" else "error",
                "result": result,
                "order_type": "market",
                "asset": asset,
                "side": "buy" if is_buy else "sell",
                "size": size,
                "price": limit_price,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[TRADE] Error: {e}")
            return {"status": "error", "message": str(e)}

    def place_limit_order(self, asset: str, is_buy: bool, size: float, price: float, 
                          tif: str = "Gtc", reduce_only: bool = False) -> Dict[str, Any]:
        """
        Place a limit order
        
        Args:
            asset: Asset symbol
            is_buy: True for buy, False for sell
            size: Position size
            price: Limit price
            tif: Time in force - "Gtc" (Good til Canceled), "Ioc" (Immediate or Cancel), "Alo" (Add Liquidity Only)
            reduce_only: If True, order can only reduce position
            
        Returns:
            Order result dict
        """
        if not self.exchange:
            return {"status": "error", "message": "Exchange client not initialized"}
            
        try:
            order_type = {"limit": {"tif": tif}}
            result = self.exchange.order(asset.upper(), is_buy, size, price, order_type, reduce_only=reduce_only)
            return {
                "status": "ok" if result.get("status") == "ok" else "error",
                "result": result,
                "order_type": "limit",
                "asset": asset,
                "side": "buy" if is_buy else "sell",
                "size": size,
                "price": price,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def close_position(self, asset: str, slippage: float = 0.01) -> Dict[str, Any]:
        """Close entire position for an asset"""
        if not self.exchange:
            return {"status": "error", "message": "Exchange client not initialized"}
            
        try:
            result = self.exchange.market_close(asset.upper(), slippage=slippage)
            return {
                "status": "ok" if result.get("status") == "ok" else "error",
                "result": result,
                "action": "close_position",
                "asset": asset,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def cancel_order(self, asset: str, order_id: int) -> Dict[str, Any]:
        """Cancel an open order"""
        if not self.exchange:
            return {"status": "error", "message": "Exchange client not initialized"}
            
        try:
            result = self.exchange.cancel(asset.upper(), order_id)
            return {"status": "ok", "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def cancel_all_orders(self, asset: Optional[str] = None) -> Dict[str, Any]:
        """Cancel all open orders (optionally for a specific asset)"""
        if not self.exchange:
            return {"status": "error", "message": "Exchange client not initialized"}
            
        try:
            if asset:
                result = self.exchange.cancel_all(asset.upper())
            else:
                result = self.exchange.cancel_all()
            return {"status": "ok", "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_open_orders(self, address: Optional[str] = None) -> List[Dict]:
        """Get all open orders"""
        addr = address or self.wallet_address
        if not addr:
            return []
            
        try:
            return self.info.open_orders(addr)
        except Exception as e:
            print(f"Error fetching open orders: {e}")
            return []

    # ==================== UTILITY ====================

    def get_meta(self) -> Dict[str, Any]:
        """Get exchange metadata (available assets, etc.)"""
        try:
            return self.info.meta()
        except Exception as e:
            print(f"Error fetching meta: {e}")
            return {}

    def get_available_assets(self) -> List[str]:
        """Get list of tradeable assets"""
        meta = self.get_meta()
        universe = meta.get("universe", [])
        return [asset.get("name", "") for asset in universe]


# Global instance for easy access
_client: Optional[HyperliquidClient] = None


def get_client() -> HyperliquidClient:
    """Get or create the global Hyperliquid client instance"""
    global _client
    if _client is None:
        _client = HyperliquidClient(testnet=settings.hyperliquid_testnet)
    return _client


def get_historical_data(asset: str, interval: str = "1h", lookback_periods: int = 50) -> pd.DataFrame:
    """
    Public function to get historical data (replaces Binance fetcher)
    Compatible with existing decision maker interface
    """
    client = get_client()
    return client.get_candles(asset, interval, lookback_periods)
