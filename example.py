"""
Example usage of the Cointegration Pairs Trading Strategy
"""

from cointegration_pairs_trading import CointegrationPairsTrading
import config


def run_default_strategy():
    """
    Run the strategy with default parameters from config.py
    """
    print("Running Cointegration Pairs Trading Strategy")
    print("=" * 60)

    # Initialize model
    model = CointegrationPairsTrading(
        symbol1=config.SYMBOL1,
        symbol2=config.SYMBOL2,
        lookback_period=config.LOOKBACK_PERIOD,
        z_entry=config.Z_ENTRY,
        z_exit=config.Z_EXIT,
        stop_loss=config.STOP_LOSS
    )

    # Run full analysis
    results = model.run_full_analysis(
        period=config.DATA_PERIOD,
        interval=config.DATA_INTERVAL,
        rolling_window=config.ROLLING_WINDOW,
        initial_capital=config.INITIAL_CAPITAL
    )

    # Save results
    results.to_csv(config.RESULTS_CSV)
    print(f"\nResults saved to: {config.RESULTS_CSV}")
    print(f"Chart saved to: {config.CHART_PNG}")

    return model, results


def run_aggressive_strategy():
    """
    Run a more aggressive version with tighter entry/exit thresholds
    """
    print("\nRunning AGGRESSIVE Strategy (tighter thresholds)")
    print("=" * 60)

    model = CointegrationPairsTrading(
        symbol1='CVX',
        symbol2='XOM',
        z_entry=1.5,      # More frequent entries
        z_exit=0.3,       # Quicker exits
        stop_loss=3.0
    )

    results = model.run_full_analysis(
        period='60d',
        interval='15m',
        rolling_window=100,
        initial_capital=100000
    )

    model.plot_results('aggressive_strategy.png')

    return model, results


def run_conservative_strategy():
    """
    Run a more conservative version with wider entry/exit thresholds
    """
    print("\nRunning CONSERVATIVE Strategy (wider thresholds)")
    print("=" * 60)

    model = CointegrationPairsTrading(
        symbol1='CVX',
        symbol2='XOM',
        z_entry=2.5,      # Less frequent entries
        z_exit=0.7,       # Hold positions longer
        stop_loss=4.0
    )

    results = model.run_full_analysis(
        period='60d',
        interval='15m',
        rolling_window=100,
        initial_capital=100000
    )

    model.plot_results('conservative_strategy.png')

    return model, results


if __name__ == "__main__":
    # Run default strategy
    model, results = run_default_strategy()

    # Uncomment to test other strategies:
    # aggressive_model, aggressive_results = run_aggressive_strategy()
    # conservative_model, conservative_results = run_conservative_strategy()
