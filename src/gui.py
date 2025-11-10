import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime
import os
import threading
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import run_trading_session, stop_trading_session

# Check if session log file is already in session state, if not create it
if 'session_log_file' not in st.session_state:
    # Generate a unique session log file name with timestamp when first loaded
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.session_log_file = f'trades_log_{current_time}.jsonl'
    # Initialize the new session log file
    with open(st.session_state.session_log_file, 'w') as f:
        pass  # Create empty file


# Initialize session state
if 'trading_status' not in st.session_state:
    st.session_state.trading_status = 'stopped'  # 'stopped', 'running'
if 'latest_data' not in st.session_state:
    st.session_state.latest_data = None


# Load trade history from log file
def load_trade_history():
    # Get the session log file from session state
    session_file = st.session_state.get('session_log_file', 'trades_log.jsonl')
    if not os.path.exists(session_file):
        return pd.DataFrame()
    
    trades = []
    with open(session_file, 'r') as f:
        for line in f:
            try:
                trade = json.loads(line.strip())
                trades.append(trade)
            except:
                continue  # Skip malformed lines
                
    if not trades:
        return pd.DataFrame()
    
    df = pd.DataFrame(trades)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Calculate cumulative portfolio value
    df['cumulative_portfolio'] = df['portfolio_value'].expanding().max()
    
    # For session-specific logs, show all data for this session
    return df


# Function to run the trading session in a separate thread
def start_trading_session(risk_profile, starting_funds, trading_duration, session_log_file):
    # st.session_state.trading_status is already set to 'running' before thread starts
    # Create a fresh log file for this session
    with open(session_log_file, 'w') as f:
        pass  # Create empty file
    # Set the environment variable to use the session-specific log file
    import os
    os.environ['TRADES_LOG_FILE'] = session_log_file
    try:
        final_value = run_trading_session(
            risk_profile=risk_profile,
            starting_funds=starting_funds,
            trading_duration_minutes=trading_duration
        )
        # Only update status to stopped if we're still running (not already stopped by user)
        if st.session_state.trading_status == 'running':
            st.session_state.trading_status = 'stopped'
        # Note: The success message won't work in a thread, so it's handled in the GUI
    except Exception as e:
        # Only update status to stopped if we're still running (not already stopped by user)
        if st.session_state.trading_status == 'running':
            st.session_state.trading_status = 'stopped'
        # Note: The error message won't work in a thread, so it's handled in the GUI
    finally:
        # Clean up the environment variable
        if 'TRADES_LOG_FILE' in os.environ:
            del os.environ['TRADES_LOG_FILE']


# Streamlit UI
st.title("Dashboard")

# Sidebar controls
st.sidebar.header("Trading Configuration")
risk_profile = st.sidebar.selectbox(
    "Risk Profile",
    options=['low', 'medium', 'high'],
    index=1,
    help="Select the risk level for trading strategy"
)

initial_balance = st.sidebar.number_input(
    "Initial Balance ($)",
    min_value=100.0,
    max_value=100000.0,
    value=1000.0,
    step=100.0,
    help="Starting amount for the trading simulation"
)

trading_duration = st.sidebar.slider(
    "Trading Duration (minutes)",
    min_value=1,
    max_value=240,
    value=60,
    help="How long the trading session should run"
)

# Start/Stop buttons
if st.session_state.trading_status == 'stopped':
    if st.sidebar.button("🚀 Start Trading", type="primary"):
        # Clear the log file to ensure fresh data for each run
        if os.path.exists('trades_log.jsonl'):
            os.remove('trades_log.jsonl')
        st.session_state.trading_status = 'running'  # Set status before starting thread to prevent multiple starts
        # Start trading in a separate thread, passing the session log file
        thread = threading.Thread(
            target=start_trading_session,
            args=(risk_profile, initial_balance, trading_duration, st.session_state.session_log_file)
        )
        thread.daemon = True  # Set as daemon thread to ensure it stops when main process stops
        thread.start()
        st.rerun()
elif st.session_state.trading_status == 'running':
    if st.sidebar.button("🛑 Stop Trading", type="secondary"):
        # Call the stop function to signal the trading session to stop in the terminal too
        stop_trading_session()
        st.session_state.trading_status = 'stopped'
        st.success("Trading session stopped by user.")
        st.rerun()
    st.sidebar.info("Trading in progress...")

# Show current status
if st.session_state.trading_status == 'running':
    st.info("Trading session is currently running. Click 'Refresh Data' to update the dashboard.")

# Load and display the trade history
df = load_trade_history()

if df.empty:
    st.warning("No trade data available. Configure your trading parameters and click 'Start Trading' to begin.")
    st.info("💡 Tip: Select your risk profile, initial balance, and trading duration in the sidebar, then click 'Start Trading'.")
