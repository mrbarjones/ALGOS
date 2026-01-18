"""
Configuration file for Cointegration Pairs Trading Strategy
"""

# Trading pair symbols
SYMBOL1 = 'CVX'  # Chevron
SYMBOL2 = 'XOM'  # Exxon Mobil

# Data parameters
DATA_PERIOD = '60d'        # Historical data period
DATA_INTERVAL = '15m'      # 15-minute timeframe

# Strategy parameters
LOOKBACK_PERIOD = 60       # Days for cointegration calculation
ROLLING_WINDOW = 100       # Periods for z-score rolling statistics

# Signal thresholds
Z_ENTRY = 2.0             # Entry threshold (±2 standard deviations)
Z_EXIT = 0.5              # Exit threshold (±0.5 standard deviations)
STOP_LOSS = 3.5           # Stop loss threshold (±3.5 standard deviations)

# Backtesting parameters
INITIAL_CAPITAL = 100000  # Starting capital ($100,000)
TRANSACTION_COST = 0.001  # 0.1% transaction cost per trade

# Output files
RESULTS_CSV = 'cointegration_results.csv'
CHART_PNG = 'cointegration_analysis.png'
