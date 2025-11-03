import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime
import os

st.title("Performance Dashboard")

# Load trade history from log file
def load_trade_history():
    if not os.path.exists('trades_log.jsonl'):
        return pd.DataFrame()
    
    trades = []
    with open('trades_log.jsonl', 'r') as f:
        for line in f:
            try:
                trade = json.loads(line.strip())
                trades.append(trade)
            except:
                continue  # Skip malformed lines
                
    if not trades:
        return pd.DataFrame()
    
    df = pd.DataFrame(trades)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Calculate cumulative portfolio value
    df['cumulative_portfolio'] = df['portfolio_value'].expanding().max()
    
    # Only show the most recent trading session (last 2 hours of data or last 50 trades, whichever is smaller)
    # This ensures fresh data is displayed for each run
    if len(df) > 0:
        # Get the most recent timestamp
        latest_time = df['timestamp'].max()
        # Filter to show only data from the last 2 hours (or all if less than 2 hours of data)
        time_threshold = latest_time - pd.Timedelta(hours=2)
        recent_df = df[df['timestamp'] >= time_threshold]
        
        # If more than 50 recent trades, show only the last 50
        if len(recent_df) > 50:
            recent_df = recent_df.tail(50)
        
        return recent_df
    else:
        return df

# Load the trade history
df = load_trade_history()

if df.empty:
    st.warning("No trade data available. Please run the trading agent to generate data.")
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
        st.subheader("Portfolio Value Over Time")
        
        fig = px.line(display_df, x='timestamp', y='portfolio_value', 
                     title='Simulated Portfolio Value Over Time',
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
        
        st.plotly_chart(fig, use_container_width=True)
        
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

st.sidebar.header("Controls")
st.sidebar.info("Run the trading agent to generate data for this dashboard")