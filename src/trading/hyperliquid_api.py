import random
import time
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_config

# Global variables to track simulation state
simulation_state = {
    'portfolio_value': 1000.0,
    'positions': {},
    'trade_history': [],
    'initialized': False,
    'initial_allocation_done': False  # Track if initial allocation has been performed
}

def initialize_simulation(starting_funds=None):
    """Initialize the simulation environment"""
    global simulation_state
    
    if starting_funds is not None:
        simulation_state['portfolio_value'] = starting_funds
    else:
        config = load_config()
        simulation_state['portfolio_value'] = config['starting_funds']
    
    simulation_state['positions'] = {}
    simulation_state['trade_history'] = []
    simulation_state['initialized'] = True
    simulation_state['initial_allocation_done'] = False  # Reset allocation status
    
    print(f"Simulation initialized with ${simulation_state['portfolio_value']:.2f}")

def get_portfolio_value():
    """Get the current simulated portfolio value"""
    return simulation_state['portfolio_value']

def is_initial_allocation_done():
    """Check if initial allocation has been completed"""
    return simulation_state.get('initial_allocation_done', False)

def mark_initial_allocation_done():
    """Mark that initial allocation has been completed"""
    simulation_state['initial_allocation_done'] = True

def execute_trade_simulation(asset, decision):
    """
    Execute a simulated trade based on the AI decision
    This function now properly handles individual assets and updates positions accordingly
    """
    global simulation_state
    
    if not simulation_state['initialized']:
        initialize_simulation()
    
    # Record initial state
    initial_portfolio = simulation_state['portfolio_value']
    
    # Get current position in this asset
    current_position = simulation_state['positions'].get(asset, {'size': 0, 'entry_price': 0, 'usd_value': 0})
    current_usd_value = current_position.get('usd_value', 0)
    current_size = current_position.get('size', 0)
    
    # Simulate price change for this specific asset
    if decision.lower() in ['buy', 'long']:
        # Simulate buying: increase value of this asset based on market movement
        profit_factor = random.uniform(0.98, 1.03)  # -2% to +3% change
        new_asset_value = current_usd_value * profit_factor
        
        # Update the position
        simulation_state['positions'][asset] = {
            'size': current_size * profit_factor,  # Adjust size proportionally
            'entry_price': current_position.get('entry_price', 1) * profit_factor,  # Update price
            'usd_value': new_asset_value
        }
        
    elif decision.lower() in ['sell', 'short']:
        # Simulate selling: decrease value of this asset based on market movement
        profit_factor = random.uniform(0.97, 1.02)  # -3% to +2% change
        new_asset_value = current_usd_value * profit_factor
        
        # Update the position
        simulation_state['positions'][asset] = {
            'size': current_size * profit_factor,
            'entry_price': current_position.get('entry_price', 1) * profit_factor,
            'usd_value': new_asset_value
        }
        
    elif decision.lower() == 'hold':
        # Hold position: minimal change for this asset
        profit_factor = random.uniform(0.995, 1.005)  # -0.5% to +0.5% change
        new_asset_value = current_usd_value * profit_factor
        
        # Update position with minimal change
        simulation_state['positions'][asset] = {
            'size': current_size * profit_factor,
            'entry_price': current_position.get('entry_price', 1) * profit_factor,
            'usd_value': new_asset_value
        }
    else:
        # Unknown decision, minimal change
        profit_factor = random.uniform(0.998, 1.002)  # -0.2% to +0.2% change
        new_asset_value = current_usd_value * profit_factor
        
        # Update position
        simulation_state['positions'][asset] = {
            'size': current_size * profit_factor,
            'entry_price': current_position.get('entry_price', 1) * profit_factor,
            'usd_value': new_asset_value
        }
    
    # Calculate total portfolio value based on all positions
    total_value = simulation_state.get('cash', 0)  # Start with cash
    for asset_name, position in simulation_state['positions'].items():
        total_value += position.get('usd_value', 0)
    
    simulation_state['portfolio_value'] = total_value
    
    # Calculate PnL
    pnl = simulation_state['portfolio_value'] - initial_portfolio
    pnl_percentage = (pnl / initial_portfolio) * 100 if initial_portfolio > 0 else 0
    
    # Create trade record
    trade_record = {
        'timestamp': datetime.now().isoformat(),
        'asset': asset,
        'decision': decision,
        'initial_portfolio': initial_portfolio,
        'final_portfolio': simulation_state['portfolio_value'],
        'pnl': pnl,
        'pnl_percentage': pnl_percentage
    }
    
    simulation_state['trade_history'].append(trade_record)
    
    result = {
        'status': 'success',
        'executed_decision': decision,
        'initial_portfolio': initial_portfolio,
        'final_portfolio': simulation_state['portfolio_value'],
        'pnl': pnl,
        'pnl_percentage': pnl_percentage,
        'timestamp': trade_record['timestamp']
    }
    
    return result

