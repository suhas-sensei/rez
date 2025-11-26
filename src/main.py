import asyncio
import argparse
import os
import time
from datetime import datetime, timedelta
import json
import sys
import os
import threading
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the new risk management modules
from risk_management.asset_classification import get_risk_appropriate_assets
from agent.decision_maker import make_trading_decision
from agent.advanced_decision_maker import make_advanced_trading_decision
from agent.allocation_maker import make_initial_allocation_decision
from indicators.taapi_client import get_technical_indicators
from indicators.historical_data_fetcher import get_historical_data
from trading import hyperliquid_api  # This will be our simulation layer
from config_loader import load_config

# Global stop event for trading sessions
trading_stop_event = threading.Event()


def run_trading_session(risk_profile='medium', starting_funds=1000.0, trading_duration_minutes=60, assets=None):
    """
    Run a trading session with specified parameters
    :param risk_profile: low, medium, or high
    :param starting_funds: initial balance for the portfolio
    :param trading_duration_minutes: how long to run the trading simulation in minutes
    :param assets: optional list of assets to trade, if None will be selected based on risk profile
    :return: final portfolio value
    """
    # Clear the log file to ensure fresh data for each run
    initialize_log_file()
    
    # Load configuration
    config = load_config()
    
    # Update config with provided parameters
    config['risk_profile'] = risk_profile
    
    # Determine assets based on risk profile or user specification
    if assets is None:
        # Use risk profile to select assets
        print(f"Selecting assets based on {risk_profile} risk profile...")
        selected_assets = get_risk_appropriate_assets(risk_profile, count=6)  # Default to 6 assets
        assets = selected_assets
        print(f"Selected {len(selected_assets)} assets for {risk_profile} risk profile: {selected_assets}")
    else:
        # User specified assets, validate they align with risk profile
        print(f"Using user-specified assets: {assets}")
    
    # Initialize the simulation environment
    hyperliquid_api.initialize_simulation(starting_funds=starting_funds)
    
    print(f"Starting AI Trading Agent with ${starting_funds} in simulation mode")
    print(f"Risk profile: {risk_profile}")
    print(f"Trading assets: {assets}")
    print(f"Time interval: 1h")
    print(f"Duration: {trading_duration_minutes} minutes")
    
    # Get initial market data for all assets to make allocation decision
    print("Fetching initial market data for allocation...")
    initial_indicators_map = {}
    for asset in assets:
        print(f"Getting data for {asset}...")
        initial_indicators_map[asset] = get_technical_indicators(asset, '1h')
        time.sleep(0.5)  # Small delay to prevent rate limiting
    
    # Make initial allocation decision if not already allocated
    if not hyperliquid_api.is_initial_allocation_done():
        print("Making initial allocation decision...")
        allocation_decision = make_initial_allocation_decision(assets, initial_indicators_map, starting_funds)
        print(f"Initial allocation decision: {allocation_decision}")
        
        # Execute the initial allocation
        allocation_result = hyperliquid_api.execute_initial_allocation_simulation(assets, allocation_decision)
        print(f"Initial allocation result: {allocation_result}")
    
    # Main trading loop (run for the specified duration)
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=trading_duration_minutes)
    
    iteration = 0
    while datetime.now() < end_time and not trading_stop_event.is_set():
        try:
            for asset in assets:
                current_time = datetime.now()
                if current_time >= end_time or trading_stop_event.is_set():
                    break
                
                print(f"\n--- Iteration {iteration + 1}, Asset: {asset}, Time: {current_time.strftime('%H:%M:%S')} ---")
                
                # Get technical indicators from TAAPI (for basic info)
                basic_indicators = get_technical_indicators(asset, '1h')
                
                # Get historical data for advanced algorithm
                historical_data = get_historical_data(asset, '1h', lookback_periods=50)
                
                # Get current portfolio state
                portfolio_value = hyperliquid_api.get_portfolio_value()
                
                # Make advanced trading decision using sophisticated algorithm
                advanced_decision = make_advanced_trading_decision(asset, historical_data, portfolio_value, risk_profile=risk_profile)
                decision = advanced_decision['decision']
                
                # Execute the decision in simulation
                result = hyperliquid_api.execute_trade_simulation(asset, decision)
                
                print(f"Decision: {decision}")
                print(f"Advanced Analysis: {advanced_decision['regime']} regime, confidence={advanced_decision['confidence']:.2f}")
                print(f"Result: {result}")
                
                # Log this trade to file for GUI with advanced analysis
                log_trade(asset, decision, result, portfolio_value, advanced_decision, risk_profile)
                
                # Small delay to prevent API rate limiting in simulation
                time.sleep(0.5)  # Reduced delay for faster execution
                
                # Check if stop event has been set
                if trading_stop_event.is_set():
                    break
                
            iteration += 1
            if not trading_stop_event.is_set():
                time.sleep(2)  # Reduced wait time between cycles for more frequent trading
            
        except KeyboardInterrupt:
            print("\nStopping agent...")
            break
        except Exception as e:
            print(f"Error in trading loop: {e}")
            time.sleep(5)  # Wait before retrying
            # Check if stop event has been set after an error
            if trading_stop_event.is_set():
                break

    # Clear the stop event after the trading session ends
    trading_stop_event.clear()
    final_value = hyperliquid_api.get_portfolio_value()
    print(f"\nFinal portfolio value after {trading_duration_minutes} minutes: ${final_value}")
    return final_value


