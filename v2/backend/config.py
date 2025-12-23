import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Hyperliquid
    hyperliquid_private_key: str = ""
    hyperliquid_wallet_address: str = ""
    hyperliquid_testnet: bool = True

    # Master wallet for funding new users
    master_wallet_private_key: str = ""
    master_wallet_address: str = ""
    default_funding_amount: float = 100.0  # USDC to send new users
    max_funding_per_user: float = 500.0

    # LLM Configuration
    llm_api_key: str = ""
    llm_base_url: Optional[str] = None
    llm_model: str = "gpt-4o-mini"

    # TAAPI for indicators
    taapi_api_key: str = ""

    # Trading defaults
    default_risk_profile: str = "medium"
    trading_interval_seconds: int = 60

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Privy (for JWT verification)
    privy_app_id: str = ""
    privy_app_secret: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()


def get_hyperliquid_api_url() -> str:
    """Get the appropriate Hyperliquid API URL based on testnet setting"""
    if settings.hyperliquid_testnet:
        return "https://api.hyperliquid-testnet.xyz"
    return "https://api.hyperliquid.xyz"
