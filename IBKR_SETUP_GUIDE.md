# Interactive Brokers (IBKR) Setup Guide

Complete guide to setting up live data from Interactive Brokers for your cointegration trading model.

## Prerequisites

1. **IBKR Account** (paper trading or live)
   - Sign up at: https://www.interactivebrokers.com/
   - Complete account application
   - Paper trading account is free and perfect for testing

2. **TWS or IB Gateway**
   - Download from: https://www.interactivebrokers.com/en/trading/tws.php
   - TWS = Full trading platform (recommended for beginners)
   - IB Gateway = Lightweight API-only version (for production)

## Step 1: Install IB Gateway or TWS

### Option A: TWS (Trader Workstation) - Recommended for Testing

1. Download TWS for your OS
2. Install and launch
3. Log in with your credentials (paper or live)

### Option B: IB Gateway - Lightweight for Production

1. Download IB Gateway
2. Install and launch
3. Log in with credentials

## Step 2: Configure API Access

### In TWS:

1. **Enable API**:
   - File → Global Configuration → API → Settings
   - Check "Enable ActiveX and Socket Clients"
   - Check "Read-Only API" (for safety during testing)
   - Socket port: Keep default (7497 for paper, 7496 for live)

2. **Trusted IPs**:
   - Add `127.0.0.1` (localhost) to trusted IPs
   - This allows your Python code to connect

3. **Other Settings**:
   - Uncheck "Download open orders on connection" (optional)
   - Set "Master API client ID" if needed
   - Click "OK" and restart TWS

### In IB Gateway:

1. Configure → Settings → API → Settings
2. Same settings as TWS above
3. Port defaults: 4002 (paper), 4001 (live)

## Step 3: Install Python Dependencies

```bash
pip install ibapi
```

Or add to your existing requirements:
```bash
echo "ibapi>=9.81.1" >> requirements.txt
pip install -r requirements.txt
```

## Step 4: Test Connection

Run the test script:

```python
python ibkr_provider.py
```

Expected output:
```
============================================================
IBKR Historical Data Example
============================================================
[IBKR] Connecting to 127.0.0.1:7497...
[IBKR] Connected! Next valid order ID: 1
[IBKR] Successfully connected!
[IBKR] Requesting 15 mins bars for CVX (duration: 60 D)...
[IBKR] Received 2000 bars for CVX
[IBKR] Requesting 15 mins bars for XOM (duration: 60 D)...
[IBKR] Received 2000 bars for XOM
[IBKR] Combined data: 2000 aligned bars
```

## Step 5: Integrate with Trading Model

Use the IBKR provider with your cointegration model:

```python
from cointegration_pairs_trading_demo import CointegrationPairsTrading
from ibkr_provider import IBKRDataProvider

# Initialize IBKR connection
ibkr = IBKRDataProvider(
    host='127.0.0.1',
    port=7497,  # TWS paper trading
    client_id=1
)

# Connect
ibkr.connect_and_run()

# Fetch data
data = ibkr.fetch_data(
    symbol1='CVX',
    symbol2='XOM',
    duration='60 D',
    bar_size='15 mins'
)

# Run trading model
model = CointegrationPairsTrading(
    symbol1='CVX',
    symbol2='XOM',
    z_entry=2.0,
    z_exit=0.5,
    stop_loss=3.5
)

# Use IBKR data instead of synthetic
results = model.load_data(data=data, use_synthetic=False)
model.test_cointegration()
model.calculate_signals()
model.backtest()
model.plot_results()

# Disconnect
ibkr.disconnect_client()
```

## Port Reference

| Platform | Type | Port |
|----------|------|------|
| TWS | Paper Trading | 7497 |
| TWS | Live Trading | 7496 |
| IB Gateway | Paper Trading | 4002 |
| IB Gateway | Live Trading | 4001 |

**Use paper trading (7497/4002) for testing!**

## Common Issues & Solutions

### Issue: Connection Refused

**Solution**:
- Make sure TWS/Gateway is running
- Check that API is enabled in settings
- Verify correct port number
- Ensure `127.0.0.1` is in trusted IPs

### Issue: "Connection rejected"

