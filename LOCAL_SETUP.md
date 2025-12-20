# Local Setup Guide

## Prerequisites

- Python 3.12 or compatible version
- Ubuntu/Debian-based system (for TA-Lib installation)

## Quick Start

```bash
# 1. Create and activate virtual environment
python3.12 -m venv venv
source venv/bin/activate

# 2. Install Python dependencies
pip install -r requirements.txt
pip install scikit-learn
pip install pandas-ta==0.4.71b0

# 3. Create trade log directory
mkdir -p trade_log

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your API keys (TAAPI_API_KEY, LLM_API_KEY, etc.)

# 5. Run the trading agent
python src/main.py
```

## Installing TA-Lib (Optional but Recommended)

TA-Lib provides advanced technical indicators. Install from source:

```bash
# Download and build TA-Lib C library
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib
./configure --prefix=/usr
make
sudo make install

# Install Python wrapper
source /path/to/your/venv/bin/activate
pip install TA-Lib
```

## Running the Dashboard

In a separate terminal (while the agent is running):

```bash
source venv/bin/activate
streamlit run src/gui.py
```

The dashboard will be available at http://localhost:8501

## Command Line Options

```bash
# Run with custom assets
python src/main.py --assets BTC ETH SOL --interval 1h --starting-funds 5000

# Run with different risk profiles
python src/main.py --risk-profile low    # Conservative
python src/main.py --risk-profile medium # Balanced (default)
python src/main.py --risk-profile high   # Aggressive

# Custom risk parameters
python src/main.py --risk-profile medium --stop-loss 8 --position-size-limit 5
```

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `TAAPI_API_KEY` | API key from [taapi.io](https://taapi.io/) |
| `LLM_API_KEY` | OpenAI API key or OpenRouter key |
| `LLM_BASE_URL` | API endpoint (e.g., `https://api.openai.com/v1`) |
| `LLM_MODEL` | Model name (e.g., `gpt-4o`) |
| `SIMULATION_MODE` | Set to `true` for simulation |
| `STARTING_FUNDS` | Initial virtual funds (default: 1000.0) |
