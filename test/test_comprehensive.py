"""
Comprehensive test for the improved decision algorithm
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agent.decision_maker import quant_based_decision
from src.indicators.quant_indicator_calculator import get_quant_indicators

def test_comprehensive_scenarios():
    print("Testing comprehensive market scenarios with improved algorithm...")
    
    # Test with real indicators from the calculator
    print("\n--- Testing with real calculated indicators ---")
    btc_indicators = get_quant_indicators('BTC')
    decision = quant_based_decision(btc_indicators)
    print(f"Real BTC indicators: {decision}")
    print(f"  RSI: {btc_indicators['rsi']:.2f}, MACD: {btc_indicators['macd']['value']:.2f}, Position: {btc_indicators['bb_position']:.2f}")
    
    eth_indicators = get_quant_indicators('ETH')
    decision = quant_based_decision(eth_indicators)
    print(f"Real ETH indicators: {decision}")
    print(f"  RSI: {eth_indicators['rsi']:.2f}, MACD: {eth_indicators['macd']['value']:.2f}, Position: {eth_indicators['bb_position']:.2f}")
    
    # Test trending market conditions
    print("\n--- Testing trending market conditions ---")
    strong_uptrend = {
        'rsi': 65,  # Not overbought yet
        'macd': {'value': 1000, 'signal': 800, 'histogram': 200},  # Strong bullish momentum
        'ema': 65000,
        'sma': 64000,
        'bollinger_bands': {'upper': 68000, 'middle': 64000, 'lower': 60000},
        'current_price': 66000,
        'bb_position': 0.5,  # Price in middle of BB - healthy trend
        'bb_width': 8000,
        'stochastic': {'k': 70, 'd': 65},  # Slightly overbought but bullish
        'volume': 5000
    }
    decision = quant_based_decision(strong_uptrend)
    print(f"Strong uptrend: {decision} (should consider trend continuation)")
    
    strong_downtrend = {
        'rsi': 35,  # Not oversold yet
        'macd': {'value': -800, 'signal': -600, 'histogram': -200},  # Strong bearish momentum
        'ema': 58000,
        'sma': 59000,
        'bollinger_bands': {'upper': 62000, 'middle': 58000, 'lower': 54000},
        'current_price': 57000,
        'bb_position': 0.5,  # Price in middle of BB - healthy downtrend
        'bb_width': 8000,
        'stochastic': {'k': 30, 'd': 35},  # Slightly oversold but bearish
        'volume': 5000
    }
    decision = quant_based_decision(strong_downtrend)
    print(f"Strong downtrend: {decision} (should consider trend continuation)")
    
    # Test ranging market (mean reversion friendly)
    print("\n--- Testing ranging market conditions ---")
    ranging_oversold = {
        'rsi': 25,  # Clearly oversold
        'macd': {'value': -200, 'signal': -150, 'histogram': -50},  # Bearish but weak
        'ema': 59500,
        'sma': 60000,  # Slight bearish bias but minimal
        'bollinger_bands': {'upper': 62000, 'middle': 60000, 'lower': 58000},
        'current_price': 58200,  # Near lower BB - potential bounce
        'bb_position': 0.1,  # Very near lower band
        'bb_width': 4000,  # Narrow - ranging market
        'stochastic': {'k': 15, 'd': 20},  # Oversold with bullish crossover
        'volume': 3000
    }
    decision = quant_based_decision(ranging_oversold)
    print(f"Ranging oversold: {decision} (should likely BUY)")
    
    ranging_overbought = {
        'rsi': 75,  # Clearly overbought
        'macd': {'value': 300, 'signal': 250, 'histogram': 50},  # Bullish but weak
        'ema': 60500,
        'sma': 60000,  # Slight bullish bias but minimal
        'bollinger_bands': {'upper': 62000, 'middle': 60000, 'lower': 58000},
        'current_price': 61800,  # Near upper BB - potential pullback
        'bb_position': 0.95,  # Very near upper band
        'bb_width': 4000,  # Narrow - ranging market
        'stochastic': {'k': 85, 'd': 80},  # Overbought with bearish crossover
        'volume': 3000
    }
    decision = quant_based_decision(ranging_overbought)
    print(f"Ranging overbought: {decision} (should likely SELL)")
    
    # Test conflicting signals (should HOLD)
    print("\n--- Testing conflicting signals ---")
    conflicting = {
        'rsi': 75,  # Overbought - SELL
        'macd': {'value': 300, 'signal': 200, 'histogram': 100},  # Bullish - BUY
        'ema': 59000,
        'sma': 60000,  # EMA below SMA - SELL
        'bollinger_bands': {'upper': 62000, 'middle': 60000, 'lower': 58000},
        'current_price': 59500,  # In middle - neutral
        'bb_position': 0.44,
        'bb_width': 4000,
        'stochastic': {'k': 35, 'd': 40},  # Oversold with bearish crossover - SELL
        'volume': 4000
    }
    decision = quant_based_decision(conflicting)
    print(f"Conflicting signals: {decision} (should HOLD due to disagreement)")
    
    # Test weak agreement signals
    print("\n--- Testing weak agreement signals ---")
    weak_bullish = {
        'rsi': 55,  # Slightly bullish
        'macd': {'value': 50, 'signal': 45, 'histogram': 5},  # Weak bullish
        'ema': 60100,
        'sma': 60000,  # Slightly bullish
        'bollinger_bands': {'upper': 62000, 'middle': 60000, 'lower': 58000},
        'current_price': 60200,  # Slightly above middle
        'bb_position': 0.55,
        'bb_width': 4000,
        'stochastic': {'k': 55, 'd': 50},  # Slightly bullish
        'volume': 2000
    }
    decision = quant_based_decision(weak_bullish)
    print(f"Weak bullish agreement: {decision} (should likely HOLD)")
    
    weak_bearish = {
        'rsi': 45,  # Slightly bearish
        'macd': {'value': -50, 'signal': -45, 'histogram': -5},  # Weak bearish
        'ema': 59900,
        'sma': 60000,  # Slightly bearish
        'bollinger_bands': {'upper': 62000, 'middle': 60000, 'lower': 58000},
        'current_price': 59800,  # Slightly below middle
        'bb_position': 0.45,
        'bb_width': 4000,
        'stochastic': {'k': 45, 'd': 50},  # Slightly bearish
        'volume': 2000
    }
    decision = quant_based_decision(weak_bearish)
    print(f"Weak bearish agreement: {decision} (should likely HOLD)")

if __name__ == "__main__":
    test_comprehensive_scenarios()