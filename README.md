# AI Trading Agent (Simulation)

A simulation-based AI trading agent that uses real-time market data from TAAPI to make trading decisions using AI models, with performance visualization through a simple GUI. Based on the Nocturn repository but modified for simulation trading.

## Features

- Simulation-based trading (no real money involved)
- AI-powered trading decisions using technical indicators
- Real-time portfolio visualization dashboard
- Support for open-source LLMs (Ollama, etc.) as well as commercial APIs
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

# Run the agent (default assets: BTC ETH, interval: 1h, starting funds: $1000)
python src/main.py

# Run with custom parameters
python src/main.py --assets BTC ETH SOL --interval 1h --starting-funds 5000
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
4. **Recent Trades**: Table showing the last 10 trades made by the AI agent

### Trading Decisions:

The AI agent analyzes technical indicators (RSI, MACD, EMA, etc.) and makes BUY, SELL, or HOLD decisions based on market conditions. In simulation mode, these decisions affect your virtual portfolio value.

## Configuration Options

### Environment Variables:

- `TAAPI_API_KEY`: API key for technical indicators
- `LLM_API_KEY`: API key for your LLM service
- `LLM_BASE_URL`: Base URL for LLM API (e.g., OpenAI, Ollama, etc.)
- `LLM_MODEL`: Model name to use for trading decisions
- `SIMULATION_MODE`: Should remain `true` for this simulation
- `STARTING_FUNDS`: Initial virtual amount to start with (default: 1000.0)
- `RISK_PER_TRADE`: Risk percentage per trade (default: 0.02 for 2%)

### Command Line Options:

When running `python src/main.py`:

- `--assets`: List of assets to trade (default: BTC ETH)
- `--interval`: Trading interval (default: 1h)
- `--starting-funds`: Starting simulated funds amount (default: 1000.0)

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
2. The AI analyzes the indicators and market conditions to make trading decisions
3. The simulation engine processes these decisions and adjusts your portfolio value
4. Trade results are logged for the GUI dashboard
5. The portfolio value changes based on simulated market movements

The simulation is designed to approximate real market behavior while using virtual funds.

## Safety & Disclaimers

- ✅ This is a simulation - no real money is used
- ⚠️ The agent uses AI for trading decisions but results are not guaranteed
- ⚠️ Past performance in simulation does not indicate future results
- ⚠️ Use at your own risk
- ⚠️ This is for educational purposes only

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

## License

This project is open source and available under the MIT License.
