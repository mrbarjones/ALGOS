"""
Universal Data Adapter for Cointegration Pairs Trading
Supports multiple data sources: yfinance, Alpaca, IBKR, CSV files, etc.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from abc import ABC, abstractmethod


class DataProvider(ABC):
    """Abstract base class for data providers"""

    @abstractmethod
    def fetch_data(self, symbol1, symbol2, period, interval):
        """Fetch data for two symbols"""
        pass


class YFinanceProvider(DataProvider):
    """Yahoo Finance data provider"""

    def fetch_data(self, symbol1, symbol2, period='60d', interval='15m'):
        import yfinance as yf

        data1 = yf.download(symbol1, period=period, interval=interval, progress=False)
        data2 = yf.download(symbol2, period=period, interval=interval, progress=False)

        df = pd.DataFrame({
            f'{symbol1}_close': data1['Close'],
            f'{symbol2}_close': data2['Close']
        }).dropna()

        return df


class AlpacaProvider(DataProvider):
    """Alpaca Markets data provider"""

    def __init__(self, api_key, secret_key, base_url='https://paper-api.alpaca.markets'):
        from alpaca_trade_api import REST
        self.api = REST(api_key, secret_key, base_url)

    def fetch_data(self, symbol1, symbol2, period='60D', interval='15Min'):
        # Get bars for both symbols
        bars1 = self.api.get_bars(symbol1, interval, limit=1000).df
        bars2 = self.api.get_bars(symbol2, interval, limit=1000).df

        # Combine into single DataFrame
        df = pd.DataFrame({
            f'{symbol1}_close': bars1['close'],
            f'{symbol2}_close': bars2['close']
        }).dropna()

        return df


class PolygonProvider(DataProvider):
    """Polygon.io data provider"""

    def __init__(self, api_key):
        from polygon import RESTClient
        self.client = RESTClient(api_key)

    def fetch_data(self, symbol1, symbol2, period='60d', interval='15m'):
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=int(period.replace('d', '')))

        # Fetch aggregates
        aggs1 = self.client.get_aggs(
            ticker=symbol1,
            multiplier=int(interval.replace('m', '')),
            timespan="minute",
            from_=start_date.strftime('%Y-%m-%d'),
            to=end_date.strftime('%Y-%m-%d')
        )

        aggs2 = self.client.get_aggs(
            ticker=symbol2,
            multiplier=int(interval.replace('m', '')),
            timespan="minute",
            from_=start_date.strftime('%Y-%m-%d'),
            to=end_date.strftime('%Y-%m-%d')
        )

        # Convert to DataFrame
        df1 = pd.DataFrame([{
            'timestamp': pd.Timestamp(a.timestamp, unit='ms'),
            'close': a.close
        } for a in aggs1]).set_index('timestamp')

        df2 = pd.DataFrame([{
            'timestamp': pd.Timestamp(a.timestamp, unit='ms'),
            'close': a.close
        } for a in aggs2]).set_index('timestamp')

        df = pd.DataFrame({
            f'{symbol1}_close': df1['close'],
            f'{symbol2}_close': df2['close']
        }).dropna()

        return df


class CSVProvider(DataProvider):
    """Load data from CSV files"""

    def __init__(self, csv_path_template):
        """
        csv_path_template: String with {symbol} placeholder
        Example: 'data/{symbol}_15min.csv'
        """
        self.csv_path_template = csv_path_template

    def fetch_data(self, symbol1, symbol2, period=None, interval=None):
        # Load CSV files
        df1 = pd.read_csv(
            self.csv_path_template.format(symbol=symbol1),
            index_col=0,
            parse_dates=True
        )

        df2 = pd.read_csv(
            self.csv_path_template.format(symbol=symbol2),
            index_col=0,
            parse_dates=True
        )

        # Combine
        df = pd.DataFrame({
            f'{symbol1}_close': df1['close'],
            f'{symbol2}_close': df2['close']
        }).dropna()

        return df


class LiveDataProvider(DataProvider):
    """
    Stream live data and maintain a rolling buffer
    Useful for real-time trading
    """

    def __init__(self, data_source, buffer_size=2000):
        self.data_source = data_source  # Your live data connection
        self.buffer_size = buffer_size
        self.buffer = pd.DataFrame()

    def update_buffer(self, new_bar):
        """Add new bar to buffer and maintain size"""
        self.buffer = pd.concat([self.buffer, new_bar]).tail(self.buffer_size)

    def fetch_data(self, symbol1, symbol2, period=None, interval=None):
        """Return current buffer"""
        return self.buffer.copy()


# Modified CointegrationPairsTrading to use data providers
class FlexibleCointegrationPairsTrading:
    """
    Enhanced pairs trading model that works with any data provider
    """

    def __init__(self, symbol1='CVX', symbol2='XOM',
                 data_provider=None, **strategy_params):
        self.symbol1 = symbol1
        self.symbol2 = symbol2
        self.data_provider = data_provider or YFinanceProvider()

        # Strategy parameters
        self.z_entry = strategy_params.get('z_entry', 2.0)
        self.z_exit = strategy_params.get('z_exit', 0.5)
        self.stop_loss = strategy_params.get('stop_loss', 3.5)

        self.data = None
        self.hedge_ratio = None

    def load_data(self, period='60d', interval='15m'):
        """Load data using the configured provider"""
        print(f"Loading data from {self.data_provider.__class__.__name__}...")

        self.data = self.data_provider.fetch_data(
            self.symbol1,
            self.symbol2,
            period,
            interval
        )

        print(f"Loaded {len(self.data)} data points")
        return self.data


# Usage Examples
def example_usage():
    """Examples of using different data providers"""

    # Example 1: Yahoo Finance (default, free)
    print("Example 1: Yahoo Finance")
    model = FlexibleCointegrationPairsTrading(
        symbol1='CVX',
        symbol2='XOM',
        data_provider=YFinanceProvider(),
        z_entry=2.0
    )
    data = model.load_data(period='60d', interval='15m')

    # Example 2: Alpaca (requires API keys)
    print("\nExample 2: Alpaca")
    alpaca_provider = AlpacaProvider(
        api_key='YOUR_API_KEY',
        secret_key='YOUR_SECRET_KEY'
    )
    model = FlexibleCointegrationPairsTrading(
        symbol1='CVX',
        symbol2='XOM',
        data_provider=alpaca_provider
    )
    data = model.load_data(period='60D', interval='15Min')

    # Example 3: Polygon.io (requires API key)
    print("\nExample 3: Polygon.io")
    polygon_provider = PolygonProvider(api_key='YOUR_API_KEY')
    model = FlexibleCointegrationPairsTrading(
        symbol1='CVX',
        symbol2='XOM',
        data_provider=polygon_provider
    )
    data = model.load_data(period='60d', interval='15m')

    # Example 4: CSV files (offline)
    print("\nExample 4: CSV Files")
    csv_provider = CSVProvider(csv_path_template='data/{symbol}_15min.csv')
    model = FlexibleCointegrationPairsTrading(
        symbol1='CVX',
        symbol2='XOM',
        data_provider=csv_provider
    )
    data = model.load_data()


if __name__ == "__main__":
    example_usage()
