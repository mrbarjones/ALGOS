"""
Cointegration Pairs Trading Strategy for CVX and XOM
15-Minute Timeframe

This model implements a pairs trading strategy based on cointegration
between Chevron (CVX) and Exxon Mobil (XOM).
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.regression.linear_model import OLS
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
sns.set_style('darkgrid')
plt.rcParams['figure.figsize'] = (15, 10)


class CointegrationPairsTrading:
    """
    Pairs trading strategy using cointegration between CVX and XOM.
    """

    def __init__(self, symbol1='CVX', symbol2='XOM', lookback_period=60,
                 z_entry=2.0, z_exit=0.5, stop_loss=3.5):
        """
        Initialize the pairs trading model.

        Parameters:
        -----------
        symbol1 : str
            First ticker symbol (CVX)
        symbol2 : str
            Second ticker symbol (XOM)
        lookback_period : int
            Number of periods for calculating rolling statistics (days for cointegration)
        z_entry : float
            Z-score threshold for entry (both +/-)
        z_exit : float
            Z-score threshold for exit
        stop_loss : float
            Z-score threshold for stop loss
        """
        self.symbol1 = symbol1
        self.symbol2 = symbol2
        self.lookback_period = lookback_period
        self.z_entry = z_entry
        self.z_exit = z_exit
        self.stop_loss = stop_loss

        self.data = None
        self.hedge_ratio = None
        self.spread = None
        self.signals = None
        self.portfolio = None

    def fetch_data(self, period='60d', interval='15m'):
        """
        Fetch 15-minute data for both symbols.

        Parameters:
        -----------
        period : str
            Period to download (e.g., '60d', '30d')
        interval : str
            Data interval ('15m' for 15 minutes)
        """
        print(f"Fetching {interval} data for {self.symbol1} and {self.symbol2}...")

        # Fetch data for both symbols
        data1 = yf.download(self.symbol1, period=period, interval=interval, progress=False)
        data2 = yf.download(self.symbol2, period=period, interval=interval, progress=False)

        # Combine into single DataFrame
        self.data = pd.DataFrame({
            f'{self.symbol1}_close': data1['Close'],
            f'{self.symbol2}_close': data2['Close']
        }).dropna()

        print(f"Downloaded {len(self.data)} data points")
        print(f"Date range: {self.data.index[0]} to {self.data.index[-1]}")

        return self.data

    def test_cointegration(self):
        """
        Test for cointegration between the two price series using Engle-Granger method.

        Returns:
        --------
        dict : Cointegration test results
        """
        print("\n" + "="*60)
        print("COINTEGRATION ANALYSIS")
        print("="*60)

        price1 = self.data[f'{self.symbol1}_close']
        price2 = self.data[f'{self.symbol2}_close']

        # Engle-Granger cointegration test
        score, pvalue, _ = coint(price1, price2)

        print(f"\nEngle-Granger Cointegration Test:")
        print(f"  Test Statistic: {score:.4f}")
        print(f"  P-value: {pvalue:.4f}")

        if pvalue < 0.05:
            print(f"  Result: ✓ Series are cointegrated (p < 0.05)")
        else:
            print(f"  Result: ✗ Series may not be cointegrated (p >= 0.05)")
            print(f"  Warning: Strategy may not perform well")

        # Calculate hedge ratio using OLS regression
        model = OLS(price1, price2).fit()
        self.hedge_ratio = model.params[0]

        print(f"\nHedge Ratio: {self.hedge_ratio:.4f}")
        print(f"  Interpretation: Long 1 {self.symbol1} : Short {self.hedge_ratio:.4f} {self.symbol2}")

        # Calculate spread
        self.data['spread'] = price1 - self.hedge_ratio * price2

        # Test stationarity of spread
        adf_result = adfuller(self.data['spread'].dropna())

        print(f"\nAugmented Dickey-Fuller Test on Spread:")
        print(f"  Test Statistic: {adf_result[0]:.4f}")
        print(f"  P-value: {adf_result[1]:.4f}")

        if adf_result[1] < 0.05:
            print(f"  Result: ✓ Spread is stationary (p < 0.05)")
        else:
            print(f"  Result: ✗ Spread may not be stationary (p >= 0.05)")

        return {
            'coint_pvalue': pvalue,
            'hedge_ratio': self.hedge_ratio,
            'adf_pvalue': adf_result[1]
        }

    def calculate_signals(self, rolling_window=100):
        """
        Calculate trading signals based on z-score of the spread.

        Parameters:
        -----------
        rolling_window : int
            Window for calculating rolling mean and std of spread
        """
        print("\n" + "="*60)
        print("GENERATING TRADING SIGNALS")
        print("="*60)

        # Calculate z-score of spread
        spread_mean = self.data['spread'].rolling(window=rolling_window).mean()
        spread_std = self.data['spread'].rolling(window=rolling_window).std()
        self.data['z_score'] = (self.data['spread'] - spread_mean) / spread_std

        # Initialize signals
        self.data['signal'] = 0
        self.data['position'] = 0

        # Track position state
        position = 0  # 0: neutral, 1: long spread, -1: short spread

        for i in range(len(self.data)):
            z = self.data['z_score'].iloc[i]

            if np.isnan(z):
                continue

            # Entry signals
            if position == 0:
                if z > self.z_entry:
                    # Short spread: Short CVX, Long XOM
                    position = -1
                    self.data.iloc[i, self.data.columns.get_loc('signal')] = -1
                elif z < -self.z_entry:
                    # Long spread: Long CVX, Short XOM
                    position = 1
                    self.data.iloc[i, self.data.columns.get_loc('signal')] = 1

            # Exit signals
            elif position == 1:  # Currently long spread
                if z > self.z_exit or z > self.stop_loss:
                    position = 0
                    self.data.iloc[i, self.data.columns.get_loc('signal')] = 0

            elif position == -1:  # Currently short spread
                if z < -self.z_exit or z < -self.stop_loss:
                    position = 0
                    self.data.iloc[i, self.data.columns.get_loc('signal')] = 0

            self.data.iloc[i, self.data.columns.get_loc('position')] = position

        # Count trades
        trades = (self.data['signal'] != 0).sum()
        long_trades = (self.data['signal'] == 1).sum()
        short_trades = (self.data['signal'] == -1).sum()

        print(f"\nSignal Statistics:")
        print(f"  Total trade entries: {trades}")
        print(f"  Long spread trades: {long_trades}")
        print(f"  Short spread trades: {short_trades}")
        print(f"  Z-score range: [{self.data['z_score'].min():.2f}, {self.data['z_score'].max():.2f}]")

        return self.data

    def backtest(self, initial_capital=100000, transaction_cost=0.001):
        """
        Backtest the pairs trading strategy.

        Parameters:
        -----------
        initial_capital : float
            Starting capital
        transaction_cost : float
            Transaction cost as fraction (0.001 = 0.1%)
        """
        print("\n" + "="*60)
        print("BACKTESTING STRATEGY")
        print("="*60)

        # Calculate returns for each leg
        self.data['cvx_returns'] = self.data[f'{self.symbol1}_close'].pct_change()
        self.data['xom_returns'] = self.data[f'{self.symbol2}_close'].pct_change()

        # Calculate spread returns
        # When position = 1 (long spread): long CVX, short XOM
        # When position = -1 (short spread): short CVX, long XOM
        self.data['spread_returns'] = (
            self.data['position'].shift(1) * self.data['cvx_returns'] -
            self.data['position'].shift(1) * self.hedge_ratio * self.data['xom_returns']
        )

        # Apply transaction costs on signal changes
        position_changes = self.data['position'].diff().abs()
        self.data['transaction_costs'] = position_changes * transaction_cost

        # Net returns after costs
        self.data['net_returns'] = self.data['spread_returns'] - self.data['transaction_costs']

        # Calculate cumulative returns
        self.data['cum_returns'] = (1 + self.data['net_returns'].fillna(0)).cumprod()
        self.data['portfolio_value'] = initial_capital * self.data['cum_returns']

        # Calculate performance metrics
        total_return = (self.data['portfolio_value'].iloc[-1] / initial_capital - 1) * 100

        # Annualized metrics (252 trading days * 26 periods per day for 15min = 6552 periods/year)
        periods_per_year = 252 * 26  # 15-min intervals
        returns = self.data['net_returns'].dropna()

        if len(returns) > 0:
            sharpe_ratio = np.sqrt(periods_per_year) * returns.mean() / returns.std() if returns.std() > 0 else 0

            # Calculate maximum drawdown
            cumulative = self.data['cum_returns']
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min() * 100

            # Win rate
            winning_returns = returns[returns > 0]
            win_rate = len(winning_returns) / len(returns) * 100 if len(returns) > 0 else 0

            print(f"\nPerformance Metrics:")
            print(f"  Initial Capital: ${initial_capital:,.2f}")
            print(f"  Final Portfolio Value: ${self.data['portfolio_value'].iloc[-1]:,.2f}")
            print(f"  Total Return: {total_return:.2f}%")
            print(f"  Sharpe Ratio: {sharpe_ratio:.2f}")
            print(f"  Maximum Drawdown: {max_drawdown:.2f}%")
            print(f"  Win Rate: {win_rate:.2f}%")
            print(f"  Total Periods: {len(self.data)}")
            print(f"  Transaction Costs: ${(self.data['transaction_costs'].sum() * initial_capital):,.2f}")

        return self.data

    def plot_results(self, save_path='cointegration_analysis.png'):
        """
        Create comprehensive visualization of the strategy.
        """
        print("\n" + "="*60)
        print("GENERATING VISUALIZATIONS")
        print("="*60)

        fig, axes = plt.subplots(4, 1, figsize=(16, 12))

        # Plot 1: Price series
        ax1 = axes[0]
        ax1_twin = ax1.twinx()

        ax1.plot(self.data.index, self.data[f'{self.symbol1}_close'],
                label=self.symbol1, color='blue', linewidth=1.5)
        ax1_twin.plot(self.data.index, self.data[f'{self.symbol2}_close'],
                     label=self.symbol2, color='red', linewidth=1.5)

        ax1.set_ylabel(f'{self.symbol1} Price', color='blue', fontsize=10)
        ax1_twin.set_ylabel(f'{self.symbol2} Price', color='red', fontsize=10)
        ax1.set_title('Price Series - CVX and XOM (15-min)', fontsize=12, fontweight='bold')
        ax1.tick_params(axis='y', labelcolor='blue')
        ax1_twin.tick_params(axis='y', labelcolor='red')
        ax1.legend(loc='upper left')
        ax1_twin.legend(loc='upper right')
        ax1.grid(True, alpha=0.3)

        # Plot 2: Spread and Z-score
        ax2 = axes[1]
        ax2_twin = ax2.twinx()

        ax2.plot(self.data.index, self.data['spread'],
                label='Spread', color='purple', linewidth=1)
        ax2_twin.plot(self.data.index, self.data['z_score'],
                     label='Z-Score', color='orange', linewidth=1.5)

        # Add threshold lines
        ax2_twin.axhline(y=self.z_entry, color='red', linestyle='--', alpha=0.7, label='Entry Threshold')
        ax2_twin.axhline(y=-self.z_entry, color='red', linestyle='--', alpha=0.7)
        ax2_twin.axhline(y=self.z_exit, color='green', linestyle='--', alpha=0.7, label='Exit Threshold')
        ax2_twin.axhline(y=-self.z_exit, color='green', linestyle='--', alpha=0.7)
        ax2_twin.axhline(y=0, color='black', linestyle='-', alpha=0.5)

        ax2.set_ylabel('Spread', color='purple', fontsize=10)
        ax2_twin.set_ylabel('Z-Score', color='orange', fontsize=10)
        ax2.set_title('Spread and Z-Score', fontsize=12, fontweight='bold')
        ax2.tick_params(axis='y', labelcolor='purple')
        ax2_twin.tick_params(axis='y', labelcolor='orange')
        ax2.legend(loc='upper left')
        ax2_twin.legend(loc='upper right')
        ax2.grid(True, alpha=0.3)

        # Plot 3: Positions
        ax3 = axes[2]
        ax3.fill_between(self.data.index, self.data['position'],
                        where=(self.data['position'] > 0),
                        color='green', alpha=0.3, label='Long Spread')
        ax3.fill_between(self.data.index, self.data['position'],
                        where=(self.data['position'] < 0),
                        color='red', alpha=0.3, label='Short Spread')
        ax3.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax3.set_ylabel('Position', fontsize=10)
        ax3.set_title('Trading Positions', fontsize=12, fontweight='bold')
        ax3.legend(loc='upper right')
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim([-1.5, 1.5])

        # Plot 4: Equity curve
        ax4 = axes[3]
        ax4.plot(self.data.index, self.data['portfolio_value'],
                color='darkgreen', linewidth=2, label='Portfolio Value')
        ax4.fill_between(self.data.index, self.data['portfolio_value'],
                        self.data['portfolio_value'].iloc[0],
                        alpha=0.2, color='green')
        ax4.set_ylabel('Portfolio Value ($)', fontsize=10)
        ax4.set_xlabel('Date', fontsize=10)
        ax4.set_title('Equity Curve', fontsize=12, fontweight='bold')
        ax4.legend(loc='upper left')
        ax4.grid(True, alpha=0.3)

        # Format y-axis as currency
        ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\nVisualization saved to: {save_path}")

        return fig

    def run_full_analysis(self, period='60d', interval='15m',
                         rolling_window=100, initial_capital=100000):
        """
        Run the complete analysis pipeline.
        """
        print("\n" + "="*60)
        print(f"COINTEGRATION PAIRS TRADING: {self.symbol1} vs {self.symbol2}")
        print("="*60)
        print(f"Timeframe: {interval}")
        print(f"Period: {period}")
        print(f"Entry Z-Score: ±{self.z_entry}")
        print(f"Exit Z-Score: ±{self.z_exit}")
        print(f"Stop Loss Z-Score: ±{self.stop_loss}")

        # Step 1: Fetch data
        self.fetch_data(period=period, interval=interval)

        # Step 2: Test cointegration
        coint_results = self.test_cointegration()

        # Step 3: Generate signals
        self.calculate_signals(rolling_window=rolling_window)

        # Step 4: Backtest
        self.backtest(initial_capital=initial_capital)

        # Step 5: Visualize
        self.plot_results()

        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)

        return self.data


def main():
    """
    Main execution function.
    """
    # Initialize the pairs trading model
    model = CointegrationPairsTrading(
        symbol1='CVX',
        symbol2='XOM',
        lookback_period=60,
        z_entry=2.0,      # Enter when z-score reaches ±2
        z_exit=0.5,       # Exit when z-score returns to ±0.5
        stop_loss=3.5     # Stop loss at ±3.5 z-score
    )

    # Run full analysis
    results = model.run_full_analysis(
        period='60d',           # Last 60 days
        interval='15m',         # 15-minute intervals
        rolling_window=100,     # 100 periods for z-score calculation
        initial_capital=100000  # $100,000 starting capital
    )

    # Save results to CSV
    results.to_csv('cointegration_results.csv')
    print("\nResults saved to: cointegration_results.csv")

    return model, results


if __name__ == "__main__":
    model, results = main()
