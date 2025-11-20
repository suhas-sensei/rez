# AI Trading System Architecture Flowchart

## Python TA + LLM Architecture with Fallback Mechanisms

```
Start Trading Session
        |
        v
Load Configuration (Risk Profile, Assets, etc.)
        |
        v
Get Historical Market Data for Assets
        |
        v
┌─────────────────────────────────────────────────────────────────┐
│                    Primary Decision Path                        │
└─────────────────────────────────────────────────────────────────┘
        |
        v
┌─────────────────────────────────────────────────────────────────┐
│  Advanced Trading Algorithm (advanced_decision_maker.py)        │
│  - Calculate 20+ Technical Indicators (Python TA)               │
│  - Market Regime Detection (Hurst Exponent)                     │
│  - Generate Multi-Signal Analysis                               │
└─────────────────────────────────────────────────────────────────┘
        |
        v
┌─────────────────────────────────────────────────────────────────┐
│  LLM Analysis Layer (decision_maker.py)                         │
│  - Send Indicators to LLM (OpenAI/Ollama API)                   │
│  - Get Trading Decision (BUY/SELL/HOLD)                         │
└─────────────────────────────────────────────────────────────────┘
        |
        v
┌─────────────────────────────────────────────────────────────────┐
│  Is LLM Service Available & Successful?                         │
└─────────────────────────────────────────────────────────────────┘
        |           |
       YES         NO
        |           |
        v           v
┌─────────────────┐    ┌─────────────────────────────────────────┐
│ Execute LLM     │    │          FALLBACK TRIGGERED           │
│ Decision        │    └─────────────────────────────────────────┘
└─────────────────┘                     |
        |                               v
        v                ┌─────────────────────────────────────────┐
Execute Trade           │  Fallback 1: Quant-Based Decision       │
Simulation              │  (decision_maker.py - quant_based_     │
        |               │  decision function)                     │
        v               │  - RSI Analysis                         │
Portfolio Value        │  - MACD with histogram                  │
Updated               │  - Bollinger Bands                      │
                      │  - Stochastic Oscillator                │
                      │  - Market Regime Detection              │
                      │  - Agreement Level Analysis             │
                      └─────────────────────────────────────────┘
                                    |
                                    v
                      ┌─────────────────────────────────────────┐
                      │  Is Quant Analysis Successful?          │
                      └─────────────────────────────────────────┘
                                |           |
                               YES         NO
                                |           |
                                v           v
                    ┌─────────────────┐    ┌─────────────────┐
                    │ Execute Quant   │    │  Fallback 2:    │
                    │ Decision        │    │  Simple TA      │
                    └─────────────────┘    │  (RSI-based)    │
                            |              └─────────────────┘
                            v                       |
                    Execute Trade                   |
                    Simulation                      v
                            |               Execute Simple
                            v               Decision
                    Portfolio Value
                    Updated
```

## Detailed Fallback Mechanism Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Fallback Hierarchy                         │
└─────────────────────────────────────────────────────────────────┘
        |
        v
┌─────────────────────────────────────────────────────────────────┐
│  Level 1: LLM Service Failure                                   │
│  - API Error / Timeout / Invalid Response                       │
│  → Trigger: quant_based_decision()                              │
└─────────────────────────────────────────────────────────────────┘
        |
        v
┌─────────────────────────────────────────────────────────────────┐
│  Level 2: Quant Analysis Failure                                │
│  - Missing indicators / Calculation errors                      │
│  → Trigger: simple_technical_decision()                         │
└─────────────────────────────────────────────────────────────────┘
        |
        v
┌─────────────────────────────────────────────────────────────────┐
│  Level 3: Technical Library Issues                              │
│  - TA-Lib not available → Use manual calculations               │
│  - All API failures → Use mock data generation                  │
└─────────────────────────────────────────────────────────────────┘

## Python TA Library Integration

┌─────────────────────────────────────────────────────────────────┐
│                    Python TA Components                         │
└─────────────────────────────────────────────────────────────────┘
        |
        v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  quant_indicator│    │  Historical Data│    │  Technical      │
│  _calculator.py │───▶│  fetcher.py     │───▶│  Analysis      │
│                 │    │                 │    │  Libraries      │
│  - RSI          │    │ - Get OHLCV     │    │  - pandas-ta    │
│  - MACD         │    │ - Timeframes    │    │  - TA-Lib       │
│  - Bollinger    │    │ - Lookback      │    │  - numpy/scipy  │
│  - Stochastic   │    │                 │    │                 │
│  - Custom       │    │                 │    │                 │
│  Indicators     │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘

## LLM Integration Points

┌─────────────────────────────────────────────────────────────────┐
│                    LLM Decision Points                          │
└─────────────────────────────────────────────────────────────────┘
        |
        v
┌─────────────────────────────────────────────────────────────────┐
│  Initial Allocation Decision                                     │
│  - Analyze all assets with advanced indicators                  │
│  - Generate optimal portfolio allocation                        │
└─────────────────────────────────────────────────────────────────┘
        |
        v
┌─────────────────────────────────────────────────────────────────┐
│  Trading Decision (Advanced Algorithm)                          │
│  - Market regime analysis                                       │
│  - Multi-signal weighted decision                               │
│  - Risk profile considerations                                  │
└─────────────────────────────────────────────────────────────────┘
        |
        v
┌─────────────────────────────────────────────────────────────────┐
│  Risk Profile Customization                                     │
│  - Apply profile-specific parameters                            │
│  - Adjust stop-loss, position sizing, etc.                     │
└─────────────────────────────────────────────────────────────────┘
```

## System Resilience Features

- **Continuous Operation**: Never stops, always has a fallback
- **Automatic Recovery**: Returns to primary path when services resume
- **Graceful Degradation**: Maintains core functionality during failures
- **Data Validation**: Checks for null/invalid values at each step
- **Multiple Exit Points**: Ensures safe operation under all conditions