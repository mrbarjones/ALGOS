"""
Interactive Brokers Data Provider for Cointegration Trading Model
Fetches live and historical 15-minute bar data from IBKR TWS/Gateway
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import threading
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import BarData


class IBKRDataProvider(EWrapper, EClient):
    """
    Interactive Brokers data provider with historical and live data support
    """

    def __init__(self, host='127.0.0.1', port=7497, client_id=1):
        """
        Initialize IBKR connection

        Parameters:
        -----------
        host : str
            TWS/Gateway host (default: '127.0.0.1')
        port : int
            TWS paper trading: 7497, TWS live: 7496
            Gateway paper: 4002, Gateway live: 4001
        client_id : int
            Unique client identifier
        """
        EClient.__init__(self, self)

        self.host = host
        self.port = port
        self.client_id = client_id

        # Data storage
        self.historical_data = {}
        self.data_ready = {}
        self.errors = []

        # Request tracking
        self.next_req_id = 1
        self.req_id_map = {}

        # Connection status
        self.connected = False
        self.api_thread = None

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        """Handle errors from IBKR"""
        error_msg = f"Error {errorCode}: {errorString}"
        print(f"[ERROR] ReqID {reqId}: {error_msg}")
        self.errors.append(error_msg)

        # Mark data as ready even on error to avoid hanging
        if reqId in self.data_ready:
            self.data_ready[reqId] = True

    def nextValidId(self, orderId: int):
        """Callback when connection is established"""
        super().nextValidId(orderId)
        self.next_req_id = orderId
        self.connected = True
        print(f"[IBKR] Connected! Next valid order ID: {orderId}")

    def historicalData(self, reqId, bar: BarData):
        """Callback for each historical bar received"""
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []

        self.historical_data[reqId].append({
            'timestamp': pd.Timestamp(bar.date),
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        })

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        """Callback when all historical data is received"""
        print(f"[IBKR] Historical data complete for request {reqId}")
        self.data_ready[reqId] = True

    def connect_and_run(self):
        """Connect to IBKR and run the message loop"""
        try:
            print(f"[IBKR] Connecting to {self.host}:{self.port}...")
            self.connect(self.host, self.port, self.client_id)

            # Start the socket in a thread
            self.api_thread = threading.Thread(target=self.run, daemon=True)
            self.api_thread.start()

            # Wait for connection
            timeout = 10
            start = time.time()
            while not self.connected and time.time() - start < timeout:
                time.sleep(0.1)

            if not self.connected:
                raise ConnectionError("Failed to connect to IBKR within timeout")

            print("[IBKR] Successfully connected!")
            return True

        except Exception as e:
            print(f"[IBKR] Connection failed: {e}")
            return False

    def disconnect_client(self):
        """Disconnect from IBKR"""
        if self.connected:
            self.disconnect()
            self.connected = False
            print("[IBKR] Disconnected")

    def create_stock_contract(self, symbol, exchange='SMART', currency='USD'):
        """
        Create a stock contract for IBKR API

        Parameters:
        -----------
        symbol : str
            Stock ticker (e.g., 'CVX', 'XOM')
        exchange : str
            Exchange (default: 'SMART' for intelligent routing)
        currency : str
            Currency (default: 'USD')

        Returns:
        --------
        Contract object
        """
        contract = Contract()
        contract.symbol = symbol
        contract.secType = 'STK'
        contract.exchange = exchange
        contract.currency = currency
        return contract

    def fetch_historical_bars(self, symbol, duration='60 D', bar_size='15 mins',
                             exchange='SMART', what_to_show='TRADES'):
        """
        Fetch historical bar data from IBKR

        Parameters:
        -----------
        symbol : str
            Stock ticker
        duration : str
            How far back to fetch ('60 D', '1 M', '1 Y', etc.)
        bar_size : str
            Bar size ('1 min', '5 mins', '15 mins', '1 hour', '1 day')
        exchange : str
            Exchange (default: 'SMART')
        what_to_show : str
            Data type ('TRADES', 'MIDPOINT', 'BID', 'ASK')

        Returns:
        --------
        pd.DataFrame with OHLCV data
        """
        if not self.connected:
            self.connect_and_run()

        # Create contract
        contract = self.create_stock_contract(symbol, exchange)

        # Get request ID
        req_id = self.next_req_id
        self.next_req_id += 1

        # Initialize storage
        self.historical_data[req_id] = []
        self.data_ready[req_id] = False
        self.req_id_map[req_id] = symbol

        # Request data
        end_datetime = datetime.now().strftime('%Y%m%d %H:%M:%S')
        print(f"[IBKR] Requesting {bar_size} bars for {symbol} (duration: {duration})...")

        self.reqHistoricalData(
            req_id,
            contract,
            end_datetime,
            duration,
            bar_size,
            what_to_show,
            0,  # useRTH: 1=regular trading hours only, 0=all hours (includes pre/post market)
            1,  # formatDate: 1=yyyyMMdd HH:mm:ss, 2=epoch
            False,  # keepUpToDate
            []  # chartOptions
        )

        # Wait for data
        timeout = 30
        start = time.time()
        while not self.data_ready[req_id] and time.time() - start < timeout:
            time.sleep(0.1)

        if not self.data_ready[req_id]:
            print(f"[IBKR] Timeout waiting for {symbol} data")
            return pd.DataFrame()

        # Convert to DataFrame
        if req_id in self.historical_data and self.historical_data[req_id]:
            df = pd.DataFrame(self.historical_data[req_id])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            print(f"[IBKR] Received {len(df)} bars for {symbol}")
            return df
        else:
            print(f"[IBKR] No data received for {symbol}")
            return pd.DataFrame()

    def fetch_data(self, symbol1, symbol2, duration='60 D', bar_size='15 mins'):
        """
        Fetch data for both symbols (compatible with data_providers.py interface)

        Parameters:
        -----------
        symbol1 : str
            First ticker (CVX)
        symbol2 : str
            Second ticker (XOM)
        duration : str
            Period to fetch
        bar_size : str
            Bar interval

        Returns:
        --------
        pd.DataFrame with combined data
        """
        # Fetch data for both symbols
        df1 = self.fetch_historical_bars(symbol1, duration, bar_size)
        df2 = self.fetch_historical_bars(symbol2, duration, bar_size)

        # Combine into single DataFrame
        if df1.empty or df2.empty:
            raise ValueError("Failed to fetch data from IBKR")

        combined = pd.DataFrame({
            f'{symbol1}_close': df1['close'],
            f'{symbol2}_close': df2['close']
        }).dropna()

        print(f"[IBKR] Combined data: {len(combined)} aligned bars")
        return combined


class IBKRLiveDataProvider(IBKRDataProvider):
    """
    Extended IBKR provider with live streaming data support
    """

    def __init__(self, host='127.0.0.1', port=7497, client_id=1):
        super().__init__(host, port, client_id)

        # Live data storage
        self.live_bars = {}
        self.live_callbacks = {}

    def realtimeBar(self, reqId, time_val, open_, high, low, close, volume, wap, count):
        """Callback for real-time 5-second bars"""
        symbol = self.req_id_map.get(reqId, 'Unknown')

        bar_data = {
            'timestamp': pd.Timestamp(time_val, unit='s'),
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }

        # Store bar
        if reqId not in self.live_bars:
            self.live_bars[reqId] = []
        self.live_bars[reqId].append(bar_data)

        # Call user callback if registered
        if reqId in self.live_callbacks:
            self.live_callbacks[reqId](bar_data)

        print(f"[IBKR LIVE] {symbol}: {close} @ {bar_data['timestamp']}")

    def stream_realtime_bars(self, symbol, callback=None, exchange='SMART', what_to_show='TRADES'):
        """
        Stream real-time 5-second bars (can be aggregated to 15 minutes)

        Parameters:
        -----------
        symbol : str
            Stock ticker
        callback : function
            Function to call on each new bar: callback(bar_data)
        exchange : str
            Exchange
        what_to_show : str
            Data type

        Returns:
        --------
        req_id : int
            Request ID (use to cancel stream later)
        """
        if not self.connected:
            self.connect_and_run()

        # Create contract
        contract = self.create_stock_contract(symbol, exchange)

        # Get request ID
        req_id = self.next_req_id
        self.next_req_id += 1

        self.req_id_map[req_id] = symbol
        self.live_bars[req_id] = []

        if callback:
            self.live_callbacks[req_id] = callback

        # Request real-time bars (5-second bars)
        print(f"[IBKR] Starting real-time stream for {symbol}...")
        self.reqRealTimeBars(
            req_id,
            contract,
            5,  # Bar size in seconds (5 is minimum)
            what_to_show,
            True,  # useRTH
            []  # realTimeBarsOptions
        )

        return req_id

    def cancel_realtime_bars(self, req_id):
        """Cancel real-time bar stream"""
        self.cancelRealTimeBars(req_id)
        print(f"[IBKR] Cancelled real-time stream {req_id}")


# Example usage
def example_historical_data():
    """Example: Fetch historical 15-minute data"""
    print("="*60)
    print("IBKR Historical Data Example")
    print("="*60)

    # Initialize provider
    provider = IBKRDataProvider(
        host='127.0.0.1',
        port=7497,  # TWS paper trading port
        client_id=1
    )

    try:
        # Connect
        provider.connect_and_run()

        # Fetch data for CVX and XOM
        data = provider.fetch_data(
            symbol1='CVX',
            symbol2='XOM',
            duration='60 D',
            bar_size='15 mins'
        )

        print("\n" + "="*60)
        print("Data Summary")
        print("="*60)
        print(f"\nShape: {data.shape}")
        print(f"\nFirst 5 rows:")
        print(data.head())
        print(f"\nLast 5 rows:")
        print(data.tail())

        # Save to CSV
        data.to_csv('ibkr_data.csv')
        print("\nData saved to ibkr_data.csv")

        return data

    finally:
        # Always disconnect
        provider.disconnect_client()


def example_live_stream():
    """Example: Stream real-time data"""
    print("="*60)
    print("IBKR Live Streaming Example")
    print("="*60)

    provider = IBKRLiveDataProvider(
        host='127.0.0.1',
        port=7497,
        client_id=2
    )

    def on_new_bar(bar_data):
        """Callback for each new bar"""
        print(f"New bar received: {bar_data}")

    try:
        # Connect
        provider.connect_and_run()

        # Start streaming CVX and XOM
        cvx_req = provider.stream_realtime_bars('CVX', callback=on_new_bar)
        xom_req = provider.stream_realtime_bars('XOM', callback=on_new_bar)

        print("\nStreaming live data... Press Ctrl+C to stop")

        # Stream for 60 seconds
        time.sleep(60)

        # Cancel streams
        provider.cancel_realtime_bars(cvx_req)
        provider.cancel_realtime_bars(xom_req)

    except KeyboardInterrupt:
        print("\nStopping stream...")

    finally:
        provider.disconnect_client()


if __name__ == "__main__":
    # Run historical data example
    example_historical_data()

    # Uncomment to test live streaming:
    # example_live_stream()
