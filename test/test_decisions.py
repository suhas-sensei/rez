"""
Test script to verify the decision making logic with different indicator values
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agent.decision_maker import quant_based_decision

def test_decision_logic():
    print("Testing different market conditions with updated thresholds...")
    
    # Test with oversold conditions (RSI < 30)
    oversold_indicators = {
        'rsi': 25,
        'macd': {'value': -0.5, 'signal': -0.3},
        'ema': 55000,
        'sma': 56000,
        'bollinger_bands': {'upper': 58000, 'middle': 56000, 'lower': 54000},
        'current_price': 55000,
        'bb_position': 0.15,
        'stochastic': {'k': 15, 'd': 20}
    }
    decision = quant_based_decision(oversold_indicators)
    print(f"Oversold conditions: {decision} (expected: BUY)")
    
    # Test with overbought conditions (RSI > 70)
    overbought_indicators = {
        'rsi': 75,
        'macd': {'value': 0.8, 'signal': 0.6},
        'ema': 65000,
        'sma': 64000,
        'bollinger_bands': {'upper': 66000, 'middle': 64000, 'lower': 62000},
        'current_price': 65500,
        'bb_position': 0.85,
        'stochastic': {'k': 85, 'd': 80}
    }
    decision = quant_based_decision(overbought_indicators)
    print(f"Overbought conditions: {decision} (expected: SELL)")
    
    # Test with bullish MACD crossover
    bullish_macd = {
        'rsi': 55,
        'macd': {'value': 0.5, 'signal': 0.3},  # Bullish crossover
        'ema': 60500,
        'sma': 60000,
        'bollinger_bands': {'upper': 62000, 'middle': 60000, 'lower': 58000},
        'current_price': 60500,
        'bb_position': 0.55,
        'stochastic': {'k': 60, 'd': 55}
    }
    decision = quant_based_decision(bullish_macd)
    print(f"Bullish MACD crossover: {decision} (expected: BUY)")
    
    # Test with bearish MACD crossover
    bearish_macd = {
        'rsi': 45,
        'macd': {'value': -0.3, 'signal': -0.1},  # Bearish crossover
        'ema': 59500,
        'sma': 60000,
        'bollinger_bands': {'upper': 62000, 'middle': 60000, 'lower': 58000},
        'current_price': 59500,
        'bb_position': 0.45,
        'stochastic': {'k': 40, 'd': 45}
    }
    decision = quant_based_decision(bearish_macd)
    print(f"Bearish MACD crossover: {decision} (expected: SELL)")
    
    # Test with neutral conditions
    neutral_indicators = {
        'rsi': 50,
        'macd': {'value': 0.05, 'signal': 0.05},  # No clear signal
        'ema': 60000,
        'sma': 60000,
        'bollinger_bands': {'upper': 62000, 'middle': 60000, 'lower': 58000},
        'current_price': 60000,
        'bb_position': 0.5,
        'stochastic': {'k': 50, 'd': 50}
    }
    decision = quant_based_decision(neutral_indicators)
    print(f"Neutral conditions: {decision} (expected: HOLD)")

if __name__ == "__main__":
    test_decision_logic()