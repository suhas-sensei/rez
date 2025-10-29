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
    This function uses multiple technical indicators to make more nuanced decisions
    with market regime awareness and better risk management.
    """
    try:
        # Extract key indicators with safe access
        rsi = indicators.get('rsi', 50) or 50
        macd = indicators.get('macd', {'value': 0, 'signal': 0}) or {'value': 0, 'signal': 0}
        macd_value = macd.get('value', 0) or 0
        macd_signal = macd.get('signal', 0) or 0
        macd_histogram = macd.get('histogram', 0) or 0  # Added to detect momentum
        ema = indicators.get('ema', 0) or 0
        sma = indicators.get('sma', 0) or 0
        bb_data = indicators.get('bollinger_bands', {'upper': 0, 'middle': 0, 'lower': 0}) or {'upper': 0, 'middle': 0, 'lower': 0}
        current_price = indicators.get('current_price', 0) or 0
        bb_position = indicators.get('bb_position', 0.5) or 0.5  # Position within BB (0-1)
        bb_width = indicators.get('bb_width', 0) or 0  # Width of BB bands
        stochastic_data = indicators.get('stochastic', {'k': 50, 'd': 50}) or {'k': 50, 'd': 50}
        stoch_k = stochastic_data.get('k', 50) or 50
        stoch_d = stochastic_data.get('d', 50) or 50
        volume = indicators.get('volume', 0) or 0
        
        # Calculate market regime indicators
        trend_strength = abs(ema - sma) / current_price  # Normalized trend strength
        volatility = bb_width / current_price  # Price volatility measure
        macd_momentum = abs(macd_histogram)  # Momentum strength
        
        # Determine market regime
        is_trending = trend_strength > 0.02  # More than 2% difference suggests trend
        is_volatile = volatility > 0.05  # More than 5% BB width suggests volatility
        has_momentum = abs(macd_histogram) > 0.001 * current_price  # Significant momentum
        
        # Initialize scores
        rsi_score = 0
        macd_score = 0
        ma_score = 0
        bb_score = 0
        stoch_score = 0
        trend_factor = 1.0  # Factor to adjust scores based on market regime
        
        # Adjust strategy based on market regime
        if is_trending:
            # In trending markets, favor momentum-following signals
            trend_factor = 1.5
        elif is_volatile and not is_trending:
            # In volatile but non-trending markets, favor mean reversion
            trend_factor = 0.8
        else:
            # In stable markets, use standard scoring
            trend_factor = 1.0
        
        # RSI Analysis - Adjusted with market regime awareness
        if rsi < 30:  # Strong oversold - BUY signal (stronger in ranging markets)
            rsi_score = 1.5 if not is_trending else 1.0
        elif rsi < 40:  # Mild oversold - BUY signal
            rsi_score = 1.0 if not is_trending else 0.5
        elif rsi > 70:  # Strong overbought - SELL signal
            rsi_score = -1.5 if not is_trending else -1.0
        elif rsi > 60:  # Mild overbought - SELL signal
            rsi_score = -1.0 if not is_trending else -0.5
        
        # MACD Analysis - Consider histogram for momentum
        if macd_value > macd_signal and has_momentum:  # Bullish crossover with momentum
            macd_score = 1.2
        elif macd_value > macd_signal:  # Bullish crossover without momentum
            macd_score = 0.8
        elif macd_value < macd_signal and has_momentum:  # Bearish crossover with momentum
            macd_score = -1.2
        elif macd_value < macd_signal:  # Bearish crossover without momentum
            macd_score = -0.8
        
        # Moving Average Analysis - Consider trend strength
        if current_price > ema and ema > sma:  # Bullish trend
            ma_score = 1.0 if is_trending else 0.5
        elif current_price < ema and ema < sma:  # Bearish trend
            ma_score = -1.0 if is_trending else -0.5
        # When MA signals conflict with other indicators, reduce confidence
        
        # Bollinger Bands Analysis - More nuanced approach
        if bb_position < 0.15 and not is_trending:  # Deep oversold in ranging market - BUY
            bb_score = 1.5
        elif bb_position < 0.25 and not is_trending:  # Oversold in ranging market - BUY
            bb_score = 1.0
        elif bb_position > 0.85 and not is_trending:  # Deep overbought in ranging market - SELL
            bb_score = -1.5
        elif bb_position > 0.75 and not is_trending:  # Overbought in ranging market - SELL
            bb_score = -1.0
        elif is_trending:  # In trending markets, touching bands might be continuation signals
            if current_price > bb_data.get('upper', current_price) and ma_score > 0:  # Breaking out in uptrend - BUY
                bb_score = 0.8
            elif current_price < bb_data.get('lower', current_price) and ma_score < 0:  # Breaking out in downtrend - SELL
                bb_score = -0.8
        
        # Stochastic Analysis - Consider crossover and momentum
        stoch_diff = stoch_k - stoch_d
        if stoch_k < 20 and stoch_diff > 5:  # Oversold with bullish momentum
            stoch_score = 1.2
        elif stoch_k < 30 and stoch_diff > 0:  # Mildly oversold with bullish bias
            stoch_score = 0.8
        elif stoch_k > 80 and stoch_diff < -5:  # Overbought with bearish momentum
            stoch_score = -1.2
        elif stoch_k > 70 and stoch_diff < 0:  # Mildly overbought with bearish bias
            stoch_score = -0.8
        
        # Adjust scores based on market regime
        rsi_score *= trend_factor
        macd_score *= trend_factor
        bb_score *= trend_factor
        stoch_score *= trend_factor
        
        # Apply risk management - if indicators conflict significantly, reduce trading aggressiveness
        total_score = rsi_score + macd_score + ma_score + bb_score + stoch_score
        
        # Calculate consensus level - how many indicators agree
        bullish_signals = sum(1 for s in [rsi_score, macd_score, bb_score, stoch_score] if s > 0.5)
        bearish_signals = sum(1 for s in [rsi_score, macd_score, bb_score, stoch_score] if s < -0.5)
        agreement_level = max(bullish_signals, bearish_signals)
        
        # Adjust score based on agreement level (confidence in signal)
        if agreement_level >= 3:  # Strong agreement
            total_score *= 1.2
        elif agreement_level == 1:  # Weak agreement
            total_score *= 0.7
        
        # Apply volume confirmation if available (higher volume confirms trends)
        if volume > 0:
            volume_factor = 1.1 if abs(total_score) > 0.5 else 1.0
            total_score *= volume_factor
        
        # Make final decision with dynamic thresholds based on market conditions
        # In volatile/trending markets, require stronger signals but also consider trend-following
        base_buy_threshold = 1.2 if (is_volatile or is_trending) else 0.7
        base_sell_threshold = -1.2 if (is_volatile or is_trending) else -0.7
        
        # Adjust thresholds based on agreement level
        if agreement_level >= 3:  # Strong agreement
            buy_threshold = base_buy_threshold * 0.8  # Lower threshold when indicators agree
            sell_threshold = base_sell_threshold * 0.8
        elif agreement_level <= 1:  # Weak agreement
            buy_threshold = base_buy_threshold * 1.5  # Higher threshold when indicators disagree
            sell_threshold = base_sell_threshold * 1.5
        else:  # Moderate agreement
            buy_threshold = base_buy_threshold
            sell_threshold = base_sell_threshold
        
        # In trending markets, be more willing to follow the trend if momentum aligns
        if is_trending and ma_score != 0:
            trend_aligned = (total_score > 0 and ma_score > 0) or (total_score < 0 and ma_score < 0)
            if trend_aligned:
                # Reduce threshold by 20% if we're aligned with the trend
                buy_threshold *= 0.8
                sell_threshold *= 0.8
        
        # Final decision
        if total_score >= buy_threshold:
            return 'BUY'
        elif total_score <= sell_threshold:
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