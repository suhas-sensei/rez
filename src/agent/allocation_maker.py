"""
Advanced Allocation Maker
Makes sophisticated initial allocation decisions using multi-asset analysis
"""
import os
import sys
import json
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_config
import openai
from datetime import datetime
from indicators.historical_data_fetcher import get_historical_data
from agent.advanced_decision_maker import AdvancedTradingAlgorithm

def make_advanced_initial_allocation_decision(assets, portfolio_value):
    """
    Use advanced algorithm to make an initial allocation decision based on comprehensive analysis
    """
    config = load_config()
    
    # Get historical data for all assets to run advanced analysis
    advanced_analyses = {}
    for asset in assets:
        try:
            historical_data = get_historical_data(asset, interval='1h', lookback_periods=50)
            algo = AdvancedTradingAlgorithm()
            indicators = algo.calculate_advanced_indicators(historical_data)
            signals = algo.generate_advanced_signals(indicators, asset, portfolio_value)
            
            advanced_analyses[asset] = {
                'indicators': indicators,
                'signals': signals,
                'regime': signals['regime'],
                'confidence': signals['confidence'],
                'combined_signal': signals['combined_signal']
            }
        except Exception as e:
            print(f"Error analyzing {asset} for allocation: {e}")
            # Fallback to simple analysis
            from indicators.quant_indicator_calculator import get_quant_indicators
            indicators = get_quant_indicators(asset, interval='1h', mock_data=True)
            advanced_analyses[asset] = {
                'indicators': indicators,
                'signals': {'regime': 'unknown', 'confidence': 0.3, 'combined_signal': 0},
                'regime': 'unknown',
                'confidence': 0.3,
                'combined_signal': 0
            }
    
    # Prepare comprehensive analysis data
    assets_data = ""
    for asset in assets:
        analysis = advanced_analyses[asset]
        regime = analysis['regime']
        confidence = analysis['confidence']
        combined_signal = analysis['combined_signal']
        rsi = analysis['indicators']['rsi']
        volatility = analysis['indicators']['volatility']
        hurst = analysis['indicators'].get('hurst_exponent', 0.5)
        
        assets_data += f"""
{asset}: 
  - Market Regime: {regime}
  - Signal Confidence: {confidence:.2f}
  - Combined Signal: {combined_signal:.2f}
  - RSI: {rsi:.2f} (0-100, 30=oversold, 70=overbought)  
  - Volatility: {volatility:.4f}
  - Hurst Exponent: {hurst:.2f} (0.5=random, >0.5=trending, <0.5=mean-reverting)
  - Current Price: ${analysis['indicators']['current_price']:.2f}
        """
    
    # Create a more sophisticated prompt for allocation
    prompt = f"""
    You are an expert portfolio allocation bot with advanced quantitative finance knowledge. 
    Based on the following comprehensive market analysis for {len(assets)} assets, 
    create an optimal initial allocation strategy for a portfolio starting with ${portfolio_value:,.2f}.
    
    Market analysis for each asset:
    {assets_data}
    
    Consider the following factors for allocation:
    1. Market regime of each asset (trending assets might get higher allocation in uptrends)
    2. Signal confidence (higher confidence assets get higher allocation)
    3. Combined signal strength (positive signals get higher allocation)
    4. Risk-adjusted returns (consider volatility relative to expected returns)
    5. Market efficiency (assets with mean-reverting characteristics may need different treatment)
    6. Diversification across different market regimes
    
    Current time: {datetime.now().isoformat()}
    
    Please allocate the portfolio among these assets based on their advanced technical analysis.
    The sum of all allocation percentages should equal 1.0 (100%).
    Use risk-adjusted sizing principles and consider the current market regime.
    
    Return a JSON object with asset names as keys and allocation percentages as values.
    Example: {{"BTC": 0.4, "ETH": 0.3, "SOL": 0.2, "AVAX": 0.1}}
    
    Only respond with the JSON object and nothing else.
    """
    
    # Configure the LLM client
    if config['llm_base_url']:
        client = openai.OpenAI(
            base_url=config['llm_base_url'],
            api_key=config['llm_api_key']
        )
    else:
        client = openai.OpenAI(
            base_url=config.get('llm_base_url', 'https://api.openai.com/v1'),
            api_key=config['llm_api_key']
        )
    
    try:
        response = client.chat.completions.create(
            model=config['llm_model'],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.4  # Slightly higher for more nuanced allocation
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            allocation = json.loads(json_str)
            
            # Validate and normalize allocation
            total_allocation = sum(allocation.values())
            if 0.8 <= total_allocation <= 1.2:  # Allow some variance
                # Ensure all assets in the original list are represented
                final_allocation = {}
                for asset in assets:
                    final_allocation[asset] = allocation.get(asset, 0.0)
                
                # Normalize to exactly 1.0
                actual_sum = sum(final_allocation.values())
                if actual_sum > 0:
                    for asset in final_allocation:
                        final_allocation[asset] = final_allocation[asset] / actual_sum
                
                return final_allocation
            else:
                # Fallback to risk-weighted allocation based on analysis
                return _calculate_risk_weighted_allocation(advanced_analyses, assets)
        else:
            # Fallback to risk-weighted allocation
            return _calculate_risk_weighted_allocation(advanced_analyses, assets)
            
    except Exception as e:
        print(f"Error getting AI allocation decision: {e}")
        # Fallback to risk-weighted allocation
        return _calculate_risk_weighted_allocation(advanced_analyses, assets)


def _calculate_risk_weighted_allocation(advanced_analyses, assets):
    """
    Calculate allocation based on quantitative analysis without LLM
    """
    allocations = {}
    
    # Extract scores for each asset based on our advanced analysis
    asset_scores = {}
    total_score = 0
    
    for asset in assets:
        analysis = advanced_analyses[asset]
        indicators = analysis['indicators']
        
        # Calculate a comprehensive score for each asset
        # Higher score = more allocation
        
        # Signal strength (absolute value, higher is better for allocation)
        signal_strength = abs(analysis['combined_signal']) * analysis['confidence']
        
        # Momentum score (based on ROC and other momentum indicators)
        momentum_score = abs(indicators.get('roc', 0)) * 10  # Scale up for impact
        
        # Trend strength score
        trend_score = 0
        hurst = indicators.get('hurst_exponent', 0.5)
        if hurst > 0.6:  # Trending asset
            trend_score = 0.3
        elif hurst < 0.4:  # Mean-reverting asset (could be good for active trading)
            trend_score = 0.2
        else:  # Neutral
            trend_score = 0.1
        
        # Normalize by volatility (inverse relationship - less volatile = higher allocation)
        vol_score = max(0.1, 1.0 - indicators.get('volatility', 0.02) / 0.1)  # Cap at 0.1
        
        # RSI score (not too overbought or oversold)
        rsi = indicators.get('rsi', 50)
        rsi_score = 1.0 - abs(rsi - 50) / 50  # Score between 0 and 1
        
        # Combine scores
        asset_score = (
            signal_strength * 0.3 +
            momentum_score * 0.2 +
            trend_score * 0.2 +
            vol_score * 0.15 +
            rsi_score * 0.15
        )
        
        asset_scores[asset] = asset_score
        total_score += asset_score
    
    # Convert scores to allocations
    if total_score > 0:
        for asset in assets:
            allocations[asset] = asset_scores[asset] / total_score
    else:
        # Equal allocation if no valid scores
        equal_pct = 1.0 / len(assets) if len(assets) > 0 else 0
        allocations = {asset: equal_pct for asset in assets}
    
    return allocations


def make_initial_allocation_decision(assets, indicators_map, portfolio_value):
    """
    Use advanced algorithm to make initial allocation decision
    """
    return make_advanced_initial_allocation_decision(assets, portfolio_value)