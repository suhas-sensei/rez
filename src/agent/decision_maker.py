import os
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_config
import openai
from datetime import datetime
from indicators.quant_indicator_calculator import get_quant_indicators

def make_trading_decision(asset, indicators, portfolio_value):
    """
    Use AI to make a trading decision based on technical indicators and portfolio state
    Supports both OpenAI-compatible APIs and open source models
    """
    config = load_config()
    
    # Prepare the prompt for the LLM
    prompt = f"""
    You are an expert trading bot. Based on the following market data, make a trading decision.
    
    Current asset: {asset}
    Portfolio value: ${portfolio_value:,.2f}
    Current indicators:
    - RSI: {indicators['rsi']}
    - MACD value: {indicators['macd']['value']}
    - MACD signal: {indicators['macd']['signal']}
    - EMA: {indicators['ema']}
    - SMA: {indicators['sma']}
    - Bollinger Bands: Upper {indicators['bollinger_bands']['upper']}, 
                       Middle {indicators['bollinger_bands']['middle']}, 
                       Lower {indicators['bollinger_bands']['lower']}
    
    Current time: {datetime.now().isoformat()}
    
    Please respond with ONLY ONE of these three words:
    1. "BUY" - if the indicators suggest going long
    2. "SELL" - if the indicators suggest going short
    3. "HOLD" - if the indicators suggest maintaining current position or being neutral
    
    Be concise and only respond with the single word decision.
    """
    
    # Configure the LLM client
    if config['llm_base_url']:
        # Using a local model or OpenAI-compatible API (like Ollama) or OpenRouter
        client = openai.OpenAI(
            base_url=config['llm_base_url'],
            api_key=config['llm_api_key']
        )
    else:
        # Using a standard OpenAI-compatible API
        client = openai.OpenAI(
            base_url=config.get('llm_base_url', 'https://api.openai.com/v1'),
            api_key=config['llm_api_key']
        )
    
    try:
        response = client.chat.completions.create(
            model=config['llm_model'],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.1  # Low temperature for more consistent decisions
        )
        
        decision = response.choices[0].message.content.strip().upper()
        
        # Validate the decision
        if decision in ['BUY', 'SELL', 'HOLD', 'LONG', 'SHORT']:
            if decision == 'LONG':
                decision = 'BUY'
            elif decision == 'SHORT':
                decision = 'SELL'
            return decision
        else:
            # Fallback to HOLD if the response is not one of the expected values
            return 'HOLD'
            
    except Exception as e:
        print(f"Error getting AI decision: {e}")
        # Fallback to quant library-based technical analysis if AI fails
        return quant_based_decision(indicators)


def quant_based_decision(indicators):
    """
    Advanced fallback decision based on quant library calculations.
    This function uses multiple technical indicators to make more nuanced decisions.
    """
    try:
        # Extract key indicators with safe access
        rsi = indicators.get('rsi', 50) or 50
        macd = indicators.get('macd', {'value': 0, 'signal': 0}) or {'value': 0, 'signal': 0}
        macd_value = macd.get('value', 0) or 0
        macd_signal = macd.get('signal', 0) or 0
        ema = indicators.get('ema', 0) or 0
        sma = indicators.get('sma', 0) or 0
        bb_data = indicators.get('bollinger_bands', {'upper': 0, 'middle': 0, 'lower': 0}) or {'upper': 0, 'middle': 0, 'lower': 0}
        current_price = indicators.get('current_price', 0) or 0
        bb_position = indicators.get('bb_position', 0.5) or 0.5  # Position within BB (0-1)
        stochastic_data = indicators.get('stochastic', {'k': 50, 'd': 50}) or {'k': 50, 'd': 50}
        stoch_k = stochastic_data.get('k', 50) or 50
        stoch_d = stochastic_data.get('d', 50) or 50
        
        # Initialize scores
        rsi_score = 0
        macd_score = 0
        ma_score = 0
        bb_score = 0
        stoch_score = 0
        
        # RSI Analysis
        if rsi < 30:  # Oversold - BUY signal
            rsi_score = 2
        elif rsi < 40:  # Slightly oversold - BUY signal
            rsi_score = 1
        elif rsi > 70:  # Overbought - SELL signal
            rsi_score = -2
        elif rsi > 60:  # Slightly overbought - SELL signal
            rsi_score = -1
        
        # MACD Analysis
        if macd_value > macd_signal:  # Bullish crossover
            macd_score = 1
        elif macd_value < macd_signal:  # Bearish crossover
            macd_score = -1
        
        # Moving Average Analysis
        if current_price > ema and ema > sma:  # Price above EMA and EMA above SMA (bullish)
            ma_score = 1
        elif current_price < ema and ema < sma:  # Price below EMA and EMA below SMA (bearish)
            ma_score = -1
        
        # Bollinger Bands Analysis
        if bb_position < 0.2:  # Price near lower band (oversold)
            bb_score = 1
        elif bb_position > 0.8:  # Price near upper band (overbought)
            bb_score = -1
        
        # Stochastic Analysis
        if stoch_k < 20 and stoch_k > stoch_d:  # Oversold and bullish crossover
            stoch_score = 1
        elif stoch_k > 80 and stoch_k < stoch_d:  # Overbought and bearish crossover
            stoch_score = -1
        
        # Calculate composite score
        total_score = rsi_score + macd_score + ma_score + bb_score + stoch_score
        
        # Make decision based on composite score
        # Lower thresholds to make the system more responsive
        if total_score >= 1:
            return 'BUY'
        elif total_score <= -1:
            return 'SELL'
        else:
            return 'HOLD'
    
    except Exception as e:
        print(f"Error in quant-based decision: {e}")
        # Ultimate fallback to simple technical decision
        return simple_technical_decision(indicators)


def simple_technical_decision(indicators):
    """
    Fallback simple decision based on technical indicators
    """
    rsi = indicators.get('rsi', 50) or 50
    
    if rsi < 30:  # Oversold
        return 'BUY'
    elif rsi > 70:  # Overbought
        return 'SELL'
    else:  # Neutral
        return 'HOLD'