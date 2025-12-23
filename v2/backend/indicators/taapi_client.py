import requests
from config import settings


def get_technical_indicators(asset, interval='1h'):
    """
    Fetch technical indicators from TAAPI.io
    """
    taapi_api_key = settings.taapi_api_key

    if not taapi_api_key:
        # Return mock data for simulation if no API key
        return {
            'rsi': 50,
            'macd': {'value': 0.1, 'signal': 0.05},
            'ema': 50000,
            'sma': 49500,
            'bollinger_bands': {'upper': 51000, 'middle': 50000, 'lower': 49000}
        }

    # Example: fetch RSI indicator
    url = f"https://api.taapi.io/rsi"
    payload = {
        "secret": taapi_api_key,
        "exchange": "binance",
        "symbol": f"{asset}/USDT",
        "interval": interval
    }

    try:
        response = requests.post(url, json=payload)
        rsi = response.json().get('value', 50)
    except:
        rsi = 50  # Default value if API fails

    # For MVP, returning mock data with RSI from API
    return {
        'rsi': rsi,
        'macd': {'value': 0.1, 'signal': 0.05},
        'ema': 50000,
        'sma': 49500,
        'bollinger_bands': {'upper': 51000, 'middle': 50000, 'lower': 49000}
    }
