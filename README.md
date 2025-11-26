# AI Trading Agent (Simulation)

A simulation-based AI trading agent that uses real-time market data from TAAPI to make trading decisions using AI models, with performance visualization through a simple GUI. Based on the Nocturn repository but modified for simulation trading.

## Features

- Simulation-based trading (no real money involved)
- AI-powered trading decisions using technical indicators
- Real-time portfolio visualization dashboard
- Support for open-source LLMs (Ollama, etc.) as well as commercial APIs
- **NEW: Python quant library fallback mechanism** - automatic fallback to quantitative analysis when LLM services are unavailable
- **NEW: Advanced Risk Management System** - comprehensive risk profile-based trading with customizable parameters (low/medium/high risk)
- **NEW: Dynamic Asset Selection** - risk-based asset universes with adaptive filtering
- Configurable starting funds and risk parameters
- Simple GUI for monitoring portfolio performance

## Prerequisites

Before getting started, you'll need:

1. **Python 3.8+** installed on your system
2. **API Key from TAAPI.io** for technical indicators (get a free key at [https://taapi.io/](https://taapi.io/))
3. **Access to an LLM** - either:
   - OpenAI API key (or compatible service), OR
   - Local LLM running with Ollama (instructions below)
4. **Git** for cloning the repository

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/hypeAI.git
cd hypeAI
```

### 2. Set up Python Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 3. Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit the `.env` file with your settings:

#### For Open Source Models with Ollama:

1. Install Ollama from [https://ollama.ai/](https://ollama.ai/)
2. Pull a model you want to use:
```bash
ollama pull llama3.2
```
3. Run Ollama:
```bash
ollama serve
```
4. Edit your `.env` file:
```env
LLM_API_KEY=dummy_key_for_ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.2
```

#### For OpenAI API:

1. Get an OpenAI API key from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Edit your `.env` file:
```env
LLM_API_KEY=your_openai_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

#### For Other LLM Services:

Most OpenAI-compatible services can be configured with the appropriate base URL and model name.

#### TAAPI Configuration:

1. Get a free API key from [https://taapi.io/](https://taapi.io/)
2. Add it to your `.env` file:
```env
TAAPI_API_KEY=your_taapi_api_key_here
```

## Running the Agent

### 1. Run the Trading Agent

```bash
# Activate your virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate   # Windows

# Run the agent with default settings (BTC, ETH, 1h interval, $1000 starting funds)
python src/main.py

# Run with custom assets
python src/main.py --assets BTC ETH SOL AVAX DOGE --interval 1h --starting-funds 5000

# Run with low risk profile (conservative trading)
python src/main.py --risk-profile low --assets BTC ETH --starting-funds 1000

# Run with high risk profile (aggressive trading)
python src/main.py --risk-profile high --assets SOL ARB LINK DOGE APT PEPE --starting-funds 1000

# Run with custom risk parameters
python src/main.py --risk-profile medium --stop-loss 8 --position-size-limit 5 --assets BTC ETH SOL --starting-funds 2000

# Run with custom parameters overriding risk profile defaults
python src/main.py --risk-profile low --stop-loss 6 --risk-per-trade 1.5 --assets BTC ETH --interval 4h --starting-funds 10000
```

### 2. View the Portfolio Dashboard

While the agent is running, open a new terminal window, activate the virtual environment, and run:

```bash
# Activate your virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate   # Windows

# Run the Streamlit dashboard
streamlit run src/gui.py
```

The dashboard will open in your browser at [http://localhost:8501](http://localhost:8501)

## Understanding the Results

### Dashboard Components:

1. **Portfolio Value Over Time**: Line chart showing how your simulated portfolio value changes over time
2. **Metrics**: Current portfolio value, total P&L (Profit & Loss), and number of trades executed
3. **Performance Statistics**: Total return percentage, maximum and minimum portfolio values
4. **Recent Trades**: Table showing the last 10 trades made by the AI agent with risk profile information
5. **Risk Profile Display**: Shows the risk profile currently being used by the trading agent

### Trading Decisions:

The AI agent analyzes technical indicators (RSI, MACD, EMA, etc.) and makes BUY, SELL, or HOLD decisions based on market conditions. In simulation mode, these decisions affect your virtual portfolio value.

## Advanced Risk Management System

The system now includes sophisticated risk management features:

### Risk Profiles:
- **Low Risk**: Conservative trading with tight stop-loss (3-5%), small position sizing (1-2%), and conservative entry signals
- **Medium Risk**: Balanced trading with moderate stop-loss (6-8%), medium position sizing (2-4%), and balanced entry signals  
- **High Risk**: Aggressive trading with wider stop-loss (9-12%), higher position sizing (4-6%), and aggressive entry signals

### Custom Parameters:
- `--stop-loss`: Custom stop-loss percentage (overrides profile default)
- `--position-size-limit`: Custom position size limit as percentage (overrides profile default)
- `--risk-per-trade`: Custom risk percentage per trade (overrides profile default)
- `--take-profit`: Custom take-profit percentage

### Asset Classification:
- Assets are automatically classified based on volatility, liquidity, and market cap
- Risk-appropriate assets are selected based on your chosen profile
- Dynamic filtering ensures assets meet current quality standards

### Fallback Mechanism:

The system includes a robust Python quant library fallback that activates when LLM services become unavailable. When the AI service fails, the system automatically uses Python libraries (pandas-ta, ta) to calculate technical indicators and make trading decisions based on:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- EMA (Exponential Moving Average)
- SMA (Simple Moving Average)
- Bollinger Bands
- Stochastic Oscillator
- Additional quantitative analysis methods

This ensures continuous operation even when external AI services are down.

## Configuration Options

### Environment Variables:

- `TAAPI_API_KEY`: API key for technical indicators
- `LLM_API_KEY`: API key for your LLM service
- `LLM_BASE_URL`: Base URL for LLM API (e.g., OpenAI, Ollama, etc.)
- `LLM_MODEL`: Model name to use for trading decisions
- `SIMULATION_MODE`: Should remain `true` for this simulation
- `STARTING_FUNDS`: Initial virtual amount to start with (default: 1000.0)
- `RISK_PER_TRADE`: Risk percentage per trade (default: 0.02 for 2%)
- `RISK_PROFILE`: Default risk profile (low, medium, high; default: medium)
- `CUSTOM_STOP_LOSS`: Custom stop-loss percentage override (in %, e.g., 5.0 for 5%)
- `CUSTOM_POSITION_SIZE`: Custom position size limit override (in %, e.g., 4.0 for 4%)
- `CUSTOM_RISK_PER_TRADE`: Custom risk per trade override (in %, e.g., 2.5 for 2.5%)

### Command Line Options:

When running `python src/main.py`:

- `--assets`: List of assets to trade (default: BTC ETH; if not specified, uses risk-appropriate assets)
- `--interval`: Trading interval (default: 1h)
- `--starting-funds`: Starting simulated funds amount (default: 1000.0)
- `--risk-profile`: Risk profile for trading (low, medium, high; default: medium)
- `--stop-loss`: Custom stop-loss percentage (overrides profile default)
- `--position-size-limit`: Custom position size limit as percentage (overrides profile default)
- `--risk-per-trade`: Custom risk percentage per trade (overrides profile default)
- `--take-profit`: Custom take-profit percentage

## Supported LLMs

This agent works with any OpenAI-compatible API, including:

- OpenAI GPT models
- Anthropic Claude (via OpenRouter)
- Local models via Ollama (Llama, Mistral, etc.)
- vLLM-hosted models
- Other OpenAI-compatible APIs

To use a different model, update the `LLM_BASE_URL` and `LLM_MODEL` in your `.env` file.

## How the Simulation Works

1. The agent fetches technical indicators from TAAPI.io
2. The AI analyzes the indicators and market conditions to make trading decisions based on your selected risk profile
3. The simulation engine processes these decisions and adjusts your portfolio value
4. Trade results are logged for the GUI dashboard
5. The portfolio value changes based on simulated market movements
6. Risk management parameters are automatically applied based on your selected profile

The simulation is designed to approximate real market behavior while using virtual funds.

## Python Quant Library Fallback

The system implements a sophisticated fallback mechanism using Python quantitative analysis libraries. When the primary LLM service is unavailable, the system seamlessly switches to using:

- **pandas-ta**: Advanced technical analysis indicators
- **ta**: Financial technical analysis library
- **numpy/scipy**: Mathematical and statistical computations

This fallback provides reliable trading decisions based on multiple technical indicators using quantitative analysis methods, ensuring continuous operation without depending solely on external AI services.

## Safety & Disclaimers

- ✅ This is a simulation - no real money is used
- ⚠️ The agent uses AI for trading decisions but results are not guaranteed
- ⚠️ Past performance in simulation does not indicate future results
- ⚠️ Use at your own risk
- ⚠️ This is for educational purposes only
- ⚠️ Always test with conservative settings first when using custom parameters

## Troubleshooting

### Common Issues:

1. **"Module not found" errors**: Make sure you've activated your virtual environment and installed requirements:
   ```bash
   source venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

2. **API Key errors**: Verify your API keys are correctly set in `.env` and the file is loaded:
   ```bash
   # Check if .env file is being loaded
   python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('TAAPI_API_KEY'))"
   ```

3. **Ollama not connecting**: Make sure Ollama is running:
   ```bash
   ollama serve
   ```
   And verify you have pulled the model:
   ```bash
   ollama pull llama3.2
   ```

4. **Streamlit dashboard not showing data**: Make sure the trading agent is running first to generate data.

### Performance Tips:

- Start with fewer assets (e.g., just BTC) to reduce API calls
- Increase the interval (e.g., `--interval 4h` instead of `--interval 1h`) to reduce frequency
- Monitor your TAAPI.io usage to avoid hitting rate limits
- Use the appropriate risk profile for your trading style and experience level

### Fallback Mechanism Troubleshooting:

- If the LLM service is not working, the system will automatically use the Python quant library fallback
- Check console output for "Error getting AI decision" messages to confirm fallback activation
- The fallback mechanism includes comprehensive error handling for missing or None indicator values

## License

This project is open source and available under the MIT License.

