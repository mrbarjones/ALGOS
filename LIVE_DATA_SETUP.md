# Live Data Setup Guide

This guide shows you how to get live/real-time data for the cointegration pairs trading model.

## Quick Comparison

| Provider | Cost | Real-time? | 15-min Data? | Ease of Setup | Best For |
|----------|------|------------|--------------|---------------|----------|
| **Yahoo Finance** | Free | Delayed 15-20 min | ✓ | ⭐⭐⭐⭐⭐ | Backtesting, research |
| **Alpaca** | Free | ✓ Real-time | ✓ | ⭐⭐⭐⭐ | Live trading, paper trading |
| **Interactive Brokers** | Free with account | ✓ Real-time | ✓ | ⭐⭐⭐ | Professional trading |
| **Polygon.io** | $99/mo | ✓ Real-time | ✓ | ⭐⭐⭐⭐ | Data-intensive apps |
| **Alpha Vantage** | Free tier | Delayed | ✓ | ⭐⭐⭐⭐ | Small projects |

## Option 1: Yahoo Finance (Already Implemented)

**Pros**: Free, no API key needed, easy
**Cons**: 15-20 minute delay, rate limits

```bash
# Already works out of the box
python cointegration_pairs_trading.py
```

That's it! The code already uses yfinance.

## Option 2: Alpaca (Recommended for Live Trading)

**Pros**: Free, real-time data, paper trading, easy API
**Cons**: US stocks only

### Setup Steps:

1. **Create free account**: https://alpaca.markets/
2. **Get API keys** from dashboard (use paper trading first)
3. **Install library**:
   ```bash
   pip install alpaca-trade-api
   ```

4. **Use it**:
   ```python
   from data_providers import FlexibleCointegrationPairsTrading, AlpacaProvider

   provider = AlpacaProvider(
       api_key='YOUR_API_KEY',
       secret_key='YOUR_SECRET_KEY',
       base_url='https://paper-api.alpaca.markets'  # Paper trading
   )

   model = FlexibleCointegrationPairsTrading(
       symbol1='CVX',
       symbol2='XOM',
       data_provider=provider,
       z_entry=2.0
   )

   data = model.load_data(period='60D', interval='15Min')
   ```

## Option 3: Interactive Brokers

**Pros**: Professional grade, real-time, low commissions
**Cons**: More complex setup, requires TWS/Gateway running

### Setup Steps:

1. **Open IBKR account**: https://www.interactivebrokers.com/
2. **Install TWS or IB Gateway**
3. **Enable API access** in TWS settings
4. **Install library**:
   ```bash
   pip install ibapi
   ```

5. **Code example**:
   ```python
   from ibapi.client import EClient
   from ibapi.wrapper import EWrapper
   from ibapi.contract import Contract

   # More complex - see IBKR API documentation
   ```

## Option 4: Polygon.io

**Pros**: Excellent API, historical + real-time, reliable
**Cons**: Costs $99/month for real-time

### Setup Steps:

1. **Sign up**: https://polygon.io/
2. **Get API key**
3. **Install library**:
   ```bash
   pip install polygon-api-client
   ```

4. **Use it**:
   ```python
   from data_providers import FlexibleCointegrationPairsTrading, PolygonProvider

   provider = PolygonProvider(api_key='YOUR_API_KEY')

   model = FlexibleCointegrationPairsTrading(
       symbol1='CVX',
       symbol2='XOM',
       data_provider=provider
   )

   data = model.load_data(period='60d', interval='15m')
   ```

## Option 5: From CSV Files (Offline)

If you have your own data files:

```python
from data_providers import FlexibleCointegrationPairsTrading, CSVProvider

# Your CSV files should have: timestamp, open, high, low, close, volume
# Example: data/CVX_15min.csv, data/XOM_15min.csv

provider = CSVProvider(csv_path_template='data/{symbol}_15min.csv')

model = FlexibleCointegrationPairsTrading(
    symbol1='CVX',
    symbol2='XOM',
    data_provider=provider
)

data = model.load_data()
```

## Live Trading Setup (Real-time Signals)

For continuous live trading, you'll want to:

1. **Stream data** instead of downloading batches
2. **Update signals** as new bars close
3. **Execute trades** automatically

Example with Alpaca:

```python
import alpaca_trade_api as tradeapi
import time

# Initialize connection
api = tradeapi.REST(
    key_id='YOUR_KEY',
    secret_key='YOUR_SECRET',
    base_url='https://paper-api.alpaca.markets'
)

# Subscribe to data stream
conn = tradeapi.stream2.StreamConn(
    key_id='YOUR_KEY',
    secret_key='YOUR_SECRET',
    base_url='https://paper-api.alpaca.markets'
)

@conn.on(r'^AM\.(CVX|XOM)$')
async def on_bar(conn, channel, bar):
    """Called when new 15-min bar closes"""
    # Update your model
    # Check for signals
    # Execute trades if needed
    pass

# Run the stream
conn.run(['AM.CVX', 'AM.XOM'])
```

## My Recommendation

**For learning/backtesting**: Use Yahoo Finance (free, already working)

**For paper trading**: Use Alpaca (free, real-time, easy to set up)

**For live trading**:
- Small account: Alpaca ($0 commissions)
- Serious trader: Interactive Brokers (professional tools, low costs)

## Need Help?

The `data_providers.py` file includes flexible adapters for all these sources. You can easily switch between providers without changing your trading logic.

```python
# Just swap the provider!
provider = YFinanceProvider()  # or AlpacaProvider() or PolygonProvider()
model = FlexibleCointegrationPairsTrading(
    symbol1='CVX',
    symbol2='XOM',
    data_provider=provider
)
```
