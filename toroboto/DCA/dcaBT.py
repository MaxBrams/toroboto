# -- Import --
import pandas as pd
from binance.client import Client
import ta
import matplotlib.pyplot as plt
import numpy as np

# -- Define Binance Client --
client = Client()

# -- You can change the crypto pair ,the start date and the time interval below --
pairName = "ETHUSDT"
startDate = "01 january 2017"
timeInterval = Client.KLINE_INTERVAL_1WEEK

# -- Load all price data from binance API --
klinesT = client.get_historical_klines(pairName, timeInterval, startDate)

# -- Define your dataset --
df = pd.DataFrame(klinesT, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore' ])
df['close'] = pd.to_numeric(df['close'])
df['high'] = pd.to_numeric(df['high'])
df['low'] = pd.to_numeric(df['low'])
df['open'] = pd.to_numeric(df['open'])

# -- Set the date to index --
df = df.set_index(df['timestamp'])
df.index = pd.to_datetime(df.index, unit='ms')
del df['timestamp']

print("Data loaded 100%")

# -- Uncomment the line below if you want to check your price dataset --
# df

# -- Indicator variable --
# stochWindow = 14

# -- Drop all columns we do not need --
df.drop(columns=df.columns.difference(['open','high','low','close','volume']), inplace=True)

# -- Indicators, you can edit every value --
# df['STOCH_RSI'] = ta.momentum.stochrsi(close=df['close'], window=stochWindow)
# df['RSI'] = ta.momentum.rsi(close=df['close'], window=stochWindow)
df['LAST_ATH'] = df['close'].cummax()

print("Indicators loaded 100%")

# -- Uncomment the line below if you want to check your dataset with indicators --
df

dfTest = df[:]
weeklyAmount = 30
takerFee = 0.0007
buyAmount = weeklyAmount
mediumBuy = 0
totalInvest = 0
btcWallet = 0

for index, row in dfTest.iterrows():
    totalInvest += buyAmount
    buyBTC = buyAmount / row['close']
    btcWallet += buyBTC - takerFee * buyBTC
    mediumBuy += 1

resultInDollar = btcWallet * dfTest.iloc[-1]['close']
perfInPct = (resultInDollar - totalInvest)/totalInvest
buyAndHoldPerf = (dfTest.iloc[-1]['close'] - dfTest.iloc[0]['close'])/dfTest.iloc[0]['close']
print('Buy',mediumBuy,'time',weeklyAmount,'$')
print('Total invest', totalInvest, '$')
print('Final wallet', round(btcWallet,3), 'BTC')
print('Final wallet equivalent', round(resultInDollar,2), '$')
print('Performance',round(perfInPct*100,2), '%')
print('Buy and Hold performance', round(buyAndHoldPerf*100,2), '%')

dfTest = df[:]
weeklyAmount = 30
takerFee = 0.0007
buyAmount = 0
bigBuy = 0
mediumBuy = 0
lowBuy = 0
totalEntry = 0
totalInvest = 0
btcWallet = 0

for index, row in dfTest.iterrows():
    if row['close'] <= 0.5 * row['LAST_ATH']:
        buyAmount = 2 * weeklyAmount
        bigBuy+=1
    elif row['close'] > 0.5 * row['LAST_ATH'] and row['close'] <= 0.8 * row['LAST_ATH']:
        mediumBuy+=1
        buyAmount = 1 * weeklyAmount
    elif row['close'] > 0.8 * row['LAST_ATH']:
        lowBuy+=1
        buyAmount = 0.5 * weeklyAmount
        # buyAmount = 0
    totalInvest += buyAmount
    buyBTC = buyAmount / row['close']
    btcWallet += buyBTC - takerFee * buyBTC
    totalEntry += 1

resultInDollar = btcWallet * dfTest.iloc[-1]['close']
perfInPct = (resultInDollar - totalInvest)/totalInvest
buyAndHoldPerf = (dfTest.iloc[-1]['close'] - dfTest.iloc[0]['close'])/dfTest.iloc[0]['close']
print('Buy',bigBuy,'time',2*weeklyAmount,'$')
print('Buy',mediumBuy,'time',1*weeklyAmount,'$')
print('Buy',lowBuy,'time',0.5*weeklyAmount,'$')
print('Total invest', totalInvest, '$')
print('Final wallet', round(btcWallet,3), 'BTC')
print('Final wallet equivalent', round(resultInDollar,2), '$')
print('Performance',round(perfInPct*100,2), '%')
print('Buy and Hold performance', round(buyAndHoldPerf*100,2), '%')