else:
    # Find the first actual trading decision (not initial allocation)
    # Filter to show only trades with PnL details (real trading activity)
    # Identify trades that have PnL information in their result
    has_pnl_data = df.apply(lambda row: 'pnl' in row.get('result', {}), axis=1)
    
    if has_pnl_data.any():
        # Show only trades that have PnL information (real trading activity)
        display_df = df[has_pnl_data].copy()
        trading_df = display_df.copy()
    else:
        # If no trades have PnL info, show all except initial allocation
        initial_allocation_time = None
        if 'INITIAL_ALLOCATION' in df['asset'].values:
            initial_allocation_row = df[df['asset'] == 'INITIAL_ALLOCATION'].iloc[0]
            initial_allocation_time = initial_allocation_row['timestamp']
        
        if initial_allocation_time is not None:
            display_df = df[df['timestamp'] > initial_allocation_time].copy()
        else:
            display_df = df.copy()  # Use all data if no initial allocation to filter
        trading_df = display_df.copy()
    
    if display_df.empty:
        st.warning("No trading data to display after initial allocation.")
    else:
        # Create the main portfolio value chart
        st.subheader("📈 Portfolio Value Over Time")
        
        fig = px.line(display_df, x='timestamp', y='portfolio_value', 
                     title='',
                     labels={'portfolio_value': 'Portfolio Value ($)', 'timestamp': 'Time'})
        
        # Add a vertical line to indicate where trading began if we have PnL data
        if not trading_df.empty and len(df[~df.index.isin(trading_df.index)]) > 0:  # If there are records without PnL data
            # Show when actual trading with PnL calculation started
            trading_start_time = trading_df['timestamp'].iloc[0]
            fig.add_shape(
                type="line",
                x0=trading_start_time,
                x1=trading_start_time,
                y0=0,
                y1=1,
                yref="paper",  # Use 'paper' to span the entire y-axis
                line=dict(
                    dash="dash",
                    color="red"
                )
            )
            fig.add_annotation(
                x=trading_start_time,
                y=1,
                yref="paper",
                text="Trading Start",
                showarrow=False,
                xanchor="left",
                yanchor="bottom"
            )
        
        fig.update_layout(
            xaxis_title='Time',
            yaxis_title='Portfolio Value ($)',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Show latest portfolio value
        latest_value = display_df['portfolio_value'].iloc[-1]
        initial_value = display_df['portfolio_value'].iloc[0] 
        pnl = latest_value - initial_value
        pnl_pct = (pnl / initial_value) * 100 if initial_value != 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Latest Portfolio Value", f"${latest_value:.2f}")
        col2.metric("P&L", f"${pnl:.2f}", f"{pnl_pct:+.2f}%")
        col3.metric("Total Trades", len(display_df))
        
        # Show risk profile information if available
        if 'risk_profile' in display_df.columns and not display_df.empty:
            # Get the risk profile from the most recent trade
            latest_risk_profile = display_df['risk_profile'].iloc[-1] if not pd.isna(display_df['risk_profile'].iloc[-1]) else "Not specified"
            st.info(f"Risk Profile: **{latest_risk_profile.capitalize()}**")
        
        # Show recent trades
        st.subheader("Recent Trades")
        # Include risk profile if available in the data
        if 'risk_profile' in display_df.columns:
            recent_trades = display_df.tail(10)[['timestamp', 'asset', 'decision', 'portfolio_value', 'risk_profile']].copy()
            recent_trades = recent_trades.rename(columns={
                'portfolio_value': 'Portfolio Value ($)',
                'decision': 'Decision',
                'risk_profile': 'Risk Profile'
            })
        else:
            recent_trades = display_df.tail(10)[['timestamp', 'asset', 'decision', 'portfolio_value']].copy()
            recent_trades = recent_trades.rename(columns={
                'portfolio_value': 'Portfolio Value ($)',
                'decision': 'Decision'
            })
        st.dataframe(recent_trades)
        
        # Show statistics for the trading period
        st.subheader("Performance Statistics (From First Trade)")
        total_return = ((display_df['portfolio_value'].iloc[-1] / display_df['portfolio_value'].iloc[0]) - 1) * 100 if display_df['portfolio_value'].iloc[0] != 0 else 0
        max_value = display_df['portfolio_value'].max()
        min_value = display_df['portfolio_value'].min()
        
        stats_col1, stats_col2, stats_col3 = st.columns(3)
        stats_col1.metric("Total Return", f"{total_return:+.2f}%")
        stats_col2.metric("Max Value", f"${max_value:.2f}")
        stats_col3.metric("Min Value", f"${min_value:.2f}")

        # Calculate and display trading time
        if not df.empty:
            start_time = df['timestamp'].min()
            end_time = df['timestamp'].max()
            trading_duration = end_time - start_time
            trading_minutes = int(trading_duration.total_seconds() / 60)
            st.info(f"Trading Duration: **{trading_minutes} minutes**")

        # Show initial allocation if present
        if 'INITIAL_ALLOCATION' in df['asset'].values:
            st.subheader("Initial Allocation Details")
            initial_allocation = df[df['asset'] == 'INITIAL_ALLOCATION'].iloc[0]
            if 'allocation_breakdown' in initial_allocation:
                allocation_data = initial_allocation['allocation_breakdown']
                if allocation_data:
                    st.write("Asset Allocation Percentages:")
                    for asset, percentage in allocation_data.items():
                        st.write(f"{asset}: {percentage*100:.1f}%")

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("Configure your trading parameters in the sidebar and click 'Start Trading' to begin the simulation.")