def execute_initial_allocation_simulation(assets, allocation_data):
    """
    Execute initial asset allocation based on allocation percentages
    """
    global simulation_state
    
    if not simulation_state['initialized']:
        initialize_simulation()
    
    initial_portfolio = simulation_state['portfolio_value']
    remaining_portfolio = initial_portfolio
    
    for asset in assets:
        if asset in allocation_data:
            allocation_percentage = allocation_data[asset]
            allocation_amount = initial_portfolio * allocation_percentage
            
            # Update position for this asset
            if asset not in simulation_state['positions']:
                simulation_state['positions'][asset] = {
                    'size': allocation_amount,
                    'entry_price': 1.0,  # Using 1.0 as base price for simulation
                    'usd_value': allocation_amount
                }
            else:
                simulation_state['positions'][asset]['size'] += allocation_amount
                simulation_state['positions'][asset]['usd_value'] += allocation_amount
            
            # Deduct from remaining portfolio
            remaining_portfolio -= allocation_amount
    
    # Store remaining as cash
    simulation_state['cash'] = remaining_portfolio
    simulation_state['portfolio_value'] = initial_portfolio  # Total value remains the same
    
    # Record initial allocation trade
    trade_record = {
        'timestamp': datetime.now().isoformat(),
        'asset': 'INITIAL_ALLOCATION',
        'decision': 'ALLOCATE',
        'initial_portfolio': initial_portfolio,
        'final_portfolio': initial_portfolio,
        'pnl': 0,
        'pnl_percentage': 0,
        'allocation_breakdown': allocation_data
    }
    
    simulation_state['trade_history'].append(trade_record)
    mark_initial_allocation_done()
    
    result = {
        'status': 'success',
        'executed_decision': 'ALLOCATE',
        'initial_portfolio': initial_portfolio,
        'final_portfolio': initial_portfolio,
        'pnl': 0,
        'pnl_percentage': 0,
        'allocation_breakdown': allocation_data,
        'timestamp': trade_record['timestamp']
    }
    
    print(f"Initial allocation completed: {allocation_data}")
    return result


def get_position(asset):
    """Get the current position for an asset"""
    return simulation_state['positions'].get(asset, {'size': 0, 'entry_price': 0})

def get_trade_history():
    """Get the history of all trades"""
    return simulation_state['trade_history']

def get_cash_balance():
    """Get the current cash balance"""
    return simulation_state.get('cash', simulation_state['portfolio_value'])

def get_portfolio_allocation():
    """Get the current portfolio allocation by asset"""
    total_value = simulation_state['portfolio_value']
    if total_value <= 0:
        return {}
    
    allocation = {}
    positions = simulation_state['positions']
    
    for asset, position in positions.items():
        if 'usd_value' in position:
            allocation[asset] = position['usd_value'] / total_value
        else:
            # Estimate value if not directly stored
            allocation[asset] = (position['size'] * position.get('entry_price', 1.0)) / total_value
            
    cash_pct = get_cash_balance() / total_value
    allocation['CASH'] = cash_pct
    
    return allocation