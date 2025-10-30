import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_config
import openai
from datetime import datetime
from indicators.quant_indicator_calculator import get_quant_indicators

def make_initial_allocation_decision(assets, indicators_map, portfolio_value):
    """
    Use AI to make an initial allocation decision based on technical indicators of all assets
    Returns a dictionary with asset names as keys and allocation percentages as values
    """
    config = load_config()
    
    # Prepare the prompt for the LLM with all asset data
    assets_data = ""
    for asset in assets:
        if asset in indicators_map:
            indicators = indicators_map[asset]
            assets_data += f"\n{asset}: RSI: {indicators['rsi']}, MACD: {indicators['macd']['value']}, EMA: {indicators['ema']}, SMA: {indicators['sma']}\n"
    
    prompt = f"""
    You are an expert portfolio allocation bot. Based on the following market data for multiple assets, 
    create an initial allocation strategy for a portfolio starting with ${portfolio_value:,.2f}.
    
    Assets and their indicators:
    {assets_data}
    
    Current time: {datetime.now().isoformat()}
    
    Please allocate the portfolio among these assets based on their technical indicators.
    The sum of all allocation percentages should equal 1.0 (100%).
    
    Return a JSON object with asset names as keys and allocation percentages as values.
    For example: {{"BTC": 0.4, "ETH": 0.3, "SOL": 0.2, "AVAX": 0.1}}
    
    Only respond with the JSON object and nothing else.
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
            max_tokens=200,
            temperature=0.3  # Slightly higher temperature for creative allocation
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Extract JSON from response (in case there's extra text)
        import json
        import re
        
        # Look for JSON in the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            allocation = json.loads(json_str)
            
            # Validate that all keys are in our assets list and sum is approximately 1.0
            total_allocation = sum(allocation.values())
            if abs(total_allocation - 1.0) < 0.1:  # Allow some variance due to rounding
                # Ensure all assets in the original list are represented
                final_allocation = {}
                for asset in assets:
                    final_allocation[asset] = allocation.get(asset, 0.0)
                
                # Normalize if needed so the total is exactly 1.0
                actual_sum = sum(final_allocation.values())
                if actual_sum > 0:
                    for asset in final_allocation:
                        final_allocation[asset] = final_allocation[asset] / actual_sum
                
                return final_allocation
            else:
                # Fallback to equal allocation if the response doesn't sum to 1
                equal_pct = 1.0 / len(assets) if len(assets) > 0 else 0
                return {asset: equal_pct for asset in assets}
        else:
            # Fallback to equal allocation if no JSON found
            equal_pct = 1.0 / len(assets) if len(assets) > 0 else 0
            return {asset: equal_pct for asset in assets}
            
    except Exception as e:
        print(f"Error getting AI allocation decision: {e}")
        # Fallback to equal allocation if AI fails
        equal_pct = 1.0 / len(assets) if len(assets) > 0 else 0
        return {asset: equal_pct for asset in assets}