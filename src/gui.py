import streamlit as st
import streamlit.components.v1 as components
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

# Configure the page to have a fixed sidebar
st.set_page_config(layout="centered", initial_sidebar_state="expanded")

# Rezlabs Theme - Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    
    /* Global Styles - Default to Dark Theme for Main Content */
    .stApp {
        background-color: #0a0a0a;
        color: #e8e8e8;
    }
    
    /* Typography - Default to White for Main Content */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Instrument Serif', serif !important;
        color: #ffffff;
        font-weight: 400;
    }
    
    /* Apply Inter font generally but NOT globally to everything to avoid breaking icons */
    .stMarkdown, .stText, p, label, input, .stButton button {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Main Title */
    h1 {
        font-size: 2.5rem;
        margin-bottom: 2rem;
        letter-spacing: -0.02em;
    }
    
    /* =========================================
       SIDEBAR STYLES (LIGHT THEME)
       ========================================= */
    
    /* Sidebar Container - Desktop Default */
    [data-testid="stSidebar"] {
        background-color: #d8d8d8; /* Darker grey for better contrast with toggle button */
        border-right: 1px solid #e5e5e5;
    }
    
    /* Desktop: Fixed 15% width */
    @media (min-width: 900px) {
        [data-testid="stSidebar"] {
            min-width: 15% !important;
            max-width: 15% !important;
            width: 15% !important;
        }
        
        /* Adjust main content to respect the 15% sidebar */
        [data-testid="stMain"] {
            margin-left: 0 !important; /* Streamlit handles this automatically mostly, but we reset our previous override */
        }
    }
    
    /* Sidebar Headers */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #000000 !important;
    }
    
    /* Sidebar Text/Labels */
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stWidgetLabel {
        color: #000000 !important;
    }
    
    /* Sidebar Inputs */
    [data-testid="stSidebar"] .stSelectbox > div > div,
    [data-testid="stSidebar"] .stNumberInput input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #000000 !important;
    }

    /* Sidebar Slider - No Border */
    [data-testid="stSidebar"] .stSlider {
        color: #000000 !important;
    }
    
    /* Sidebar Selectbox SVG Icon */
    [data-testid="stSidebar"] .stSelectbox svg {
        fill: #000000 !important;
    }
    
    /* Sidebar Buttons */
    [data-testid="stSidebar"] .stButton > button {
        background-color: #000000;
        color: #ffffff;
        border: none;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #333333;
        color: #ffffff;
    }
    
    [data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #e5e5e5;
    }
    
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background-color: #f5f5f5;
        color: #000000;
    }
    
    /* Sidebar Info/Alerts */
    [data-testid="stSidebar"] .stAlert {
        background-color: #ffffff;
        border: 1px solid #e5e5e5;
        color: #000000 !important;
    }
    
    [data-testid="stSidebar"] .stAlert p {
        color: #000000 !important;
    }
    
    /* =========================================
       MAIN CONTENT STYLES (DARK THEME)
       ========================================= */
       
    /* Main Content Metrics */
    [data-testid="stMain"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }
    
    [data-testid="stMain"] [data-testid="stMetricLabel"] {
        color: #999999 !important;
    }
    
    /* Main Content Alerts/Info */
    [data-testid="stMain"] .stAlert {
        background-color: #1a1a1a;
        border: 1px solid #2a2a2a;
        color: #e8e8e8 !important;
    }
    
    [data-testid="stMain"] .stAlert p {
        color: #e8e8e8 !important;
    }
    
    /* Main Content Dataframes */
    [data-testid="stMain"] .dataframe {
        background-color: #1a1a1a;
        color: #e8e8e8;
        border: 1px solid #2a2a2a;
    }
    
    [data-testid="stMain"] .dataframe th {
        background-color: #0a0a0a;
        color: #999999;
    }
    
    [data-testid="stMain"] .dataframe td {
        border-color: #2a2a2a;
    }
    
    /* Main Content Subheaders */
    [data-testid="stMain"] h2, [data-testid="stMain"] h3 {
        border-bottom: 1px solid #2a2a2a;
    }
    
    /* Hide the vertical line separator in selectbox (Global) */
    .stSelectbox [data-baseweb="select"] > div > div:last-child {
        display: none !important;
    }
    
    /* Ensure the native sidebar toggle button is visible and styled */
    [data-testid="stSidebarCollapseButton"] {
        display: block !important;
        background-color: transparent !important; /* Transparent background */
        border: 2px solid #000000 !important; /* Black border */
        border-radius: 4px !important;
        padding: 4px !important;
    }
    
    [data-testid="stSidebarCollapseButton"]:hover {
        background-color: rgba(0, 0, 0, 0.1) !important; /* Slight dark tint on hover */
    }
    
    [data-testid="stSidebarCollapseButton"] svg {
        fill: #000000 !important; /* Black icon */
    }
    