**Solution**:
- Close TWS completely and restart
- Check that another client isn't already connected with same client_id
- Try a different client_id (1, 2, 3, etc.)

### Issue: "No data received"

**Solution**:
- Verify you have market data subscription for US stocks
- Check that trading hours are active (or use `useRTH=0`)
- Try a shorter duration (e.g., '10 D' instead of '60 D')
- Check TWS messages for data permission errors

### Issue: "Historical data bar size setting is invalid"

**Solution**:
Valid bar sizes for `reqHistoricalData`:
- `1 secs`, `5 secs`, `10 secs`, `15 secs`, `30 secs`
- `1 min`, `2 mins`, `3 mins`, `5 mins`, `10 mins`, `15 mins`, `20 mins`, `30 mins`
- `1 hour`, `2 hours`, `3 hours`, `4 hours`, `8 hours`
- `1 day`, `1 week`, `1 month`

### Issue: Data Pacing Violations

**Solution**:
- IBKR limits: 60 requests per 10 minutes for historical data
- Add delays between requests:
  ```python
  import time
  df1 = ibkr.fetch_historical_bars('CVX')
  time.sleep(2)  # Wait 2 seconds
  df2 = ibkr.fetch_historical_bars('XOM')
  ```

## Data Availability

### Historical Data Limits by Bar Size

| Bar Size | Max Duration |
|----------|--------------|
| 1 sec - 30 secs | 1 day |
| 1 min | 30 days |
| 2 mins - 30 mins | 60 days |
| 1 hour | 180 days |
| 1 day | Years |

**For 15-minute bars**: You can fetch up to **60 days** of history.

## Live Streaming Data

For real-time trading, use the live streaming example:

```python
from ibkr_provider import IBKRLiveDataProvider

provider = IBKRLiveDataProvider(port=7497)
provider.connect_and_run()

def on_bar(bar_data):
    print(f"New bar: {bar_data}")
    # Update your trading model here

# Stream CVX and XOM
cvx_req = provider.stream_realtime_bars('CVX', callback=on_bar)
xom_req = provider.stream_realtime_bars('XOM', callback=on_bar)

# Keep streaming...
```

**Note**: IBKR provides 5-second real-time bars. You'll need to aggregate these into 15-minute bars yourself.

## Market Data Subscriptions

### Paper Trading Account
- **US Stocks**: Usually included for free
- **Real-time quotes**: Delayed by 15 minutes unless you have subscriptions

### Live Trading Account
- **US Securities Snapshot and Futures Value Bundle**: $4.50/month
- Or free with $30+ commissions per month
- Check: Account → Market Data Subscriptions in TWS

## Security Best Practices

1. **Always start with paper trading**
2. **Use Read-Only API** during testing
3. **Never share API credentials**
4. **Set Master API client ID** to control which client can place orders
5. **Monitor TWS Audit Trail** (in TWS: Account → Audit Trail)
6. **Use different client_ids** for different applications
7. **Implement error handling** for all API calls
8. **Log all activity** for debugging

## Complete Example Script

See `run_ibkr_model.py` for a complete integration example.

## Next Steps

1. ✓ Set up TWS/Gateway with API enabled
2. ✓ Test connection with `ibkr_provider.py`
3. ✓ Fetch historical data
4. ✓ Run cointegration model with IBKR data
5. [ ] Test with paper trading account
6. [ ] Implement live streaming if needed
7. [ ] Add trade execution (separate guide)

## Support

- **IBKR API Documentation**: https://www.interactivebrokers.com/en/software/api/api.htm
- **IBKR Python API Guide**: https://interactivebrokers.github.io/tws-api/
- **Community Forums**: https://www.ibkrtraders.com/

## Troubleshooting Checklist

Before asking for help, verify:
- [ ] TWS/Gateway is running
- [ ] Logged in with correct account (paper vs live)
- [ ] API is enabled in Global Configuration
- [ ] Correct port number for your setup
- [ ] `127.0.0.1` is in trusted IPs
- [ ] No other applications using same client_id
- [ ] Market data subscription is active
- [ ] Using valid bar size and duration combination
- [ ] Not exceeding API rate limits
