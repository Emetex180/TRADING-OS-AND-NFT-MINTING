import pandas as pd
import plotly.graph_objects as go
import backtrader as bt

# -------------------- Trade Replay Section --------------------

# Sample data (OHLC + execution times and prices for trades)
data = {
    'time': ['2025-05-01 09:00:00', '2025-05-01 09:01:00', '2025-05-01 09:02:00'],
    'open': [100, 102, 101],
    'high': [102, 103, 102],
    'low': [99, 100, 100],
    'close': [101, 102, 101],
    'volume': [200, 250, 300]
}

# DataFrame for price data
df = pd.DataFrame(data)
df['time'] = pd.to_datetime(df['time'])

# Sample trade execution data (time and price)
trades = {
    'time': ['2025-05-01 09:00:30', '2025-05-01 09:01:45'],
    'price': [101, 102]
}
trades_df = pd.DataFrame(trades)
trades_df['time'] = pd.to_datetime(trades_df['time'])

# Create a plotly figure for candlestick chart
fig = go.Figure()

# Add candlestick chart (OHLC)
fig.add_trace(go.Candlestick(
    x=df['time'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name='Price Action'
))

# Add trade markers (executions)
fig.add_trace(go.Scatter(
    x=trades_df['time'],
    y=trades_df['price'],
    mode='markers',
    marker=dict(size=12, color='red', symbol='x'),
    name='Trade Executions'
))

# Customize chart layout
fig.update_layout(
    title="Trade Replay with Candlestick Chart",
    xaxis_title="Time",
    yaxis_title="Price",
    template="plotly_dark",
    xaxis_rangeslider_visible=False
)

# Show the interactive chart
fig.show()

# -------------------- Backtesting Section --------------------

# Create a simple strategy: Buy when price is above the moving average, sell when below
class SimpleStrategy(bt.Strategy):
    params = (('moving_avg_period', 15),)

    def __init__(self):
        # Simple moving average indicator
        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.moving_avg_period)

    def next(self):
        # Buy signal: If the close is above the moving average
        if self.data.close[0] > self.sma[0] and not self.position:
            self.buy()

        # Sell signal: If the close is below the moving average
        elif self.data.close[0] < self.sma[0] and self.position:
            self.sell()

# Load your historical data (for example, from CSV or API)
data = bt.feeds.YahooFinanceData(dataname='your_historical_data.csv')

# Set up cerebro (the backtesting engine)
cerebro = bt.Cerebro()
cerebro.adddata(data)
cerebro.addstrategy(SimpleStrategy)

# Set initial capital
cerebro.broker.set_cash(10000)

# Set commission for realistic backtesting
cerebro.broker.setcommission(commission=0.001)

# Set dynamic position sizing (10% of portfolio)
cerebro.addsizer(bt.sizers.PercentSizer, percents=10)

# Run the backtest
results = cerebro.run()

# Plot the results using candlesticks
cerebro.plot(style='candlestick')

# Print the final portfolio value after the backtest
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
