"""
Advanced Trading Algorithm with Quantitative Finance Techniques
Implements sophisticated signals, ML-based predictions, and intelligent execution
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from config import settings
from indicators.quant_indicator_calculator import QuantIndicatorCalculator

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("Warning: talib not available. Some advanced indicators will use fallback calculations.")


def get_config():
    """Get config in the format expected by existing code"""
    return {
        'llm_api_key': settings.llm_api_key,
        'llm_base_url': settings.llm_base_url,
        'llm_model': settings.llm_model,
        'default_risk_per_trade': 0.02,
        'default_position_size_limit': 0.02,
        'kelly_fraction': 0.15,
    }


class AdvancedTradingAlgorithm:
    """
    Advanced multi-layered trading algorithm implementing:
    - Technical analysis with adaptive thresholds
    - Machine learning predictions
    - Risk management with position sizing
    - Market regime detection
    - Momentum and mean reversion signals
    """

    def __init__(self, risk_profile='medium'):
        self.config = get_config()
        self.models = {}
        self.scaler = StandardScaler()
        self.lookback = 50
        self.risk_manager = AdvancedRiskManager(risk_profile=risk_profile)
        self.regime_detector = MarketRegimeDetector()
        self.indicator_calculator = QuantIndicatorCalculator()
        self.risk_profile = risk_profile

        self.ml_models = {
            'trend_prediction': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
            'volatility_prediction': RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42),
            'momentum_prediction': RandomForestRegressor(n_estimators=75, max_depth=12, random_state=42)
        }

    def calculate_advanced_indicators(self, price_data: pd.DataFrame) -> dict:
        """Calculate sophisticated indicators beyond basic TA"""
        if len(price_data) < 30:
            raise ValueError("Need at least 30 data points for advanced indicators")

        close = price_data['close'].values
        high = price_data['high'].values
        low = price_data['low'].values
        volume = price_data.get('volume', np.ones(len(close))).values

        if TALIB_AVAILABLE:
            rsi = talib.RSI(close)
            macd, macd_signal, macd_hist = talib.MACD(close)
            cci = talib.CCI(high, low, close)
            roc = talib.ROC(close, timeperiod=10)
            atr = talib.ATR(high, low, close)
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close)
            obv = talib.OBV(close, volume)
        else:
            rsi = pd.Series(close).rolling(14).apply(lambda x: 100 - (100 / (1 + np.mean(x[x > x.mean()]) / np.mean(x[x < x.mean()]) if np.mean(x[x < x.mean()]) != 0 else 1)))
            ema12 = pd.Series(close).ewm(span=12).mean()
            ema26 = pd.Series(close).ewm(span=26).mean()
            macd_val = ema12 - ema26
            macd_signal = macd_val.ewm(span=9).mean()
            macd_hist = macd_val - macd_signal
            macd = macd_val
            typical_price = (high + low + close) / 3
            typical_price_series = pd.Series(typical_price)
            cci = (typical_price_series - typical_price_series.rolling(20).mean()) / (0.015 * typical_price_series.rolling(20).std())
            roc = pd.Series(close).pct_change(10) * 100
            tr = pd.Series([max(h - l, abs(h - c_prev), abs(l - c_prev)) for h, l, c, c_prev in
                           zip(high[1:], low[1:], close[1:], close[:-1])])
            atr = pd.Series([np.nan] + tr.rolling(14).mean().tolist())
            bb_middle = pd.Series(close).rolling(20).mean()
            bb_std = pd.Series(close).rolling(20).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            obv = [0]
            for i in range(1, len(close)):
                if close[i] > close[i-1]:
                    obv.append(obv[-1] + volume[i])
                elif close[i] < close[i-1]:
                    obv.append(obv[-1] - volume[i])
                else:
                    obv.append(obv[-1])

        volatility = pd.Series(close).rolling(20).std()
        correlation = pd.Series(close).rolling(10).corr(pd.Series(close).shift(1))
        skewness = pd.Series(close).rolling(20).apply(lambda x: stats.skew(x))
        volume_sma_ratio = volume / pd.Series(volume).rolling(20).mean()
        price_position = (close - low) / (high - low)
        returns = pd.Series(close).pct_change()
        hurst_exponent = self._calculate_hurst_exponent(close)
        hurst_exponent = hurst_exponent if hurst_exponent is not None else 0.5

        def get_last_valid_value(indicator, default_val, current_price=None):
            if isinstance(indicator, (pd.Series, pd.DataFrame)):
                val = indicator.iloc[-1] if len(indicator) > 0 else np.nan
            else:
                val = indicator[-1] if len(indicator) > 0 else np.nan

            if pd.isna(val) or np.isnan(val):
                if current_price is not None and 'close' in str(current_price):
                    if 'upper' in str(default_val):
                        return current_price * 1.02
                    elif 'middle' in str(default_val):
                        return current_price
                    elif 'lower' in str(default_val):
                        return current_price * 0.98
                return default_val
            return float(val)

        return {
            'rsi': get_last_valid_value(rsi, 50),
            'macd': {
                'value': get_last_valid_value(macd, 0),
                'signal': get_last_valid_value(macd_signal, 0),
                'histogram': get_last_valid_value(macd_hist, 0)
            },
            'cci': get_last_valid_value(cci, 0),
            'bollinger_bands': {
                'upper': get_last_valid_value(bb_upper, close[-1] * 1.02, 'upper'),
                'middle': get_last_valid_value(bb_middle, close[-1], 'middle'),
                'lower': get_last_valid_value(bb_lower, close[-1] * 0.98, 'lower')
            },
            'atr': get_last_valid_value(atr, 0),
            'volatility': get_last_valid_value(volatility, 0),
            'correlation': get_last_valid_value(correlation, 0),
            'skewness': get_last_valid_value(skewness, 0),
            'obv': get_last_valid_value(obv, 0),
            'volume_sma_ratio': get_last_valid_value(volume_sma_ratio, 1),
            'price_position': price_position[-1] if not pd.isna(price_position[-1]) else 0.5,
            'roc': get_last_valid_value(roc, 0),
            'hurst_exponent': hurst_exponent,
            'current_price': close[-1],
            'returns': get_last_valid_value(returns, 0)
        }

    def _calculate_hurst_exponent(self, prices):
        """Calculate Hurst exponent to determine market regime"""
        try:
            n = len(prices)
            if n < 20:
                return None

            log_prices = np.log(prices)
            scales = np.arange(10, min(50, n//2))
            rs_vals = []

            for scale in scales:
                rs = []
                for start in range(0, n - scale, scale):
                    segment = log_prices[start:start+scale]
                    if len(segment) < 2:
                        continue
                    mean = np.mean(segment)
                    devs = segment - mean
                    cumsum_devs = np.cumsum(devs)
                    r = np.max(cumsum_devs) - np.min(cumsum_devs)
                    s = np.std(segment)
                    if s != 0:
                        rs.append(r / s)
                if rs:
                    rs_vals.append(np.mean(rs))

            if rs_vals and len(rs_vals) > 1:
                log_rs = np.log(rs_vals)
                log_scales = np.log(scales[:len(rs_vals)])
                slope, _, _, _, _ = stats.linregress(log_scales, log_rs)
                return slope
            else:
                return 0.5
        except:
            return 0.5

    def generate_advanced_signals(self, indicators: dict, asset: str, portfolio_value: float, risk_profile: str = 'medium') -> dict:
        """Generate multiple sophisticated signals"""
        signals = {}
        signals['trend_signal'] = self._calculate_trend_signal(indicators)
        signals['mean_reversion_signal'] = self._calculate_mean_reversion_signal(indicators)
        signals['momentum_signal'] = self._calculate_momentum_signal(indicators)
        signals['volatility_signal'] = self._calculate_volatility_signal(indicators)

        regime = self.regime_detector.detect_regime(indicators, risk_profile)
        signals['regime_signal'] = self._adjust_signals_for_regime(signals, regime, risk_profile)

        position_size = self.risk_manager.calculate_position_size(
            asset, indicators, portfolio_value, regime
        )

        if regime == 'trending':
            if risk_profile == 'high':
                combined_signal = (0.25 * signals['trend_signal'] + 0.35 * signals['momentum_signal'] +
                                  0.20 * signals['regime_signal'] + 0.20 * signals['volatility_signal'])
            elif risk_profile == 'low':
                combined_signal = (0.40 * signals['trend_signal'] + 0.20 * signals['momentum_signal'] +
                                  0.20 * signals['regime_signal'] + 0.20 * signals['volatility_signal'])
            else:
                combined_signal = (0.35 * signals['trend_signal'] + 0.25 * signals['momentum_signal'] +
                                  0.20 * signals['regime_signal'] + 0.20 * signals['volatility_signal'])
        elif regime == 'volatile':
            if risk_profile == 'high':
                combined_signal = (0.25 * signals['mean_reversion_signal'] + 0.30 * signals['volatility_signal'] +
                                  0.25 * signals['regime_signal'] + 0.20 * signals['momentum_signal'])
            elif risk_profile == 'low':
                combined_signal = (0.35 * signals['mean_reversion_signal'] + 0.20 * signals['volatility_signal'] +
                                  0.20 * signals['regime_signal'] + 0.25 * signals['momentum_signal'])
            else:
                combined_signal = (0.30 * signals['mean_reversion_signal'] + 0.25 * signals['volatility_signal'] +
                                  0.25 * signals['regime_signal'] + 0.20 * signals['momentum_signal'])
        else:
            if risk_profile == 'high':
                combined_signal = (0.30 * signals['trend_signal'] + 0.30 * signals['mean_reversion_signal'] +
                                  0.20 * signals['momentum_signal'] + 0.20 * signals['volatility_signal'])
            elif risk_profile == 'low':
                combined_signal = (0.30 * signals['trend_signal'] + 0.20 * signals['mean_reversion_signal'] +
                                  0.25 * signals['momentum_signal'] + 0.25 * signals['volatility_signal'])
            else:
                combined_signal = (0.25 * signals['trend_signal'] + 0.25 * signals['mean_reversion_signal'] +
                                  0.25 * signals['momentum_signal'] + 0.25 * signals['volatility_signal'])

        return {
            'combined_signal': combined_signal,
            'position_size': position_size,
            'regime': regime,
            'individual_signals': signals,
            'confidence': abs(combined_signal)
        }

    def _calculate_trend_signal(self, indicators: dict) -> float:
        rsi = indicators['rsi']
        macd_val = indicators['macd']['value']
        macd_sig = indicators['macd']['signal']
        ema = indicators.get('ema', indicators['current_price'] * 0.99)
        sma = indicators.get('sma', indicators['current_price'])
        current_price = indicators['current_price']

        signal = 0
        if current_price > ema and ema > sma:
            signal += 0.5
        elif current_price < ema and ema < sma:
            signal -= 0.5

        if macd_val > macd_sig:
            signal += 0.3
        elif macd_val < macd_sig:
            signal -= 0.3

        if 30 < rsi < 70:
            signal *= 1.2
        elif rsi > 70:
            signal *= 0.8
        elif rsi < 30:
            signal *= 0.8

        return signal

    def _calculate_mean_reversion_signal(self, indicators: dict) -> float:
        rsi = indicators['rsi']
        bb_upper = indicators['bollinger_bands']['upper']
        bb_lower = indicators['bollinger_bands']['lower']
        current_price = indicators['current_price']
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) != 0 else 0.5

        signal = 0
        if rsi < 30:
            signal += 0.8
        elif rsi < 40:
            signal += 0.5
        elif rsi > 70:
            signal -= 0.8
        elif rsi > 60:
            signal -= 0.5

        if bb_position < 0.2:
            signal += 0.6
        elif bb_position < 0.3:
            signal += 0.4
        elif bb_position > 0.8:
            signal -= 0.6
        elif bb_position > 0.7:
            signal -= 0.4

        return signal

    def _calculate_momentum_signal(self, indicators: dict) -> float:
        roc = indicators['roc']
        macd_hist = indicators['macd']['histogram']
        cci = indicators.get('cci', 0)
        volume_ratio = indicators.get('volume_sma_ratio', 1)

        signal = 0
        if roc > 0:
            signal += 0.4 * min(roc * 10, 1)
        elif roc < 0:
            signal -= 0.4 * min(abs(roc) * 10, 1)

        if macd_hist > 0:
            signal += 0.3
        elif macd_hist < 0:
            signal -= 0.3

        if cci > 100:
            signal += 0.3
        elif cci < -100:
            signal -= 0.3
        elif cci > 0:
            signal += 0.1
        elif cci < 0:
            signal -= 0.1

        if volume_ratio > 1.2:
            signal *= 1.2
        elif volume_ratio < 0.8:
            signal *= 0.8

        return signal

    def _calculate_volatility_signal(self, indicators: dict) -> float:
        volatility = indicators['volatility']
        hurst = indicators['hurst_exponent']
        skewness = indicators['skewness']

        signal = 0

        if hurst > 0.6:
            signal += 0.2
        elif hurst < 0.4:
            signal -= 0.2

        if volatility > np.mean(indicators.get('volatility_history', [volatility])) * 1.5:
            signal += 0.1 * (volatility / np.mean(indicators.get('volatility_history', [volatility])))

        if skewness > 0.5:
            signal += 0.1
        elif skewness < -0.5:
            signal -= 0.1

        return signal

    def _adjust_signals_for_regime(self, signals: dict, regime: str, risk_profile: str = 'medium') -> float:
        if regime == 'trending':
            if risk_profile == 'high':
                trend_weight, mean_rev_weight = 1.3, 0.7
            elif risk_profile == 'low':
                trend_weight, mean_rev_weight = 1.1, 0.9
            else:
                trend_weight, mean_rev_weight = 1.2, 0.8
        elif regime == 'volatile':
            if risk_profile == 'high':
                trend_weight, mean_rev_weight = 0.9, 0.7
            elif risk_profile == 'low':
                trend_weight, mean_rev_weight = 0.7, 0.5
            else:
                trend_weight, mean_rev_weight = 0.8, 0.6
        else:
            if risk_profile == 'high':
                trend_weight, mean_rev_weight = 0.9, 1.1
            elif risk_profile == 'low':
                trend_weight, mean_rev_weight = 0.7, 1.3
            else:
                trend_weight, mean_rev_weight = 0.8, 1.2

        if risk_profile == 'high':
            momentum_weight, vol_weight = 1.1, 1.1
        elif risk_profile == 'low':
            momentum_weight, vol_weight = 0.9, 0.9
        else:
            momentum_weight, vol_weight = 1.0, 1.0

        trend_signal = signals['trend_signal'] * trend_weight
        mean_rev_signal = signals['mean_reversion_signal'] * mean_rev_weight
        momentum_signal = signals['momentum_signal'] * momentum_weight
        vol_signal = signals['volatility_signal'] * vol_weight

        return (trend_signal + mean_rev_signal + momentum_signal + vol_signal) / 4.0


class AdvancedRiskManager:
    """Advanced risk management with position sizing based on Kelly Criterion"""

    def __init__(self, risk_profile='medium'):
        self.risk_profile = risk_profile.lower()

        if self.risk_profile == 'low':
            self.max_position_size = 0.015
            self.max_total_risk = 0.10
            self.kelly_fraction = 0.10
        elif self.risk_profile == 'high':
            self.max_position_size = 0.03
            self.max_total_risk = 0.20
            self.kelly_fraction = 0.18
        else:
            self.max_position_size = 0.02
            self.max_total_risk = 0.15
            self.kelly_fraction = 0.15

    def calculate_position_size(self, asset: str, indicators: dict, portfolio_value: float, regime: str) -> float:
        win_rate = self._estimate_win_rate(indicators, regime)
        avg_win = 0.02
        avg_loss = 0.015

        if avg_loss > 0:
            b = avg_win / avg_loss
            kelly_percentage = (b * win_rate - (1 - win_rate)) / b
            kelly_percentage = max(0, min(self.max_position_size, kelly_percentage))
        else:
            kelly_percentage = 0.02

        if regime == 'volatile':
            kelly_percentage *= 0.7
        elif regime == 'trending':
            kelly_percentage *= 1.2

        position_size = kelly_percentage * self.kelly_fraction
        position_size = min(self.max_position_size, position_size)
        dollar_amount = portfolio_value * position_size
        return min(dollar_amount, portfolio_value * self.max_total_risk)

    def _estimate_win_rate(self, indicators: dict, regime: str) -> float:
        rsi = indicators['rsi']
        roc = indicators['roc']
        volatility = indicators['volatility']

        base_win_rate = 0.55

        if 30 <= rsi <= 70:
            base_win_rate -= 0.05
        elif rsi < 30 or rsi > 70:
            base_win_rate += 0.05

        if abs(roc) > 0.03:
            base_win_rate += 0.03

        if volatility > 0.05:
            base_win_rate -= 0.05

        if regime == 'volatile':
            base_win_rate -= 0.05
        elif regime == 'trending':
            base_win_rate += 0.02

        return max(0.45, min(0.65, base_win_rate))


class MarketRegimeDetector:
    """Detect market regime (trending, ranging, volatile)"""

    def detect_regime(self, indicators: dict, risk_profile: str = 'medium') -> str:
        volatility = indicators['volatility']
        atr = indicators['atr']
        hurst = indicators['hurst_exponent']
        current_price = indicators['current_price']

        if risk_profile == 'low':
            vol_threshold_multiplier = 0.8
            hurst_trend_threshold = 0.65
            hurst_mean_rev_threshold = 0.35
            atr_trend_threshold_multiplier = 0.8
        elif risk_profile == 'high':
            vol_threshold_multiplier = 1.2
            hurst_trend_threshold = 0.55
            hurst_mean_rev_threshold = 0.45
            atr_trend_threshold_multiplier = 1.2
        else:
            vol_threshold_multiplier = 1.0
            hurst_trend_threshold = 0.6
            hurst_mean_rev_threshold = 0.4
            atr_trend_threshold_multiplier = 1.0

        is_high_vol = volatility > (0.05 * current_price * vol_threshold_multiplier)
        is_trending = hurst > hurst_trend_threshold
        is_mean_reverting = hurst < hurst_mean_rev_threshold

        if is_high_vol:
            return 'volatile'
        elif is_trending:
            return 'trending'
        elif is_mean_reverting:
            return 'ranging'
        else:
            if atr > (0.02 * current_price * atr_trend_threshold_multiplier):
                return 'trending'
            else:
                return 'ranging'


def make_advanced_trading_decision(asset: str, price_data: pd.DataFrame, portfolio_value: float, risk_profile: str = 'medium') -> dict:
    """Main function to make advanced trading decisions"""
    try:
        algo = AdvancedTradingAlgorithm(risk_profile=risk_profile)
        indicators = algo.calculate_advanced_indicators(price_data)
        advanced_signals = algo.generate_advanced_signals(indicators, asset, portfolio_value, risk_profile)

        combined_signal = advanced_signals['combined_signal']
        confidence = advanced_signals['confidence']
        regime = advanced_signals['regime']

        if risk_profile == 'low':
            buy_threshold_strong, buy_threshold_weak = 0.5, 0.25
            sell_threshold_strong, sell_threshold_weak = -0.5, -0.25
        elif risk_profile == 'high':
            buy_threshold_strong, buy_threshold_weak = 0.35, 0.15
            sell_threshold_strong, sell_threshold_weak = -0.35, -0.15
        else:
            buy_threshold_strong, buy_threshold_weak = 0.4, 0.2
            sell_threshold_strong, sell_threshold_weak = -0.4, -0.2

        if combined_signal > buy_threshold_strong:
            decision, strength = 'BUY', 'STRONG'
        elif combined_signal > buy_threshold_weak:
            decision, strength = 'BUY', 'WEAK'
        elif combined_signal < sell_threshold_strong:
            decision, strength = 'SELL', 'STRONG'
        elif combined_signal < sell_threshold_weak:
            decision, strength = 'SELL', 'WEAK'
        else:
            decision, strength = 'HOLD', 'NEUTRAL'

        return {
            'decision': decision,
            'strength': strength,
            'combined_signal': combined_signal,
            'confidence': confidence,
            'regime': regime,
            'position_size': advanced_signals['position_size'],
            'detailed_signals': advanced_signals['individual_signals'],
            'indicators_used': {
                'rsi': indicators['rsi'],
                'macd': indicators['macd']['value'],
                'volatility': indicators['volatility'],
                'hurst_exponent': indicators['hurst_exponent']
            },
            'risk_profile': risk_profile
        }

    except Exception as e:
        print(f"Error in advanced trading decision: {e}")
        from agent.decision_maker import quant_based_decision
        basic_indicators = {
            'rsi': 50, 'macd': {'value': 0, 'signal': 0, 'histogram': 0},
            'ema': price_data['close'].iloc[-1], 'sma': price_data['close'].iloc[-1],
            'bollinger_bands': {'upper': price_data['close'].iloc[-1]*1.02,
                               'middle': price_data['close'].iloc[-1],
                               'lower': price_data['close'].iloc[-1]*0.98},
            'current_price': price_data['close'].iloc[-1]
        }
        simple_decision = quant_based_decision(basic_indicators)
        return {
            'decision': simple_decision,
            'strength': 'FALLBACK',
            'combined_signal': 0,
            'confidence': 0.3,
            'regime': 'unknown',
            'position_size': portfolio_value * 0.01,
            'detailed_signals': {},
            'indicators_used': basic_indicators,
            'risk_profile': risk_profile
        }
