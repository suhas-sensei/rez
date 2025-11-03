import os
from dotenv import load_dotenv

def load_config():
    """Load configuration from environment variables"""
    load_dotenv()
    
    # Get basic config
    config = {
        'taapi_api_key': os.getenv('TAAPI_API_KEY'),
        'llm_api_key': os.getenv('LLM_API_KEY'),
        'llm_model': os.getenv('LLM_MODEL', 'openai/gpt-3.5-turbo'),  # Default to OpenAI, but allow other models
        'llm_base_url': os.getenv('LLM_BASE_URL'),  # For local models like Ollama
        'simulation_mode': os.getenv('SIMULATION_MODE', 'true').lower() == 'true',
        'starting_funds': float(os.getenv('STARTING_FUNDS', '1000.0')),
        'risk_per_trade': float(os.getenv('RISK_PER_TRADE', '0.02')),  # 2% risk per trade
    }
    
    # Add risk profile configuration
    risk_profile = os.getenv('RISK_PROFILE', 'medium').lower()
    config['risk_profile'] = risk_profile
    
    # Set risk profile defaults (more conservative to align with original algorithm)
    if risk_profile == 'low':
        config['default_stop_loss_percent'] = 0.08  # 8% for low risk (higher to avoid premature stops)
        config['default_position_size_limit'] = 0.01  # 1% max per trade
        config['default_risk_per_trade'] = 0.015  # 1.5% risk per trade
        config['kelly_fraction'] = 0.10  # More conservative
    elif risk_profile == 'high':
        config['default_stop_loss_percent'] = 0.15  # 15% for high risk (to allow more room)
        config['default_position_size_limit'] = 0.03  # 3% max per trade (not too aggressive)
        config['default_risk_per_trade'] = 0.025  # 2.5% risk per trade
        config['kelly_fraction'] = 0.20  # More moderate than original
    else:  # medium risk (default)
        config['default_stop_loss_percent'] = 0.12  # 12% for medium risk (more reasonable)
        config['default_position_size_limit'] = 0.02  # 2% max per trade
        config['default_risk_per_trade'] = 0.02  # 2% risk per trade (original default)
        config['kelly_fraction'] = 0.15  # More conservative than original
    
    # Allow custom overrides from environment variables
    custom_stop_loss = os.getenv('CUSTOM_STOP_LOSS')
    if custom_stop_loss:
        try:
            config['default_stop_loss_percent'] = float(custom_stop_loss) / 100.0
        except ValueError:
            pass  # Keep default if conversion fails
    
    custom_position_size = os.getenv('CUSTOM_POSITION_SIZE')
    if custom_position_size:
        try:
            config['default_position_size_limit'] = float(custom_position_size) / 100.0
        except ValueError:
            pass  # Keep default if conversion fails
    
    custom_risk_per_trade = os.getenv('CUSTOM_RISK_PER_TRADE')
    if custom_risk_per_trade:
        try:
            config['default_risk_per_trade'] = float(custom_risk_per_trade) / 100.0
        except ValueError:
            pass  # Keep default if conversion fails
    
    return config