</style>
""", unsafe_allow_html=True)

# Check if session log file is already in session state, if not create it
if 'session_log_file' not in st.session_state:
    # Generate a unique session log file name with timestamp when first loaded
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.session_log_file = f'trade_log/trades_log_{current_time}.jsonl'
    # Initialize the new session log file
    # Ensure the directory exists
    os.makedirs('trade_log', exist_ok=True)
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
    session_file = st.session_state.get('session_log_file', 'trade_log/trades_log.jsonl')
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
st.title("Rez Dashboard")

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
        if os.path.exists('trade_log/trades_log.jsonl'):
            os.remove('trade_log/trades_log.jsonl')
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
        
        # Filter out any rows with NaN values in portfolio_value to prevent undefined in chart
        filtered_df = display_df.dropna(subset=['portfolio_value'])
        
        if filtered_df.empty:
            st.warning("No valid data available for portfolio value chart.")
        else:
            fig = px.line(filtered_df, x='timestamp', y='portfolio_value',
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
                        color="#999999"
                    )
                )
                fig.add_annotation(
                    x=trading_start_time,
                    y=1,
                    yref="paper",
                    text="Trading Start",
                    showarrow=False,
                    xanchor="left",
                    yanchor="bottom",
                    font=dict(color="#ffffff")
                )
            
            fig.update_layout(
                xaxis_title='Time',
                yaxis_title='Portfolio Value ($)',
                hovermode='x unified',
                # Rezlabs Theme - Dark monochrome styling
                plot_bgcolor='#0a0a0a',
                paper_bgcolor='#0a0a0a',
                font=dict(
                    family='Inter, sans-serif',
                    size=12,
                    color='#e8e8e8'
                ),
                xaxis=dict(
                    gridcolor='#2a2a2a',
                    linecolor='#444444',
                    zerolinecolor='#444444'
                ),
                yaxis=dict(
                    gridcolor='#2a2a2a',
                    linecolor='#444444',
                    zerolinecolor='#444444'
                ),
                title_text="",
                margin=dict(t=30, l=10, r=10, b=10)
            )
            
            # Update trace styling - white line for portfolio value
            fig.update_traces(
                line=dict(color='#ffffff', width=2),
                hovertemplate='<b>%{x}</b><br>Portfolio: $%{y:,.2f}<extra></extra>'
            )
            
            st.plotly_chart(fig, width='stretch')
        
        # Show latest portfolio value
        if not display_df.empty and 'portfolio_value' in display_df.columns:
            latest_value = display_df['portfolio_value'].iloc[-1] if not pd.isna(display_df['portfolio_value'].iloc[-1]) else 0
            initial_value = display_df['portfolio_value'].iloc[0] if not pd.isna(display_df['portfolio_value'].iloc[0]) else 0
            pnl = latest_value - initial_value
            pnl_pct = (pnl / initial_value) * 100 if initial_value != 0 else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Latest Portfolio Value", f"${latest_value:.2f}")
            col2.metric("P&L", f"${pnl:.2f}", f"{pnl_pct:+.2f}%")
            col3.metric("Total Trades", len(display_df))
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Latest Portfolio Value", "$0.00")
            col2.metric("P&L", "$0.00", "0.00%")
            col3.metric("Total Trades", "0")
        
        # Show risk profile information if available
        if 'risk_profile' in display_df.columns and not display_df.empty:
            # Get the risk profile from the most recent trade
            latest_risk_profile = display_df['risk_profile'].iloc[-1] if not pd.isna(display_df['risk_profile'].iloc[-1]) else "Not specified"
            if latest_risk_profile != "Not specified":
                st.info(f"Risk Profile: **{latest_risk_profile.capitalize()}**")
            else:
                st.info(f"Risk Profile: **{latest_risk_profile}**")
        
        # Show recent trades
        st.subheader("Recent Trades")
        if not display_df.empty:
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
            # Clean any NaN values in the recent trades dataframe
            recent_trades = recent_trades.fillna("N/A")
            st.dataframe(recent_trades)
        else:
            st.write("No recent trades to display.")
        
        # Show statistics for the trading period
        st.subheader("Performance Statistics (From First Trade)")
        if not display_df.empty and 'portfolio_value' in display_df.columns and len(display_df) > 0:
            latest_pv = display_df['portfolio_value'].iloc[-1] if not pd.isna(display_df['portfolio_value'].iloc[-1]) else 0
            initial_pv = display_df['portfolio_value'].iloc[0] if not pd.isna(display_df['portfolio_value'].iloc[0]) else 0
            total_return = ((latest_pv / initial_pv) - 1) * 100 if initial_pv != 0 else 0
            max_value = display_df['portfolio_value'].max() if not display_df['portfolio_value'].isna().all() else 0
            min_value = display_df['portfolio_value'].min() if not display_df['portfolio_value'].isna().all() else 0
            
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            stats_col1.metric("Total Return", f"{total_return:+.2f}%")
            stats_col2.metric("Max Value", f"${max_value:.2f}")
            stats_col3.metric("Min Value", f"${min_value:.2f}")
        else:
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            stats_col1.metric("Total Return", "0.00%")
            stats_col2.metric("Max Value", "$0.00")
            stats_col3.metric("Min Value", "$0.00")

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