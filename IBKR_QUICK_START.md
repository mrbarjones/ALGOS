# IBKR Quick Start - 5 Minute Setup

Get your cointegration trading model running with IBKR live data in 5 minutes.

## 1. Install Dependencies (1 minute)

```bash
pip install ibapi
```

## 2. Configure TWS/Gateway (2 minutes)

### Launch TWS:
1. Open Trader Workstation (TWS)
2. Log in with paper trading account

### Enable API:
1. **File** → **Global Configuration** → **API** → **Settings**
2. ✓ Check "**Enable ActiveX and Socket Clients**"
3. ✓ Check "**Read-Only API**" (for safety)
4. Add `127.0.0.1` to **Trusted IPs**
5. Click **OK** and **restart TWS**

**Important**: Make sure TWS stays open while running your code!

## 3. Test Connection (1 minute)

```bash
python ibkr_provider.py
```

Expected output:
```
[IBKR] Connecting to 127.0.0.1:7497...
[IBKR] Connected! Next valid order ID: 1
[IBKR] Successfully connected!
```

## 4. Run Trading Model (1 minute)

```bash
python run_ibkr_model.py
```

This will:
- Connect to IBKR
- Fetch 60 days of 15-minute bars for CVX and XOM
- Run cointegration analysis
- Generate trading signals
- Backtest the strategy
- Create visualizations

## Quick Reference

### Port Numbers
```
TWS Paper Trading:    7497  ← Use this for testing
TWS Live Trading:     7496
Gateway Paper:        4002
Gateway Live:         4001
```

### Connection Settings

Edit in `run_ibkr_model.py`:
```python
IBKR_HOST = '127.0.0.1'
IBKR_PORT = 7497        # Change if using different platform
CLIENT_ID = 1           # Change if connection conflicts
```

### Customize Strategy

```python
SYMBOL1 = 'CVX'         # First symbol
SYMBOL2 = 'XOM'         # Second symbol
Z_ENTRY = 2.0           # Entry threshold
Z_EXIT = 0.5            # Exit threshold
STOP_LOSS = 3.5         # Stop loss threshold
```

## Common Issues

### "Connection refused"
- ✓ Is TWS/Gateway running?
- ✓ Is API enabled? (Step 2 above)
- ✓ Using correct port? (7497 for TWS paper)

### "No data received"
- ✓ Market hours? (Or set `useRTH=0` in code)
- ✓ Market data subscription active?
- ✓ Try shorter duration: `DURATION = '10 D'`

### "Duplicate client ID"
- ✓ Another app connected? Close it.
- ✓ Change `CLIENT_ID = 2` in code

## Simple Integration Example

```python
from ibkr_provider import IBKRDataProvider
from cointegration_pairs_trading_demo import CointegrationPairsTrading

# Connect to IBKR
ibkr = IBKRDataProvider(port=7497)
ibkr.connect_and_run()

# Get data
data = ibkr.fetch_data('CVX', 'XOM', duration='60 D', bar_size='15 mins')

# Run model
model = CointegrationPairsTrading('CVX', 'XOM')
model.load_data(data=data, use_synthetic=False)
model.test_cointegration()
model.calculate_signals()
model.backtest()
model.plot_results()

# Disconnect
ibkr.disconnect_client()
```

## Output Files

After running `run_ibkr_model.py`:

```
ibkr_raw_data.csv                  - Raw OHLCV data from IBKR
ibkr_backtest_results.csv          - Complete backtest with signals
ibkr_cointegration_analysis.png    - Performance charts
ibkr_trading_report.txt            - Summary report
```

## Next Steps

1. ✓ Test with paper trading
2. Review results in generated files
3. Adjust parameters (z-scores, symbols)
4. Implement live trading if satisfied

## Full Documentation

- Complete setup: `IBKR_SETUP_GUIDE.md`
- API reference: `ibkr_provider.py`
- Strategy details: `README.md`

## Need Help?

Check `IBKR_SETUP_GUIDE.md` for:
- Detailed troubleshooting
- Advanced configuration
- Live streaming setup
- Market data subscriptions
- Security best practices
