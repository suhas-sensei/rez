import asyncio
import argparse
import os
import time
from datetime import datetime
import json
import sys
import os
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


def main():
    # Clear the log file to ensure fresh data for each run
    initialize_log_file()
    
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
    
    args = parser.parse_args()

    # Load configuration
    config = load_config()
    
    # Update config with command-line arguments if provided
    if args.stop_loss is not None:
        config['default_stop_loss_percent'] = args.stop_loss / 100.0
    if args.position_size_limit is not None:
        config['default_position_size_limit'] = args.position_size_limit / 100.0
    if args.risk_per_trade is not None:
        config['default_risk_per_trade'] = args.risk_per_trade / 100.0
    
    # Set risk profile
    config['risk_profile'] = args.risk_profile
    
    # Determine assets based on risk profile or user specification
    if args.assets is None:
        # Use risk profile to select assets
        print(f"Selecting assets based on {args.risk_profile} risk profile...")
        selected_assets = get_risk_appropriate_assets(args.risk_profile, count=6)  # Default to 6 assets
        args.assets = selected_assets
        print(f"Selected {len(selected_assets)} assets for {args.risk_profile} risk profile: {selected_assets}")
    else:
        # User specified assets, validate they align with risk profile
        print(f"Using user-specified assets: {args.assets}")
    
    # Initialize the simulation environment
    hyperliquid_api.initialize_simulation(starting_funds=args.starting_funds)
    
    print(f"Starting AI Trading Agent with ${args.starting_funds} in simulation mode")
    print(f"Risk profile: {args.risk_profile}")
    print(f"Trading assets: {args.assets}")
    print(f"Time interval: {args.interval}")
    
    # Get initial market data for all assets to make allocation decision
    print("Fetching initial market data for allocation...")
    initial_indicators_map = {}
    for asset in args.assets:
        print(f"Getting data for {asset}...")
        initial_indicators_map[asset] = get_technical_indicators(asset, args.interval)
        time.sleep(0.5)  # Small delay to prevent rate limiting
    
    # Make initial allocation decision if not already allocated
    if not hyperliquid_api.is_initial_allocation_done():
        print("Making initial allocation decision...")
        allocation_decision = make_initial_allocation_decision(args.assets, initial_indicators_map, args.starting_funds)
        print(f"Initial allocation decision: {allocation_decision}")
        
        # Execute the initial allocation
        allocation_result = hyperliquid_api.execute_initial_allocation_simulation(args.assets, allocation_decision)
        print(f"Initial allocation result: {allocation_result}")
    
    # Main trading loop (for simulation, we can run for a limited number of iterations)
    iterations = 0
    max_iterations = 100  # Limit iterations for demo purposes
    
    while iterations < max_iterations:
        try:
            for asset in args.assets:
                print(f"\n--- Iteration {iterations + 1}, Asset: {asset} ---")
                
                # Get technical indicators from TAAPI (for basic info)
                basic_indicators = get_technical_indicators(asset, args.interval)
                
                # Get historical data for advanced algorithm
                historical_data = get_historical_data(asset, args.interval, lookback_periods=50)
                
                # Get current portfolio state
                portfolio_value = hyperliquid_api.get_portfolio_value()
                
                # Make advanced trading decision using sophisticated algorithm
                advanced_decision = make_advanced_trading_decision(asset, historical_data, portfolio_value, risk_profile=args.risk_profile)
                decision = advanced_decision['decision']
                
                # Execute the decision in simulation
                result = hyperliquid_api.execute_trade_simulation(asset, decision)
                
                print(f"Decision: {decision}")
                print(f"Advanced Analysis: {advanced_decision['regime']} regime, confidence={advanced_decision['confidence']:.2f}")
                print(f"Result: {result}")
                
                # Log this trade to file for GUI with advanced analysis
                log_trade(asset, decision, result, portfolio_value, advanced_decision, args.risk_profile)
                
                # Small delay to prevent API rate limiting in simulation
                time.sleep(0.5)  # Reduced delay for faster execution
                
            iterations += 1
            time.sleep(2)  # Reduced wait time between cycles for more frequent trading
            
        except KeyboardInterrupt:
            print("\nStopping agent...")
            break
        except Exception as e:
            print(f"Error in trading loop: {e}")
            time.sleep(5)  # Wait before retrying

    print("\nFinal portfolio value:", hyperliquid_api.get_portfolio_value())


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
    with open('trades_log.jsonl', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


# Initialize log file at the start of each run
def initialize_log_file():
    """Clear the log file at the start of each run to show fresh data"""
    with open('trades_log.jsonl', 'w') as f:
        pass  # Just open and close to clear the file


if __name__ == "__main__":
    main()