def execute_trade_simulation(asset, decision):
    """
    Execute a simulated trade based on the AI decision
    This function now properly handles trading decisions by buying/selling portions of positions
    """
    global simulation_state

    if not simulation_state['initialized']:
        initialize_simulation()

    # Record initial state
    initial_portfolio = simulation_state['portfolio_value']

    # Get current position in this asset
    current_position = simulation_state['positions'].get(asset, {'size': 0, 'entry_price': 1.0, 'usd_value': 0})
    
    # Get cash balance
    cash = simulation_state.get('cash', initial_portfolio * 0.3)  # Default to 30% of portfolio as cash

    # Determine position sizing based on risk profile (this information could be passed from config)
    # For now we'll use a default position sizing
    config = load_config()
    risk_per_trade = config.get('default_risk_per_trade', 0.02)  # Default 2% risk per trade
    position_size_limit = config.get('default_position_size_limit', 0.10)  # Default 10% of portfolio

    # Calculate position value changes based on market movement
    # First, simulate the market movement for this asset
    if decision.lower() in ['buy', 'long']:
        # Buy decisions should have a higher probability of positive movement based on confidence
        # But market movements are independent of the decision (real markets don't always confirm decisions!)
        market_movement = random.uniform(-0.01, 0.03)  # -1% to +3% movement
    elif decision.lower() in ['sell', 'short']:
        # Sell decisions based on current market conditions
        market_movement = random.uniform(-0.03, 0.01)  # -3% to +1% movement
    elif decision.lower() == 'hold':
        # Hold should have minimal change
        market_movement = random.uniform(-0.005, 0.005)  # -0.5% to +0.5% movement
    else:
        # Default random movement
        market_movement = random.uniform(-0.015, 0.015)  # -1.5% to +1.5% movement

    # Get the current position details
    position_size = current_position['size']
    entry_price = current_position['entry_price']
    
    # Calculate new price based on market movement
    current_price = entry_price
    new_price = current_price * (1 + market_movement)

    # Update existing position value based on new price (before executing trade)
    current_usd_value = position_size * new_price

    # Execute the trading decision by adjusting position size
    if decision.lower() in ['buy', 'long'] and cash > 0:
        # Execute buy: increase position size using cash
        buy_amount = min(cash * 0.2, initial_portfolio * position_size_limit * 0.5)  # Buy up to 20% of cash or 50% of position limit
        additional_size = buy_amount / new_price if new_price > 0 else 0
        position_size += additional_size
        cash -= buy_amount
    elif decision.lower() in ['sell', 'short'] and position_size > 0:
        # Execute sell: reduce position size, increase cash
        sell_fraction = 0.3  # Sell 30% of position
        sell_size = position_size * sell_fraction
        sell_amount = sell_size * new_price  # Amount of cash received from selling
        
        position_size -= sell_size
        cash += sell_amount
    
    # Ensure no negative values
    position_size = max(0, position_size)
    cash = max(0, cash)
    current_usd_value = position_size * new_price if position_size > 0 else 0

    # Update the position with the new calculated values
    simulation_state['positions'][asset] = {
        'size': position_size,
        'entry_price': new_price,  # Update entry price to current market price
        'usd_value': current_usd_value
    }
    
    # Update cash in simulation state
    simulation_state['cash'] = cash

    # Calculate total portfolio value based on all positions + cash
    total_value = simulation_state.get('cash', 0)
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