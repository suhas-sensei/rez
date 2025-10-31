"""
Advanced Data Fetcher Module
Fetches and manages historical price data for advanced trading algorithms
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AdvancedDataFetcher:
    """
    Fetches historical price data for advanced analysis
    """
    
    def __init__(self):
        self.data_cache = {}
        
    def fetch_historical_data(self, asset: str, interval: str = '1h', lookback_periods: int = 50) -> pd.DataFrame:
        """
        Fetch or generate historical price data for the given asset
        """
        cache_key = f"{asset}_{interval}_{lookback_periods}"
        
        # Check cache first
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        
        # Generate mock historical data since we're in simulation
        df = self._generate_mock_data(asset, interval, lookback_periods)
        
        # Cache the data
        self.data_cache[cache_key] = df
        
        return df
    
    def _generate_mock_data(self, asset: str, interval: str, periods: int) -> pd.DataFrame:
        """
        Generate realistic mock price data
        """
        # Base prices for different assets
        base_prices = {
            'BTC': 60000,
            'ETH': 3000,
            'SOL': 150,
            'AVAX': 40,
            'XRP': 0.5,
            'ADA': 0.4,
            'DOGE': 0.15,
            'DOT': 7,
            'LINK': 15,
            'MATIC': 0.8,
            'UNI': 10,
            'LTC': 90,
            'BCH': 600,
            'ETC': 25,
            'XLM': 0.15,
            'TRX': 0.15,
            'AVAX': 40,
            'ATOM': 12
        }
        
        base_price = base_prices.get(asset.upper(), 100)
        
        # Generate realistic price movements based on asset volatility
        volatility = self._get_asset_volatility(asset)
        
        # Generate prices with realistic movement
        prices = [base_price]
        for i in range(1, periods):
            # Create trending, ranging, or volatile periods
            if i % 15 == 0:  # Every 15 periods, change regime slightly
                regime = random.choice(['trend_up', 'trend_down', 'range', 'volatile'])
            else:
                regime = 'continue'
            
            # Generate return based on regime
            if regime == 'trend_up':
                daily_return = np.random.normal(0.01, volatility * 0.8)  # 1% average daily trend up
            elif regime == 'trend_down':
                daily_return = np.random.normal(-0.008, volatility * 0.8)  # 0.8% average daily trend down
            elif regime == 'volatile':
                daily_return = np.random.normal(0, volatility * 1.5)  # Higher volatility
            elif regime == 'range':
                daily_return = np.random.normal(0, volatility * 0.5)  # Lower volatility for ranging
            else:  # continue
                daily_return = np.random.normal(0, volatility)
            
            new_price = max(0.01, prices[-1] * (1 + daily_return))  # Ensure price doesn't go below $0.01
            prices.append(new_price)
        
        # Create OHLCV data from closing prices
        opens = []
        highs = []
        lows = []
        closes = prices
        volumes = []
        
        for i, close in enumerate(closes):
            if i == 0:
                open_price = close * np.random.uniform(0.99, 1.01)
            else:
                open_price = closes[i-1]  # Previous close is today's open
            opens.append(open_price)
            
            # Calculate high and low based on open/close and some random variation
            high_low_range = abs(close - open_price) + close * volatility * 0.5
            high = max(open_price, close) + np.random.uniform(0, high_low_range)
            low = min(open_price, close) - np.random.uniform(0, high_low_range * 0.7)
            
            # Ensure low doesn't go below 0
            low = max(0.01, low)
            
            highs.append(high)
            lows.append(low)
            
            # Random volume
            volume = np.random.uniform(1000, 10000)
            volumes.append(volume)
        
        df = pd.DataFrame({
            'timestamp': pd.date_range(end=datetime.now(), periods=periods, freq=self._get_freq(interval)),
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes
        })
        
        return df
    
    def _get_asset_volatility(self, asset: str) -> float:
        """
        Get typical volatility for different assets
        """
        volatility_map = {
            'BTC': 0.03,   # 3% daily
            'ETH': 0.04,   # 4% daily
            'SOL': 0.08,   # 8% daily (more volatile)
            'AVAX': 0.06,  # 6% daily
            'XRP': 0.05,   # 5% daily
            'ADA': 0.06,   # 6% daily
            'DOGE': 0.07,  # 7% daily
            'DOT': 0.05,   # 5% daily
            'LINK': 0.04,  # 4% daily
            'MATIC': 0.06, # 6% daily
            'UNI': 0.05,   # 5% daily
            'LTC': 0.04,   # 4% daily
            'BCH': 0.04,   # 4% daily
            'ETC': 0.05,   # 5% daily
            'XLM': 0.04,   # 4% daily
            'TRX': 0.05,   # 5% daily
            'ATOM': 0.04   # 4% daily
        }
        return volatility_map.get(asset.upper(), 0.05)  # Default 5% volatility
    
    def _get_freq(self, interval: str) -> str:
        """
        Convert interval string to pandas frequency
        """
        interval_map = {
            '1m': '1T',
            '5m': '5T',
            '15m': '15T',
            '30m': '30T',
            '1h': 'H',
            '4h': '4H',
            '1d': 'D',
            '1w': 'W'
        }
        return interval_map.get(interval, 'H')  # Default to hourly

# Global instance for easy access
data_fetcher = AdvancedDataFetcher()

def get_historical_data(asset: str, interval: str = '1h', lookback_periods: int = 50) -> pd.DataFrame:
    """
    Public function to get historical data
    """
    return data_fetcher.fetch_historical_data(asset, interval, lookback_periods)