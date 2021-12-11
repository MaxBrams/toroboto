# Load data

# -- Import --
import pandas as pd
from binance.client import Client
import ta
import matplotlib.pyplot as plt
plt.style.use('dark_background')
import numpy as np
from tbtrixBT import tbtrix
from trixATRBT import tbtrixatr
from tbcrossemaBT import tbcrossema
import indicators
from backtestAnalysis import backtestAnalysis

# -- Define Binance Client --
client = Client()

# -- Klines Intervals
klineIntervalList = ["KLINE_INTERVAL_1MINUTE", "KLINE_INTERVAL_3MINUTE", "KLINE_INTERVAL_5MINUTE", "KLINE_INTERVAL_15MINUTE", "KLINE_INTERVAL_30MINUTE", "KLINE_INTERVAL_1HOUR", "KLINE_INTERVAL_2HOUR",
                     "KLINE_INTERVAL_4HOUR", "KLINE_INTERVAL_6HOUR", "KLINE_INTERVAL_8HOUR", "KLINE_INTERVAL_12HOUR", "KLINE_INTERVAL_1DAY", "KLINE_INTERVAL_3DAY", "KLINE_INTERVAL_1WEEK",
                     "KLINE_INTERVAL_1MONTH"]

# -- You can change the crypto pair ,the start date and the time interval below --
pairName = "ETHUSDT"  # input('Enter pair name (ex: ETHUSDT): ').upper()
startDate = "10 january 2020"  # input('Enter a start date (ex: 01 january 2020): ')  # "09 december 2020"
#print('Select a kline time interval: \n 1. 1 minute \n 2. 3 minutes \n 3. 5 minutes \n 4. 15 minutes \n 5. 30 minutes \n 6. 1 hour \n 7. 2 hours \n 8. 4 hours \n 9. 6 hours \n 10. 8 hours \n '
#     '11. 12 hours \n 12. 1 day \n 13. 3 days \n 14. 1 week \n 15. 1 month')
klineInterval = "KLINE_INTERVAL_1HOUR"  # str(klineIntervalList[int(input()) - 1])
timeInterval = getattr(Client, klineInterval)

# -- Load all price data from binance API --
klinesT = client.get_historical_klines(pairName, timeInterval, startDate)

# -- Define your dataset --
df = pd.DataFrame(klinesT, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
df['close'] = pd.to_numeric(df['close'])
df['high'] = pd.to_numeric(df['high'])
df['low'] = pd.to_numeric(df['low'])
df['open'] = pd.to_numeric(df['open'])

# -- Set the date to index --
df = df.set_index(df['timestamp'])
df.index = pd.to_datetime(df.index, unit='ms')
del df['timestamp']

print("Data loaded 100%")

# -- Drop all columns we do not need --
df.drop(df.columns.difference(['open', 'high', 'low', 'close', 'volume']), axis=1, inplace=True)

# -- Initial Conditions --
usdt = 1000
makerFee = 0.0002
takerFee = 0.0007

# -- Do not touch these values --
initalWallet = usdt
wallet = usdt
coin = 0
lastAth = 0
# previousRow = dfTest.iloc[0] / ! \
stopLoss = 0
takeProfit = 500000
buyReady = True
sellReady = True

initCond = [pairName, initalWallet, wallet, coin, lastAth, stopLoss, takeProfit, buyReady, sellReady, makerFee, takerFee]

# BACKTEST EXECUTION

trixdt = tbtrix(df, initCond)
trixatrdt = tbtrixatr(df, initCond)
crossemadt = tbcrossema(df, initCond)

# Backtest Analysis
#backtestAnalysis(trixdt[0], trixdt[1], initCond)
#backtestAnalysis(crossemadt[0], crossemadt[1], initCond)

trixdt[0].rename(columns={"wallet": "trixwallet"}, inplace=True)
trixatrdt[0].rename(columns={"wallet": "trixATR"}, inplace=True)
crossemadt[0].rename(columns={"wallet": "crossEMAwallet"}, inplace=True)
result = pd.concat([trixdt[0], crossemadt[0], trixatrdt[0]], axis=1, join="inner")
result = result.loc[:, ~result.columns.duplicated()]

# Plot
result[['crossEMAwallet', 'trixwallet', 'trixATR', 'hold']].plot(subplots=False, figsize=(20, 10))

plt.show()
print("\n----- Plot -----")
