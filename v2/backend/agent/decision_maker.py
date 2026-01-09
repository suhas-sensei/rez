import openai
from datetime import datetime
from config import settings
from indicators.quant_indicator_calculator import calculate_indicators


def get_config():
    """Get config in the format expected by existing code"""
    return {
        'llm_api_key': settings.llm_api_key,
        'llm_base_url': settings.llm_base_url,
        'llm_model': settings.llm_model,
    }


def make_trading_decision(asset, indicators, portfolio_value, risk_profile="medium"):
    """
    Use AI to make a trading decision based on technical indicators and portfolio state
    Supports both OpenAI-compatible APIs and open source models
    """
    config = get_config()

    # Adjust prompt based on risk profile
    risk_guidance = {
        "low": "Be conservative. Only recommend BUY or SELL when indicators strongly agree. Prefer HOLD when uncertain.",
        "medium": "Take balanced approach. Trade when indicators show moderate agreement.",
        "high": "Be aggressive. Look for trading opportunities even with weaker signals. Prefer action over holding."
    }

    guidance = risk_guidance.get(risk_profile, risk_guidance["medium"])

    # Prepare the prompt for the LLM
    prompt = f"""
    You are an expert trading bot. Based on the following market data, make a trading decision.

    Current asset: {asset}
    Portfolio value: ${portfolio_value:,.2f}
    Risk Profile: {risk_profile.upper()}

    Current indicators:
    - RSI: {indicators['rsi']}
    - MACD value: {indicators['macd']['value']}
    - MACD signal: {indicators['macd']['signal']}
    - EMA: {indicators['ema']}
    - SMA: {indicators['sma']}
    - Bollinger Bands: Upper {indicators['bollinger_bands']['upper']},
                       Middle {indicators['bollinger_bands']['middle']},
                       Lower {indicators['bollinger_bands']['lower']}

    Trading guidance: {guidance}

    Please respond with ONLY ONE of these three words:
    1. "BUY" - if the indicators suggest going long
    2. "SELL" - if the indicators suggest going short
    3. "HOLD" - if the indicators suggest maintaining current position or being neutral

    Be concise and only respond with the single word decision.
    """

    # Configure the LLM client
    if config['llm_base_url']:
        client = openai.OpenAI(
            base_url=config['llm_base_url'],
            api_key=config['llm_api_key']
        )
    else:
        client = openai.OpenAI(
            base_url='https://api.openai.com/v1',
            api_key=config['llm_api_key']
        )

    try:
        response = client.chat.completions.create(
            model=config['llm_model'],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.1
        )

        decision = response.choices[0].message.content.strip().upper()

        if decision in ['BUY', 'SELL', 'HOLD', 'LONG', 'SHORT']:
            if decision == 'LONG':
                decision = 'BUY'
            elif decision == 'SHORT':
                decision = 'SELL'
            return decision
        else:
            return 'HOLD'

    except Exception as e:
        print(f"Error getting AI decision: {e}")
        return quant_based_decision(indicators, risk_profile)


