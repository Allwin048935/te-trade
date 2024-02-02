import ccxt
import pandas as pd
import time
from config import BINANCE_API_KEY, BINANCE_API_SECRET, symbols, time_interval, short_ema_period, medium_ema_period, long_ema_period, fixed_usdt_amount

# Set up the Binance client
exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_API_SECRET,
    'enableRateLimit': True,
})


df['short_ema'] = df['close'].ewm(alpha=2/(short_period + 1), adjust=False).mean()
df['medium_ema'] = df['close'].ewm(alpha=2/(medium_period + 1), adjust=False).mean()
df['long_ema'] = df['close'].ewm(alpha=2/(long_period + 1), adjust=False).mean()

# Function to get the current market price
def get_market_price(symbol):
    ticker = exchange.fetch_ticker(symbol)
    return ticker['last']

# Function to calculate the quantity based on fixed USDT amount
def calculate_quantity(symbol, usdt_amount):
    market_price = get_market_price(symbol)
    quantity = usdt_amount / market_price
    return quantity

# Function to place a market buy order
def place_market_buy_order(symbol, quantity):
    order = exchange.create_market_buy_order(symbol=symbol, amount=quantity)
    print(f"Market Buy Order placed for {symbol}: {order}")
    return order

# Function to place a market sell order
def place_market_sell_order(symbol, quantity):
    order = exchange.create_market_sell_order(symbol=symbol, amount=quantity)
    print(f"Market Sell Order placed for {symbol}: {order}")
    return order

# Function to place a market close order
def close_position(symbol, position_type):
    if position_type == 'long':
        place_market_sell_order(symbol, calculate_quantity(symbol, fixed_usdt_amount))
    elif position_type == 'short':
        place_market_buy_order(symbol, calculate_quantity(symbol, fixed_usdt_amount))

# Main trading function
def ema_strategy():
    position_types = {symbol: None for symbol in symbols}  # To track the current position type for each symbol
    while True:
        try:
            for symbol in symbols:
                # Fetch historical data and calculate EMAs
                data = fetch_and_calculate_emas(symbol, short_ema_period, medium_ema_period, long_ema_period, 100)

                # Check if there's enough data for EMA calculation
                if len(data) < long_ema_period:
                    print(f"Not enough data for {symbol}. Waiting for more...")
                    continue

                # Check for EMA crossovers and crossunders individually
                if (
                    data['short_ema'].iloc[-2] >= data['long_ema'].iloc[-2] and
                    data['short_ema'].iloc[-3] <= data['long_ema'].iloc[-3] and
                    data['short_ema'].iloc[-4] <= data['long_ema'].iloc[-4]
                ):
                    # Short EMA crossover Long EMA - Take Long Order
                    if position_types[symbol] != 'long':
                        close_position(symbol, position_types[symbol])  # Close any existing short position
                        position_types[symbol] = 'long'
                        place_market_buy_order(symbol, calculate_quantity(symbol, fixed_usdt_amount))
                    print(f'{symbol} Short EMA crossed over Long EMA - Take Long Order')

                if (
                    data['short_ema'].iloc[-2] <= data['medium_ema'].iloc[-2] and
                    data['short_ema'].iloc[-3] >= data['medium_ema'].iloc[-3] and
                    data['short_ema'].iloc[-4] >= data['medium_ema'].iloc[-4]
                ):
                    # Short EMA crossunder Medium EMA - Close Long Order
                    if position_types[symbol] == 'long':
                        close_position(symbol, position_types[symbol])
                        position_types[symbol] = None
                    print(f'{symbol} Short EMA crossed under Medium EMA - Close Long Order')

                if (
                    data['short_ema'].iloc[-2] <= data['long_ema'].iloc[-2] and
                    data['short_ema'].iloc[-3] >= data['long_ema'].iloc[-3] and
                    data['short_ema'].iloc[-4] >= data['long_ema'].iloc[-4]
                ):
                    # Short EMA crossunder Long EMA - Take Short Order
                    if position_types[symbol] != 'short':
                        close_position(symbol, position_types[symbol])  # Close any existing long position
                        position_types[symbol] = 'short'
                        place_market_sell_order(symbol, calculate_quantity(symbol, fixed_usdt_amount))
                    print(f'{symbol} Short EMA crossed under Long EMA - Take Short Order')

                if (
                    data['short_ema'].iloc[-2] >= data['medium_ema'].iloc[-2] and
                    data['short_ema'].iloc[-3] <= data['medium_ema'].iloc[-3] and
                    data['short_ema'].iloc[-4] <= data['medium_ema'].iloc[-4]
                ):
                    # Short EMA crossover Medium EMA - Close Short Order
                    if position_types[symbol] == 'short':
                        close_position(symbol, position_types[symbol])
                        position_types[symbol] = None
                    print(f'{symbol} Short EMA crossed over Medium EMA - Close Short Order')

            # Sleep for some time (e.g., 1 hour) before checking again
            time.sleep(300)

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(300)  # Wait for 5 minutes before trying again

# Run the trading strategy
ema_strategy()
