"""
Run Cointegration Pairs Trading Model with IBKR Live Data

This script demonstrates how to:
1. Connect to Interactive Brokers TWS/Gateway
2. Fetch historical 15-minute data for CVX and XOM
3. Run the cointegration analysis
4. Generate trading signals
5. Backtest the strategy
6. Save results and visualizations
"""

import sys
from datetime import datetime
from ibkr_provider import IBKRDataProvider
from cointegration_pairs_trading_demo import CointegrationPairsTrading


def main():
    """Main execution function"""

    print("\n" + "="*70)
    print("COINTEGRATION PAIRS TRADING - IBKR LIVE DATA")
    print("="*70)

    # ========== CONFIGURATION ==========
    # IBKR Connection Settings
    IBKR_HOST = '127.0.0.1'
    IBKR_PORT = 7497  # TWS paper: 7497, TWS live: 7496, Gateway paper: 4002, Gateway live: 4001
    CLIENT_ID = 1

    # Trading Symbols
    SYMBOL1 = 'CVX'   # Chevron
    SYMBOL2 = 'XOM'   # Exxon Mobil

    # Data Settings
    DURATION = '60 D'      # How far back to fetch (max 60 days for 15-min bars)
    BAR_SIZE = '15 mins'   # Bar interval

    # Strategy Parameters
    Z_ENTRY = 2.0      # Enter trade when z-score reaches ±2.0
    Z_EXIT = 0.5       # Exit trade when z-score returns to ±0.5
    STOP_LOSS = 3.5    # Stop loss at ±3.5 z-score

    # Backtest Settings
    ROLLING_WINDOW = 100    # Periods for z-score calculation
    INITIAL_CAPITAL = 100000  # Starting capital

    print(f"\nConfiguration:")
    print(f"  IBKR Connection: {IBKR_HOST}:{IBKR_PORT}")
    print(f"  Symbols: {SYMBOL1} / {SYMBOL2}")
    print(f"  Bar Size: {BAR_SIZE}")
    print(f"  Duration: {DURATION}")
    print(f"  Z-Entry: ±{Z_ENTRY}, Z-Exit: ±{Z_EXIT}, Stop Loss: ±{STOP_LOSS}")
    print()

    # ========== STEP 1: CONNECT TO IBKR ==========
    print("STEP 1: Connecting to Interactive Brokers...")
    print("-" * 70)

    ibkr = IBKRDataProvider(
        host=IBKR_HOST,
        port=IBKR_PORT,
        client_id=CLIENT_ID
    )

    try:
        # Connect to IBKR
        if not ibkr.connect_and_run():
            print("[ERROR] Failed to connect to IBKR. Please check:")
            print("  - TWS or IB Gateway is running")
            print("  - API is enabled in Global Configuration")
            print("  - Correct port number")
            print("  - 127.0.0.1 is in trusted IPs")
            sys.exit(1)

        # ========== STEP 2: FETCH DATA ==========
        print("\n" + "="*70)
        print("STEP 2: Fetching Historical Data from IBKR")
        print("-" * 70)

        data = ibkr.fetch_data(
            symbol1=SYMBOL1,
            symbol2=SYMBOL2,
            duration=DURATION,
            bar_size=BAR_SIZE
        )

        if data.empty:
            print("[ERROR] No data received from IBKR")
            sys.exit(1)

        print(f"\n✓ Successfully fetched {len(data)} bars")
        print(f"  Date range: {data.index[0]} to {data.index[-1]}")
        print(f"\nData preview:")
        print(data.head())

        # Save raw data
        data.to_csv('ibkr_raw_data.csv')
        print(f"\n✓ Raw data saved to: ibkr_raw_data.csv")

        # ========== STEP 3: INITIALIZE TRADING MODEL ==========
        print("\n" + "="*70)
        print("STEP 3: Initializing Cointegration Trading Model")
        print("-" * 70)

        model = CointegrationPairsTrading(
            symbol1=SYMBOL1,
            symbol2=SYMBOL2,
            z_entry=Z_ENTRY,
            z_exit=Z_EXIT,
            stop_loss=STOP_LOSS
        )

        # ========== STEP 4: RUN ANALYSIS ==========
        print("\n" + "="*70)
        print("STEP 4: Running Cointegration Analysis")
        print("-" * 70)

        # Load data into model
        model.load_data(data=data, use_synthetic=False)

        # Test cointegration
        coint_results = model.test_cointegration()

        # Check if pairs are cointegrated
        if coint_results['coint_pvalue'] >= 0.05:
            print("\n[WARNING] P-value >= 0.05. Pairs may not be strongly cointegrated.")
            print("Strategy may not perform well. Consider:")
            print("  - Using different time period")
            print("  - Trying different stock pairs")
            print("  - Adjusting parameters")
            print("\nContinuing anyway for demonstration...")

        # ========== STEP 5: GENERATE SIGNALS ==========
        print("\n" + "="*70)
        print("STEP 5: Generating Trading Signals")
        print("-" * 70)

        model.calculate_signals(rolling_window=ROLLING_WINDOW)

        # ========== STEP 6: BACKTEST ==========
        print("\n" + "="*70)
        print("STEP 6: Backtesting Strategy")
        print("-" * 70)

        model.backtest(initial_capital=INITIAL_CAPITAL)

        # ========== STEP 7: VISUALIZE RESULTS ==========
        print("\n" + "="*70)
        print("STEP 7: Generating Visualizations")
        print("-" * 70)

        model.plot_results('ibkr_cointegration_analysis.png')

        # ========== STEP 8: SAVE RESULTS ==========
        print("\n" + "="*70)
        print("STEP 8: Saving Results")
        print("-" * 70)

        results_df = model.data
        results_df.to_csv('ibkr_backtest_results.csv')
        print("✓ Backtest results saved to: ibkr_backtest_results.csv")

        # Generate summary report
        generate_summary_report(model, coint_results, INITIAL_CAPITAL)

        # ========== COMPLETED ==========
        print("\n" + "="*70)
        print("ANALYSIS COMPLETE!")
        print("="*70)
        print("\nGenerated files:")
        print("  - ibkr_raw_data.csv             : Raw price data from IBKR")
        print("  - ibkr_backtest_results.csv     : Complete backtest results")
        print("  - ibkr_cointegration_analysis.png : Performance visualizations")
        print("  - ibkr_trading_report.txt       : Summary report")
        print("\nNext steps:")
        print("  1. Review the visualizations and metrics")
        print("  2. Adjust parameters if needed (z_entry, z_exit, etc.)")
        print("  3. Test with paper trading before going live")
        print("  4. Consider implementing live trade execution")

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Shutting down...")

    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Always disconnect from IBKR
        print("\nDisconnecting from IBKR...")
        ibkr.disconnect_client()
        print("✓ Disconnected\n")