def stop_trading_session():
    """
    Signal the trading session to stop
    """
    trading_stop_event.set()


def main():
    parser = argparse.ArgumentParser(description='AI Trading Agent with Simulation')
    parser.add_argument('--assets', nargs='+', default=None, help='Assets to trade (if not using risk profile)')
    parser.add_argument('--interval', default='1h', help='Trading interval')
    parser.add_argument('--starting-funds', type=float, default=1000.0, help='Starting simulated funds')
    parser.add_argument('--risk-profile', choices=['low', 'medium', 'high'], default='medium', 
                        help='Risk profile for trading (low, medium, high)')
    parser.add_argument('--stop-loss', type=float, 
                        help='Custom stop-loss percentage (overrides profile default)')
    parser.add_argument('--position-size-limit', type=float, 
                        help='Custom position size limit as percentage (overrides profile default)')
    parser.add_argument('--risk-per-trade', type=float, 
                        help='Custom risk percentage per trade (overrides profile default)')
    parser.add_argument('--take-profit', type=float, 
                        help='Custom take-profit percentage')
    parser.add_argument('--duration', type=int, default=60, help='Trading duration in minutes')
    
    args = parser.parse_args()

    # Call the new function with command line arguments
    final_value = run_trading_session(
        risk_profile=args.risk_profile,
        starting_funds=args.starting_funds,
        trading_duration_minutes=args.duration,
        assets=args.assets
    )
    
    print("\nFinal portfolio value:", final_value)


def log_trade(asset, decision, result, portfolio_value, advanced_decision=None, risk_profile=None):
    """Log trade data for GUI visualization"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "asset": asset,
        "decision": decision,
        "result": result,
        "portfolio_value": portfolio_value
    }
    
    # Add risk profile information
    if risk_profile:
        log_entry['risk_profile'] = risk_profile
    
    # Add advanced decision data if available
    if advanced_decision:
        log_entry['advanced_analysis'] = {
            'regime': advanced_decision.get('regime', 'unknown'),
            'confidence': advanced_decision.get('confidence', 0),
            'combined_signal': advanced_decision.get('combined_signal', 0),
            'strength': advanced_decision.get('strength', 'unknown'),
            'position_size': advanced_decision.get('position_size', 0)
        }
    
    # Append to trades log file - only for the active session
    # Use a configurable log file name with default fallback
    import os
    log_file_name = os.environ.get('TRADES_LOG_FILE', 'trade_log/trades_log.jsonl')
    with open(log_file_name, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


# Initialize log file at the start of each run
def initialize_log_file():
    """Clear the log file at the start of each run to show fresh data"""
    import os
    log_file_name = os.environ.get('TRADES_LOG_FILE', 'trade_log/trades_log.jsonl')
    with open(log_file_name, 'w') as f:
        pass  # Just open and close to clear the file


if __name__ == "__main__":
    main()