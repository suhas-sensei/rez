"""
Funding Service
Auto-funds new user wallets with testnet tokens when they sign up
"""
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime
from eth_account import Account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants
import json
import os
from config import settings


@dataclass
class FundingRecord:
    """Record of a funding transaction"""
    user_id: str
    wallet_address: str
    amount: float
    tx_hash: Optional[str]
    timestamp: str
    status: str  # "pending", "completed", "failed"


@dataclass 
class UserRecord:
    """User account record"""
    privy_id: str
    wallet_address: str
    created_at: str
    total_funded: float = 0.0
    funding_history: List[FundingRecord] = field(default_factory=list)


class UserStore:
    """Simple JSON-based user storage (replace with DB in production)"""
    
    def __init__(self, storage_path: str = "data/users.json"):
        self.storage_path = storage_path
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, 'w') as f:
                json.dump({}, f)
    
    def _load(self) -> Dict:
        with open(self.storage_path, 'r') as f:
            return json.load(f)
    
    def _save(self, data: Dict):
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def get_user_by_privy_id(self, privy_id: str) -> Optional[Dict]:
        data = self._load()
        return data.get(privy_id)
    
    def get_user_by_wallet(self, wallet_address: str) -> Optional[Dict]:
        data = self._load()
        for user in data.values():
            if user.get("wallet_address", "").lower() == wallet_address.lower():
                return user
        return None
    
    def create_user(self, privy_id: str, wallet_address: str) -> Dict:
        data = self._load()
        
        if privy_id in data:
            return data[privy_id]
        
        user = {
            "privy_id": privy_id,
            "wallet_address": wallet_address,
            "created_at": datetime.now().isoformat(),
            "total_funded": 0.0,
            "funding_history": []
        }
        
        data[privy_id] = user
        self._save(data)
        return user
    
    def update_user_funding(self, privy_id: str, amount: float, tx_hash: Optional[str], status: str):
        data = self._load()
        
        if privy_id not in data:
            return
        
        funding_record = {
            "amount": amount,
            "tx_hash": tx_hash,
            "timestamp": datetime.now().isoformat(),
            "status": status
        }
        
        data[privy_id]["funding_history"].append(funding_record)
        
        if status == "completed":
            data[privy_id]["total_funded"] += amount
        
        self._save(data)
    
    def get_total_funded(self, privy_id: str) -> float:
        user = self.get_user_by_privy_id(privy_id)
        return user.get("total_funded", 0.0) if user else 0.0