def generate_summary_report(model, coint_results, initial_capital):
    """Generate a text summary report"""

    results = model.data
    final_value = results['portfolio_value'].iloc[-1]
    total_return = (final_value / initial_capital - 1) * 100

    report = f"""
{'='*70}
COINTEGRATION PAIRS TRADING - SUMMARY REPORT
{'='*70}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SYMBOLS: {model.symbol1} / {model.symbol2}

COINTEGRATION TEST RESULTS
{'-'*70}
Engle-Granger P-value:  {coint_results['coint_pvalue']:.6f}
Cointegrated?:          {'Yes (p < 0.05)' if coint_results['coint_pvalue'] < 0.05 else 'No (p >= 0.05)'}
Hedge Ratio:            {coint_results['hedge_ratio']:.4f}
ADF P-value (spread):   {coint_results['adf_pvalue']:.6f}

STRATEGY PARAMETERS
{'-'*70}
Z-Score Entry:          ±{model.z_entry}
Z-Score Exit:           ±{model.z_exit}
Stop Loss:              ±{model.stop_loss}

TRADING STATISTICS
{'-'*70}
Total Trade Entries:    {(results['signal'] != 0).sum()}
Long Spread Trades:     {(results['signal'] == 1).sum()}
Short Spread Trades:    {(results['signal'] == -1).sum()}
Z-Score Range:          [{results['z_score'].min():.2f}, {results['z_score'].max():.2f}]

PERFORMANCE METRICS
{'-'*70}
Initial Capital:        ${initial_capital:,.2f}
Final Portfolio Value:  ${final_value:,.2f}
Total Return:           {total_return:.2f}%

Data Period:            {results.index[0]} to {results.index[-1]}
Total Bars:             {len(results)}

INTERPRETATION
{'-'*70}
"""

    # Add interpretation
    if coint_results['coint_pvalue'] < 0.05:
        report += "✓ Pairs are statistically cointegrated - good for mean reversion\n"
    else:
        report += "✗ Pairs may not be cointegrated - strategy may underperform\n"

    if total_return > 0:
        report += f"✓ Strategy was profitable with {total_return:.2f}% return\n"
    else:
        report += f"✗ Strategy lost {abs(total_return):.2f}%\n"

    report += f"\n{'='*70}\n"

    # Save to file
    with open('ibkr_trading_report.txt', 'w') as f:
        f.write(report)

    # Print to console
    print(report)


if __name__ == "__main__":
    main()
