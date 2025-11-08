"""
Advanced Data Fetcher Module
Fetches and manages historical price data for advanced trading algorithms
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time
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
        Fetch real historical price data for the given asset
        """
        cache_key = f"{asset}_{interval}_{lookback_periods}"
        
        # Check cache first
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        
        # Try to fetch real data from Binance
        df = self._fetch_real_data(asset, interval, lookback_periods)
        
        # Cache the data
        self.data_cache[cache_key] = df
        
        return df
    
    def _fetch_real_data(self, asset: str, interval: str, lookback_periods: int) -> pd.DataFrame:
        """
        Fetch real historical data from Binance API (no API key required)
        """
        # Map common asset names to Binance symbols
        asset_mapping = {
            'BTC': 'BTCUSDT',
            'ETH': 'ETHUSDT',
            'SOL': 'SOLUSDT',
            'AVAX': 'AVAXUSDT',
            'ADA': 'ADAUSDT',
            'DOT': 'DOTUSDT',
            'LINK': 'LINKUSDT',
            'MATIC': 'MATICUSDT',
            'UNI': 'UNIUSDT',
            'LTC': 'LTCUSDT',
            'BCH': 'BCHUSDT',
            'ETC': 'ETCUSDT',
            'XLM': 'XLMUSDT',
            'TRX': 'TRXUSDT',
            'DOGE': 'DOGEUSDT',
            'XRP': 'XRPUSDT',
            'ATOM': 'ATOMUSDT',
            'NEAR': 'NEARUSDT',
            'APT': 'APTUSDT',
            'ARB': 'ARBUSDT',
            'PEPE': 'PEPEUSDT',
            'SHIB': 'SHIBUSDT',
            'POL': 'POLUSDT',  # POL was rebranded to POL from MATIC
            'XMR': 'XMRUSDT',
            'ALGO': 'ALGOUSDT',
            'XTZ': 'XTZUSDT',
            'BSV': 'BSVUSDT',
            'DGB': 'DGBUSDT',
            'RVN': 'RVNUSDT',
            'ZEC': 'ZECUSDT',
            'ENJ': 'ENJUSDT',
            'MANA': 'MANAUSDT',
            'SAND': 'SANDUSDT',
            'AAVE': 'AAVEUSDT',
            'CRV': 'CRVUSDT',
            'COMP': 'COMPUSDT',
            'MKR': 'MKRUSDT',
            'YFI': 'YFIUSDT',
            'SNX': 'SNXUSDT',
            'FIL': 'FILUSDT',
            'HBAR': 'HBARUSDT',
            'ICP': 'ICPUSDT',
            'VET': 'VETUSDT',
            'SUI': 'SUIUSDT',
            'STX': 'STXUSDT',
            'FET': 'FETUSDT',
            'FLOW': 'FLOWUSDT',
            'GRT': 'GRTUSDT',
            'CHZ': 'CHZUSDT',
            'THETA': 'THETAUSDT',
            'AXS': 'AXSUSDT',
            'FTM': 'FTMUSDT',
            'LDO': 'LDOUSDT',
            'INJ': 'INJUSDT',
            'RUNE': 'RUNEUSDT',
            'CAKE': 'CAKEUSDT',
            'QNT': 'QNTUSDT',
            'EGLD': 'EGLDUSDT',
            'AGIX': 'AGIXUSDT',
            'TIA': 'TIAUSDT',
            'KSM': 'KSMUSDT',
            'MINA': 'MINAUSDT',
            'ROSE': 'ROSEUSDT',
            'JUP': 'JUPUSDT',
            'PYTH': 'PYTHUSDT',
            'STRK': 'STRKUSDT',
            'WIF': 'WIFUSDT'
        }
        
        # Get Binance symbol for the asset
        symbol = asset_mapping.get(asset.upper())
        if not symbol:
            print(f"Asset {asset} not found in Binance mapping. Using mock data.")
            return self._generate_mock_data(asset, interval, lookback_periods)
        
        try:
            # Calculate limit for the request
            limit = lookback_periods
            
            # Map interval to Binance format
            binance_interval = self._get_binance_interval(interval)
            
            # Fetch market data from Binance
            base_url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': binance_interval,
                'limit': limit
            }
            
            # Use headers to avoid being blocked by servers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(base_url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                if not data or len(data) == 0:
                    print(f"No data returned for {asset} (symbol: {symbol})")
                    return self._generate_mock_data(asset, interval, lookback_periods)
                
                # Process the data - Binance klines format: [timestamp, open, high, low, close, volume, ...]
                timestamps = []
                opens = []
                highs = []
                lows = []
                closes = []
                volumes = []
                
                for item in data:
                    timestamps.append(pd.Timestamp.fromtimestamp(item[0]/1000))
                    opens.append(float(item[1]))
                    highs.append(float(item[2]))
                    lows.append(float(item[3]))
                    closes.append(float(item[4]))
                    volumes.append(float(item[5]))
                
                df = pd.DataFrame({
                    'timestamp': pd.to_datetime(timestamps),
                    'open': pd.Series(opens, dtype='float64'),
                    'high': pd.Series(highs, dtype='float64'),
                    'low': pd.Series(lows, dtype='float64'),
                    'close': pd.Series(closes, dtype='float64'),
                    'volume': pd.Series(volumes, dtype='float64')
                })
                
                # Adding small delay to prevent rate limiting when multiple assets are requested
                time.sleep(0.1)
                
                return df
            else:
                print(f"Failed to fetch data for {asset} (symbol: {symbol}). Status: {response.status_code} - Using mock data")
                time.sleep(0.1)  # Small delay before fallback
                return self._generate_mock_data(asset, interval, lookback_periods)
                
        except Exception as e:
            print(f"Error fetching real data for {asset}: {e}")
            time.sleep(0.1)  # Small delay before fallback
            return self._generate_mock_data(asset, interval, lookback_periods)
    
    def _get_binance_interval(self, interval: str) -> str:
        """
        Map interval to Binance format
        """
        binance_intervals = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d',
            '1w': '1w'
        }
        return binance_intervals.get(interval, '1h')
    
    def _generate_mock_data(self, asset: str, interval: str, periods: int) -> pd.DataFrame:
        """
        Generate realistic mock price data (fallback if real data not available)
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
            return_val = np.random.normal(0, volatility)
            new_price = max(0.01, prices[-1] * (1 + return_val))  # Ensure price doesn't go below $0.01
            prices.append(new_price)
        
        # Create OHLCV data from closing prices
        opens = []
        highs = []
        lows = []
        closes = prices
        volumes = []
        
        for i, close in enumerate(closes):
            if i == 0:
                open_price = close
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
            
            # Realistic volume based on asset
            volume_base = {
                'BTC': 25000000000,  # $25B
                'ETH': 15000000000,  # $15B
                'SOL': 1000000000,   # $1B
                'AVAX': 300000000,   # $300M
                'XRP': 2000000000,   # $2B
                'ADA': 500000000,    # $500M
                'DOGE': 1000000000,  # $1B
                'DOT': 300000000,    # $300M
                'LINK': 400000000,   # $400M
                'MATIC': 600000000,  # $600M
                'UNI': 300000000,    # $300M
                'LTC': 2000000000,   # $2B
                'BCH': 1500000000,   # $1.5B
                'ETC': 200000000,    # $200M
                'XLM': 500000000,    # $500M
                'TRX': 300000000,    # $300M
                'AVAX': 300000000,   # $300M
                'ATOM': 400000000     # $400M
            }
            
            base_volume = volume_base.get(asset.upper(), 100000000)  # Default $100M
            volume = base_volume * np.random.uniform(0.5, 2.0)  # 50-200% of base volume
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
            '1m': '1min',
            '5m': '5min',
            '15m': '15min',
            '30m': '30min',
            '1h': '1h',
            '4h': '4h',
            '1d': '1D',
            '1w': '1W'
        }
        return interval_map.get(interval, '1h')  # Default to hourly
    


# Global instance for easy access
data_fetcher = AdvancedDataFetcher()

def get_historical_data(asset: str, interval: str = '1h', lookback_periods: int = 50) -> pd.DataFrame:
    """
    Public function to get historical data
    """
    return data_fetcher.fetch_historical_data(asset, interval, lookback_periods)