def quant_based_decision(indicators, risk_profile="medium"):
    """
    Advanced fallback decision based on quant library calculations.
    Adjusts thresholds based on risk profile.
    """
    # Risk multipliers - higher risk = lower thresholds = more trades
    risk_multipliers = {
        "low": 1.5,      # Higher thresholds, fewer trades
        "medium": 1.0,   # Standard thresholds
        "high": 0.5      # Lower thresholds, more trades
    }
    risk_mult = risk_multipliers.get(risk_profile, 1.0)

    try:
        rsi = indicators.get('rsi', 50) or 50
        macd = indicators.get('macd', {'value': 0, 'signal': 0}) or {'value': 0, 'signal': 0}
        macd_value = macd.get('value', 0) or 0
        macd_signal = macd.get('signal', 0) or 0
        macd_histogram = macd.get('histogram', 0) or 0
        ema = indicators.get('ema', 0) or 0
        sma = indicators.get('sma', 0) or 0
        bb_data = indicators.get('bollinger_bands', {'upper': 0, 'middle': 0, 'lower': 0}) or {'upper': 0, 'middle': 0, 'lower': 0}
        current_price = indicators.get('current_price', 0) or 0
        bb_position = indicators.get('bb_position', 0.5) or 0.5
        bb_width = indicators.get('bb_width', 0) or 0
        stochastic_data = indicators.get('stochastic', {'k': 50, 'd': 50}) or {'k': 50, 'd': 50}
        stoch_k = stochastic_data.get('k', 50) or 50
        stoch_d = stochastic_data.get('d', 50) or 50
        volume = indicators.get('volume', 0) or 0

        trend_strength = abs(ema - sma) / current_price if current_price != 0 else 0
        volatility = bb_width / current_price if current_price != 0 and bb_width is not None else 0

        is_trending = trend_strength > 0.02
        is_volatile = volatility > 0.05
        has_momentum = abs(macd_histogram) > 0.001 * current_price

        rsi_score = 0
        macd_score = 0
        ma_score = 0
        bb_score = 0
        stoch_score = 0
        trend_factor = 1.0

        if is_trending:
            trend_factor = 1.5
        elif is_volatile and not is_trending:
            trend_factor = 0.8

        if rsi < 30:
            rsi_score = 1.5 if not is_trending else 1.0
        elif rsi < 40:
            rsi_score = 1.0 if not is_trending else 0.5
        elif rsi > 70:
            rsi_score = -1.5 if not is_trending else -1.0
        elif rsi > 60:
            rsi_score = -1.0 if not is_trending else -0.5

        if macd_value > macd_signal and has_momentum:
            macd_score = 1.2
        elif macd_value > macd_signal:
            macd_score = 0.8
        elif macd_value < macd_signal and has_momentum:
            macd_score = -1.2
        elif macd_value < macd_signal:
            macd_score = -0.8

        if current_price > ema and ema > sma:
            ma_score = 1.0 if is_trending else 0.5
        elif current_price < ema and ema < sma:
            ma_score = -1.0 if is_trending else -0.5

        if bb_position < 0.15 and not is_trending:
            bb_score = 1.5
        elif bb_position < 0.25 and not is_trending:
            bb_score = 1.0
        elif bb_position > 0.85 and not is_trending:
            bb_score = -1.5
        elif bb_position > 0.75 and not is_trending:
            bb_score = -1.0
        elif is_trending:
            if current_price > bb_data.get('upper', current_price) and ma_score > 0:
                bb_score = 0.8
            elif current_price < bb_data.get('lower', current_price) and ma_score < 0:
                bb_score = -0.8

        stoch_diff = stoch_k - stoch_d
        if stoch_k < 20 and stoch_diff > 5:
            stoch_score = 1.2
        elif stoch_k < 30 and stoch_diff > 0:
            stoch_score = 0.8
        elif stoch_k > 80 and stoch_diff < -5:
            stoch_score = -1.2
        elif stoch_k > 70 and stoch_diff < 0:
            stoch_score = -0.8

        rsi_score *= trend_factor
        macd_score *= trend_factor
        bb_score *= trend_factor
        stoch_score *= trend_factor

        total_score = rsi_score + macd_score + ma_score + bb_score + stoch_score

        bullish_signals = sum(1 for s in [rsi_score, macd_score, bb_score, stoch_score] if s > 0.5)
        bearish_signals = sum(1 for s in [rsi_score, macd_score, bb_score, stoch_score] if s < -0.5)
        agreement_level = max(bullish_signals, bearish_signals)

        if agreement_level >= 3:
            total_score *= 1.2
        elif agreement_level == 1:
            total_score *= 0.7

        if volume > 0:
            volume_factor = 1.1 if abs(total_score) > 0.5 else 1.0
            total_score *= volume_factor

        # Apply risk multiplier to thresholds
        base_buy_threshold = (1.2 if (is_volatile or is_trending) else 0.7) * risk_mult
        base_sell_threshold = (-1.2 if (is_volatile or is_trending) else -0.7) * risk_mult

        if agreement_level >= 3:
            buy_threshold = base_buy_threshold * 0.8
            sell_threshold = base_sell_threshold * 0.8
        elif agreement_level <= 1:
            buy_threshold = base_buy_threshold * 1.5
            sell_threshold = base_sell_threshold * 1.5
        else:
            buy_threshold = base_buy_threshold
            sell_threshold = base_sell_threshold

        if is_trending and ma_score != 0:
            trend_aligned = (total_score > 0 and ma_score > 0) or (total_score < 0 and ma_score < 0)
            if trend_aligned:
                buy_threshold *= 0.8
                sell_threshold *= 0.8

        if total_score >= buy_threshold:
            return 'BUY'
        elif total_score <= sell_threshold:
            return 'SELL'
        else:
            return 'HOLD'

    except Exception as e:
        print(f"Error in quant-based decision: {e}")
        return simple_technical_decision(indicators)


def simple_technical_decision(indicators):
    """
    Fallback simple decision based on technical indicators
    """
    rsi = indicators.get('rsi', 50) or 50

    if rsi < 30:
        return 'BUY'
    elif rsi > 70:
        return 'SELL'
    else:
        return 'HOLD'
