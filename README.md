# ALGOS - Cointegration Pairs Trading Strategy

## Overview

This repository contains an algorithmic trading model that implements a **pairs trading strategy** using **cointegration** between Chevron (CVX) and Exxon Mobil (XOM) on a **15-minute timeframe**.

## Strategy Description

### Pairs Trading with Cointegration

Pairs trading is a market-neutral strategy that exploits the mean-reverting relationship between two cointegrated assets. When two stocks are cointegrated, they share a long-term equilibrium relationship, and temporary deviations from this relationship create trading opportunities.

### Key Components

1. **Cointegration Testing**: Uses the Engle-Granger method to test if CVX and XOM are cointegrated
2. **Hedge Ratio Calculation**: Determines the optimal ratio for the pair using OLS regression
3. **Spread Construction**: Creates a mean-reverting spread from the price series
4. **Z-Score Signals**: Generates trading signals based on standardized deviations from the mean
5. **Mean Reversion Trading**:
   - Enter when spread deviates significantly (z-score > ±2.0)
   - Exit when spread reverts to mean (z-score < ±0.5)
   - Stop loss at extreme deviations (z-score > ±3.5)

### Trading Logic

- **Long Spread** (when z-score < -2.0): Buy CVX, Sell XOM
- **Short Spread** (when z-score > +2.0): Sell CVX, Buy XOM
- **Exit Position** (when |z-score| < 0.5): Close all positions
- **Stop Loss** (when |z-score| > 3.5): Emergency exit

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Execution

```python
python cointegration_pairs_trading.py
```

### Custom Parameters

```python
from cointegration_pairs_trading import CointegrationPairsTrading

# Initialize model with custom parameters
model = CointegrationPairsTrading(
    symbol1='CVX',
    symbol2='XOM',
    lookback_period=60,
    z_entry=2.0,
    z_exit=0.5,
    stop_loss=3.5
)

# Run analysis
results = model.run_full_analysis(
    period='60d',
    interval='15m',
    rolling_window=100,
    initial_capital=100000
)
```

## Output

The model generates:

1. **Console Output**:
   - Cointegration test results
   - Hedge ratio
   - Trading signals statistics
   - Performance metrics (returns, Sharpe ratio, max drawdown, win rate)

2. **CSV File** (`cointegration_results.csv`):
   - Complete time series with prices, spreads, z-scores, signals, and returns

3. **Visualization** (`cointegration_analysis.png`):
   - Price series for both stocks
   - Spread and z-score with entry/exit thresholds
   - Trading positions over time
   - Equity curve

## Performance Metrics

The backtesting framework calculates:

- **Total Return**: Overall percentage return
- **Sharpe Ratio**: Risk-adjusted returns (annualized)
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Transaction Costs**: Total costs from trading

## Configuration

Edit `config.py` to customize:

- Trading symbols
- Data period and interval
- Z-score thresholds
- Initial capital
- Transaction costs

## Technical Details

### Cointegration Test

The model uses the **Engle-Granger two-step method**:
1. Run OLS regression: `CVX = β × XOM + ε`
2. Test residuals for stationarity using Augmented Dickey-Fuller test
3. If p-value < 0.05, series are cointegrated

### Spread Calculation

```
Spread = CVX - (hedge_ratio × XOM)
```

### Z-Score Calculation

```
Z-Score = (Spread - Rolling_Mean) / Rolling_StdDev
```

## Risk Considerations

- **Cointegration Breakdown**: The historical relationship may not hold in the future
- **Market Regime Changes**: Strategy performance varies across different market conditions
- **Execution Risk**: 15-minute data may have slippage in real trading
- **Transaction Costs**: Frequent trading can erode returns
- **Stop Losses**: Extreme market events can exceed stop loss levels

## Dependencies

- `numpy`: Numerical computations
- `pandas`: Data manipulation
- `matplotlib`: Plotting
- `seaborn`: Statistical visualizations
- `statsmodels`: Cointegration and stationarity tests
- `yfinance`: Financial data download
- `scipy`: Scientific computing

## License

MIT License

## Disclaimer

This model is for educational and research purposes only. Past performance does not guarantee future results. Always conduct thorough testing and risk assessment before deploying any trading strategy with real capital.