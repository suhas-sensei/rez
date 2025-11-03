# Advanced Risk Management System for Crypto Trading Engine

## Overview

This document outlines the implementation of a dynamic risk management system for the crypto trading engine. The system introduces risk profile-based trading parameters that allow users to customize their trading behavior according to their risk tolerance while maintaining sophisticated risk controls.

## Risk Profile Architecture

### Low Risk Profile
- **Stop-Loss Settings**: 3-5% fixed stop-loss or adaptive stop-loss based on volatility
- **Position Sizing**: Maximum 1-2% of portfolio value per trade
- **Risk Per Trade**: 1% of portfolio value
- **Portfolio Risk Limit**: Maximum 15% total portfolio risk
- **Kelly Fraction**: 0.15 (conservative approach)
- **Signal Sensitivity**: Higher confidence thresholds required for trade execution
- **Asset Universe**: Focus on large-cap, stable cryptocurrencies (BTC, ETH, USDT, USDC, etc.)
- **Market Regime Adaptation**: Conservative position sizing in all market conditions

### Medium Risk Profile
- **Stop-Loss Settings**: 6-8% fixed stop-loss or adaptive stop-loss based on volatility
- **Position Sizing**: Maximum 2-4% of portfolio value per trade
- **Risk Per Trade**: 2% of portfolio value
- **Portfolio Risk Limit**: Maximum 25% total portfolio risk
- **Kelly Fraction**: 0.25 (balanced approach)
- **Signal Sensitivity**: Moderate confidence thresholds for trade execution
- **Asset Universe**: Mix of large and mid-cap cryptocurrencies (BTC, ETH, SOL, AVAX, ADA, DOT, LINK, etc.)
- **Market Regime Adaptation**: Adjusted position sizing based on market conditions

### High Risk Profile
- **Stop-Loss Settings**: 9-12% fixed stop-loss or 8-10% trailing stop-loss
- **Position Sizing**: Maximum 4-6% of portfolio value per trade
- **Risk Per Trade**: 3% of portfolio value
- **Portfolio Risk Limit**: Maximum 35% total portfolio risk
- **Kelly Fraction**: 0.35 (aggressive approach)
- **Signal Sensitivity**: Lower confidence thresholds for trade execution
- **Asset Universe**: Focus on mid and small-cap cryptocurrencies with higher volatility (SOL, AVAX, LUNA, FTM, VET, etc.)
- **Market Regime Adaptation**: Higher position sizing during trending markets, caution during volatile periods

## Asset Universe Classification

### Classification Methodology

Assets are classified using a multi-factor risk scoring algorithm based on:

1. **Volatility Metrics**:
   - 30-day historical volatility (standard deviation of returns)
   - Average True Range (ATR) relative to price
   - Price volatility ratios

2. **Liquidity Metrics**:
   - Average daily trading volume (minimum $50M for high-risk, $100M for medium-risk, $200M for low-risk)
   - Bid-ask spreads
   - Market depth

3. **Market Cap Classification**:
   - Large Cap (>$10B): Generally low-risk
   - Mid Cap ($1B-$10B): Medium-risk 
   - Small Cap (<$1B): High-risk

4. **Correlation Analysis**:
   - Correlation with Bitcoin (BTC) as market indicator
   - Cross-correlation with other portfolio holdings

### Risk Scoring Algorithm

Each asset is assigned a risk score based on weighted factors:

```
Risk Score = (Volatility Weight × 0.4) + (Liquidity Weight × 0.3) + (Market Cap Weight × 0.2) + (Correlation Weight × 0.1)
```

- Low Risk: Risk Score 0.0-0.3
- Medium Risk: Risk Score 0.3-0.7
- High Risk: Risk Score 0.7-1.0

### Dynamic Universe Updates

The asset universe is updated weekly using a hybrid approach:

1. **Static Core Universe** (Updated Weekly):
   - Recalculated based on 30-day trailing volatility and other metrics
   - Maintains diversification across sectors
   - Excludes assets below minimum liquidity thresholds

2. **Dynamic Daily Filtering**:
   - Filters current assets based on real-time liquidity
   - Removes assets with extreme volatility events (>20% single-day moves)
   - Ensures sufficient data availability for technical analysis

## Dynamic Risk Parameters

### Stop-Loss Implementation

1. **Fixed Percentage Stop-Loss**:
   - Low Risk: 3-5% below entry price
   - Medium Risk: 6-8% below entry price
   - High Risk: 9-12% below entry price

2. **Volatility-Adjusted Stop-Loss**:
   - Stop-loss percentage scaled by current volatility relative to historical volatility
   - Formula: `StopLoss% = BaseStopLoss% × (CurrentVolatility / HistoricalVolatility)`

3. **Trailing Stop-Loss** (High Risk Profile):
   - Activates when trade is in profit (>3%)
   - Trailing percentage: 5-7% of current price
   - Locks in profits while allowing for positive volatility

4. **User Override Capability**:
   - Users can specify custom stop-loss percentages
   - System validates that custom values are within reasonable bounds
   - Override values take precedence over profile defaults

