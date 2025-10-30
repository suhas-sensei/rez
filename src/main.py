import asyncio
import argparse
import os
import time
from datetime import datetime
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agent.decision_maker import make_trading_decision
from agent.allocation_maker import make_initial_allocation_decision
from indicators.taapi_client import get_technical_indicators
from trading import hyperliquid_api  # This will be our simulation layer
from config_loader import load_config


def main():
    parser = argparse.ArgumentParser(description='AI Trading Agent with Simulation')
    parser.add_argument('--assets', nargs='+', default=['BTC', 'ETH'], help='Assets to trade')
    parser.add_argument('--interval', default='1h', help='Trading interval')
    parser.add_argument('--starting-funds', type=float, default=1000.0, help='Starting simulated funds')
    args = parser.parse_args()

    # Load configuration
    config = load_config()
    
    # Initialize the simulation environment
    hyperliquid_api.initialize_simulation(starting_funds=args.starting_funds)
    
    print(f"Starting AI Trading Agent with ${args.starting_funds} in simulation mode")
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
                
                # Get technical indicators from TAAPI
                indicators = get_technical_indicators(asset, args.interval)
                
                # Get current portfolio state
                portfolio_value = hyperliquid_api.get_portfolio_value()
                
                # Make trading decision using AI
                decision = make_trading_decision(asset, indicators, portfolio_value)
                
                # Execute the decision in simulation
                result = hyperliquid_api.execute_trade_simulation(asset, decision)
                
                print(f"Decision: {decision}")
                print(f"Result: {result}")
                
                # Log this trade to file for GUI
                log_trade(asset, decision, result, portfolio_value)
                
                # Small delay to prevent API rate limiting in simulation
                time.sleep(1)
                
            iterations += 1
            time.sleep(5)  # Wait between cycles
            
        except KeyboardInterrupt:
            print("\nStopping agent...")
            break
        except Exception as e:
            print(f"Error in trading loop: {e}")
            time.sleep(5)  # Wait before retrying

    print("\nFinal portfolio value:", hyperliquid_api.get_portfolio_value())


def log_trade(asset, decision, result, portfolio_value):
    """Log trade data for GUI visualization"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "asset": asset,
        "decision": decision,
        "result": result,
        "portfolio_value": portfolio_value
    }
    
    # Append to trades log file
    with open('trades_log.jsonl', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


if __name__ == "__main__":
    main()