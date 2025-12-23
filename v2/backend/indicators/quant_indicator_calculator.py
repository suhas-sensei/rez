"""
Quantitative Indicator Calculator
Calculates technical indicators from OHLCV data (from Hyperliquid)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False


class QuantIndicatorCalculator:
    """
    Calculate technical indicators from price data
    """

    def calculate_indicators_from_data(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate technical indicators from OHLCV DataFrame
        
        Args:
            price_data: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
            
        Returns:
            Dictionary containing calculated indicators
        """
        required_cols = ['open', 'high', 'low', 'close']
        for col in required_cols:
            if col not in price_data.columns:
                raise ValueError(f"Required column '{col}' not found in price data")

        if 'timestamp' in price_data.columns:
            price_data = price_data.sort_values('timestamp')

        close = price_data['close'].values
        high = price_data['high'].values
        low = price_data['low'].values
        volume = price_data['volume'].values if 'volume' in price_data.columns else np.ones(len(close))

        rsi = self._calculate_rsi(close)
        macd_data = self._calculate_macd(close)
        ema = self._calculate_ema(close)
        sma = self._calculate_sma(close)
        bb_data = self._calculate_bollinger_bands(close)
        stoch_data = self._calculate_stochastic(high, low, close)
        
        bb_width = bb_data['upper'] - bb_data['lower']
        bb_position = (close[-1] - bb_data['lower']) / bb_width if bb_width != 0 else 0.5
        volatility = np.std(np.diff(close) / close[:-1]) if len(close) > 1 else 0.0

        return {
            'rsi': rsi,
            'macd': macd_data,
            'ema': ema,
            'sma': sma,
            'bollinger_bands': bb_data,
            'stochastic': stoch_data,
            'bb_width': bb_width,
            'bb_position': bb_position,
            'current_price': float(close[-1]),
            'volume': float(volume[-1]) if len(volume) > 0 else 0.0,
            'volatility': float(volatility)
        }

    def _calculate_rsi(self, prices: np.array, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if TALIB_AVAILABLE:
            try:
                rsi = talib.RSI(prices, timeperiod=period)
                if rsi is not None and len(rsi) > 0 and not np.isnan(rsi[-1]):
                    return float(rsi[-1])
            except:
                pass

        # Fallback calculation
        deltas = np.diff(prices)
        gain = np.where(deltas > 0, deltas, 0)
        loss = np.where(deltas < 0, -deltas, 0)

        if len(gain) >= period:
            avg_gain = np.mean(gain[-period:])
            avg_loss = np.mean(loss[-period:])
        else:
            avg_gain = np.mean(gain) if len(gain) > 0 else 0
            avg_loss = np.mean(loss) if len(loss) > 0 else 0.001

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return float(100 - (100 / (1 + rs)))

    def _calculate_macd(self, prices: np.array) -> Dict[str, float]:
        """Calculate MACD"""
        if TALIB_AVAILABLE:
            try:
                macd, signal, hist = talib.MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9)
                if macd is not None and len(macd) > 0 and not np.isnan(macd[-1]):
                    return {
                        'value': float(macd[-1]) if not np.isnan(macd[-1]) else 0.0,
                        'signal': float(signal[-1]) if not np.isnan(signal[-1]) else 0.0,
                        'histogram': float(hist[-1]) if not np.isnan(hist[-1]) else 0.0
                    }
            except:
                pass

        # Fallback
        exp1 = self._ema_array(prices, 12)
        exp2 = self._ema_array(prices, 26)
        macd_line = exp1 - exp2
        signal_line = self._ema_array(macd_line, 9)

        return {
            'value': float(macd_line[-1]),
            'signal': float(signal_line[-1]),
            'histogram': float(macd_line[-1] - signal_line[-1])
        }

    def _calculate_ema(self, prices: np.array, period: int = 20) -> float:
        """Calculate Exponential Moving Average"""
        if TALIB_AVAILABLE:
            try:
                ema = talib.EMA(prices, timeperiod=period)
                if ema is not None and len(ema) > 0 and not np.isnan(ema[-1]):
                    return float(ema[-1])
            except:
                pass

        # Fallback
        multiplier = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        return float(ema)

    def _calculate_sma(self, prices: np.array, period: int = 20) -> float:
        """Calculate Simple Moving Average"""
        if TALIB_AVAILABLE:
            try:
                sma = talib.SMA(prices, timeperiod=period)
                if sma is not None and len(sma) > 0 and not np.isnan(sma[-1]):
                    return float(sma[-1])
            except:
                pass

        if len(prices) >= period:
            return float(np.mean(prices[-period:]))
        return float(np.mean(prices))

    def _calculate_bollinger_bands(self, prices: np.array, period: int = 20, std_dev: int = 2) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        if TALIB_AVAILABLE:
            try:
                upper, middle, lower = talib.BBANDS(prices, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)
                if upper is not None and len(upper) > 0 and not np.isnan(upper[-1]):
                    return {
                        'upper': float(upper[-1]),
                        'middle': float(middle[-1]),
                        'lower': float(lower[-1])
                    }
            except:
                pass

        # Fallback
        if len(prices) >= period:
            sma = np.mean(prices[-period:])
            std = np.std(prices[-period:])
        else:
            sma = np.mean(prices)
            std = np.std(prices)

        return {
            'upper': float(sma + std_dev * std),
            'middle': float(sma),
            'lower': float(sma - std_dev * std)
        }

    def _calculate_stochastic(self, high: np.array, low: np.array, close: np.array, 
                               k_period: int = 14, d_period: int = 3) -> Dict[str, float]:
        """Calculate Stochastic Oscillator"""
        if TALIB_AVAILABLE:
            try:
                slowk, slowd = talib.STOCH(high, low, close, 
                                          fastk_period=k_period, slowk_period=d_period, slowd_period=d_period)
                if slowk is not None and len(slowk) > 0 and not np.isnan(slowk[-1]):
                    return {'k': float(slowk[-1]), 'd': float(slowd[-1])}
            except:
                pass

        # Fallback
        if len(low) >= k_period:
            low_min = np.min(low[-k_period:])
            high_max = np.max(high[-k_period:])
        else:
            low_min = np.min(low)
            high_max = np.max(high)

        if high_max - low_min != 0:
            k_val = (close[-1] - low_min) / (high_max - low_min) * 100
            k_val = max(0, min(100, k_val))
        else:
            k_val = 50.0

        return {'k': float(k_val), 'd': float(k_val)}

    def _ema_array(self, prices: np.array, period: int) -> np.array:
        """Helper to calculate EMA as array"""
        multiplier = 2 / (period + 1)
        ema_values = np.zeros_like(prices)
        ema_values[0] = prices[0]
        for i in range(1, len(prices)):
            ema_values[i] = (prices[i] - ema_values[i-1]) * multiplier + ema_values[i-1]
        return ema_values


def calculate_indicators(price_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Public function to calculate indicators from price data
    
    Args:
        price_data: DataFrame with OHLCV columns (from Hyperliquid candles)
        
    Returns:
        Dict of indicators ready for decision makers
    """
    calculator = QuantIndicatorCalculator()
    return calculator.calculate_indicators_from_data(price_data)