### Position Sizing Algorithm

Position sizing incorporates multiple factors for sophisticated risk management:

1. **Risk-Based Position Limiting**:
   - Maximum percentage of portfolio allocated per trade
   - Low Risk: 1-2% of portfolio value
   - Medium Risk: 2-4% of portfolio value
   - High Risk: 4-6% of portfolio value

2. **Volatility-Adjusted Position Sizing**:
   - Reduces position size for above-average volatility assets
   - Formula: `Adjusted Position Size = Base Position Size × (1 - (Volatility Ratio - 1) × 0.5)`

3. **Correlation-Adjusted Position Sizing**:
   - Reduces position size when asset is highly correlated with existing holdings
   - Formula: `Correlation Adj. = Base Size × (1 - Correlation Factor × 0.3)`

4. **Kelly Criterion Integration**:
   - Estimation of win rate and risk-reward ratio
   - Kelly percentage calculation: `K = (bp - q) / b` where:
     - `b` = odds (avg_win / avg_loss)
     - `p` = win rate
     - `q` = 1 - win rate
   - Risk-adjusted Kelly fraction applied per profile

## Market Regime Detection and Adaptation

The system detects market regimes to adapt risk parameters dynamically:

1. **Trending Markets** (Hurst Exponent > 0.6):
   - Slightly increased position sizing for all profiles
   - Emphasis on momentum signals
   - Reduced volatility adjustments

2. **Mean-Reverting Markets** (Hurst Exponent < 0.4):
   - Increased position sizing for mean reversion signals
   - Tighter stop-loss settings
   - Emphasis on oscillating indicators (RSI, Stochastic)

3. **Volatile Markets** (High ATR and Volatility):
   - Reduced position sizing across all profiles
   - Wider stop-loss settings to avoid whipsaws
   - Reduced signal sensitivity

## Technical Implementation Considerations

### AdvancedRiskManager Parameters

The AdvancedRiskManager is updated with profile-specific parameters:

1. **Low Risk Profile**:
   - `max_position_size = 0.02` (2%)
   - `max_total_risk = 0.15` (15%)
   - `kelly_fraction = 0.15`
   - `volatility_multiplier = 0.8`

2. **Medium Risk Profile**:
   - `max_position_size = 0.04` (4%)
   - `max_total_risk = 0.25` (25%)
   - `kelly_fraction = 0.25`
   - `volatility_multiplier = 1.0`

3. **High Risk Profile**:
   - `max_position_size = 0.06` (6%)
   - `max_total_risk = 0.35` (35%)
   - `kelly_fraction = 0.35`
   - `volatility_multiplier = 1.2`

### Signal Weighting Adjustments

Signal weights are adjusted based on risk profile and market regime:

1. **Trending Market Weights**:
   - Trend Signal: 35% (Low Risk), 30% (Medium), 25% (High)
   - Momentum Signal: 25% (Low Risk), 30% (Medium), 35% (High)
   - Mean Reversion: 20% (Low Risk), 20% (Medium), 15% (High)
   - Volatility Signal: 20% (Low Risk), 20% (Medium), 25% (High)

2. **Ranging Market Weights**:
   - Equal distribution across all signals with risk-based adjustments

### User Input Parameters

Command-line arguments for risk customization:

1. `--risk-profile`: low, medium, or high (default: medium)
2. `--stop-loss`: Custom stop-loss percentage override
3. `--position-size-limit`: Custom maximum position size percentage
4. `--risk-per-trade`: Custom risk percentage per trade
5. `--take-profit`: Custom take-profit percentage

### Configuration Integration

The config_loader.py file is updated to handle risk profile parameters:

1. **Environment Variables**:
   - `RISK_PROFILE`: Default risk profile (low, medium, high)
   - `CUSTOM_STOP_LOSS`: User-defined stop-loss override
   - `CUSTOM_POSITION_SIZE`: User-defined position size override

2. **Runtime Override**:
   - Command-line arguments take precedence over environment variables
   - Environment variables take precedence over profile defaults

## Performance Metrics and Monitoring

The system tracks risk-adjusted performance metrics:

1. **Risk-Adjusted Returns**:
   - Sharpe ratio
   - Sortino ratio
   - Maximum drawdown by profile

2. **Risk Compliance**:
   - Percentage of trades within position size limits
   - Stop-loss hit rates by profile
   - Portfolio risk exposure

3. **Profile Effectiveness**:
   - Performance consistency within each risk profile
   - Profile-specific risk metric compliance
   - Correlation between selected profile and actual risk metrics

## Implementation Timeline

1. **Phase 1**: Asset universe classification and risk scoring
2. **Phase 2**: Dynamic risk parameter implementation
3. **Phase 3**: User input handling and configuration updates
4. **Phase 4**: Market regime adaptation
5. **Phase 5**: Testing and validation

This comprehensive risk management system provides users with the flexibility to customize their trading according to their risk tolerance while maintaining sophisticated risk controls and portfolio protection mechanisms.