class FundingService:
    """
    Service to fund new user wallets with testnet tokens
    """
    
    def __init__(self):
        self.user_store = UserStore()
        self.max_funding_per_user = settings.max_funding_per_user
        self.default_funding_amount = settings.default_funding_amount
        
        # Initialize master wallet for funding
        self.master_exchange = None
        self.master_info = None
        
        if settings.master_wallet_private_key:
            try:
                api_url = constants.TESTNET_API_URL if settings.hyperliquid_testnet else constants.MAINNET_API_URL
                master_wallet = Account.from_key(settings.master_wallet_private_key)
                self.master_exchange = Exchange(master_wallet, api_url)
                self.master_info = Info(api_url, skip_ws=True)
                self.master_address = master_wallet.address
                print(f"Funding service initialized with master wallet: {self.master_address}")
            except Exception as e:
                print(f"Warning: Could not initialize master wallet for funding: {e}")
    
    def register_user(self, privy_id: str, wallet_address: str) -> Dict:
        """
        Register a new user from Privy authentication
        
        Args:
            privy_id: User's Privy ID
            wallet_address: User's embedded wallet address
            
        Returns:
            User record dict
        """
        existing = self.user_store.get_user_by_privy_id(privy_id)
        if existing:
            return {"status": "existing", "user": existing}
        
        user = self.user_store.create_user(privy_id, wallet_address)
        return {"status": "created", "user": user}
    
    def fund_user(self, privy_id: str, amount: Optional[float] = None) -> Dict:
        """
        Fund a user's wallet with testnet tokens
        
        Args:
            privy_id: User's Privy ID
            amount: Amount to fund (uses default if not specified)
            
        Returns:
            Funding result dict
        """
        user = self.user_store.get_user_by_privy_id(privy_id)
        if not user:
            return {"status": "error", "message": "User not found"}
        
        wallet_address = user.get("wallet_address")
        if not wallet_address:
            return {"status": "error", "message": "User has no wallet address"}
        
        # Check funding limits
        total_funded = self.user_store.get_total_funded(privy_id)
        fund_amount = amount or self.default_funding_amount
        
        if total_funded + fund_amount > self.max_funding_per_user:
            remaining = self.max_funding_per_user - total_funded
            if remaining <= 0:
                return {
                    "status": "limit_reached",
                    "message": f"User has reached max funding limit of {self.max_funding_per_user}",
                    "total_funded": total_funded
                }
            fund_amount = remaining
        
        # Check if master wallet is configured
        if not self.master_exchange:
            # Record as pending/simulated if no master wallet
            self.user_store.update_user_funding(privy_id, fund_amount, None, "simulated")
            return {
                "status": "simulated",
                "message": "Funding simulated (no master wallet configured)",
                "amount": fund_amount
            }
        
        # Execute the transfer
        try:
            result = self._transfer_funds(wallet_address, fund_amount)
            
            if result.get("status") == "ok":
                tx_hash = result.get("tx_hash")
                self.user_store.update_user_funding(privy_id, fund_amount, tx_hash, "completed")
                return {
                    "status": "completed",
                    "message": f"Successfully funded {fund_amount} to {wallet_address}",
                    "amount": fund_amount,
                    "tx_hash": tx_hash
                }
            else:
                self.user_store.update_user_funding(privy_id, fund_amount, None, "failed")
                return {
                    "status": "failed",
                    "message": result.get("message", "Transfer failed"),
                    "amount": fund_amount
                }
                
        except Exception as e:
            self.user_store.update_user_funding(privy_id, fund_amount, None, "failed")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _transfer_funds(self, to_address: str, amount: float) -> Dict:
        """
        Transfer USDC from master wallet to user wallet on Hyperliquid
        
        Note: On Hyperliquid, you transfer using the USD balance (USDC)
        """
        if not self.master_exchange:
            return {"status": "error", "message": "Master wallet not configured"}
        
        try:
            # Check master wallet balance first
            master_state = self.master_info.user_state(self.master_address)
            master_balance = float(master_state.get("marginSummary", {}).get("accountValue", 0))
            
            if master_balance < amount:
                return {
                    "status": "error", 
                    "message": f"Insufficient master wallet balance: {master_balance} < {amount}"
                }
            
            # Execute transfer using Hyperliquid's transfer function
            # Note: This transfers USD (USDC) to another address on Hyperliquid
            result = self.master_exchange.usd_transfer(to_address, amount)
            
            if result.get("status") == "ok":
                return {
                    "status": "ok",
                    "tx_hash": result.get("response", {}).get("data", {}).get("hash"),
                    "amount": amount
                }
            else:
                return {
                    "status": "error",
                    "message": f"Transfer failed: {result}"
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_user_funding_status(self, privy_id: str) -> Dict:
        """Get funding status for a user"""
        user = self.user_store.get_user_by_privy_id(privy_id)
        if not user:
            return {"status": "error", "message": "User not found"}
        
        return {
            "status": "ok",
            "wallet_address": user.get("wallet_address"),
            "total_funded": user.get("total_funded", 0),
            "max_allowed": self.max_funding_per_user,
            "remaining": self.max_funding_per_user - user.get("total_funded", 0),
            "funding_history": user.get("funding_history", [])
        }
    
    def get_master_wallet_balance(self) -> float:
        """Get current balance of master funding wallet"""
        if not self.master_info or not self.master_address:
            return 0.0
        
        try:
            state = self.master_info.user_state(self.master_address)
            return float(state.get("marginSummary", {}).get("accountValue", 0))
        except:
            return 0.0


# Global instance
_funding_service: Optional[FundingService] = None


def get_funding_service() -> FundingService:
    """Get or create the global funding service instance"""
    global _funding_service
    if _funding_service is None:
        _funding_service = FundingService()
    return _funding_service
