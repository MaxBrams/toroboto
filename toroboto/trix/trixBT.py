# Load data

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
startDate = "10 january 2020"
timeInterval = Client.KLINE_INTERVAL_1HOUR

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


# Define indicator

# -- Drop all columns we do not need --
df.drop(df.columns.difference(['open','high','low','close','volume']), axis=1, inplace=True)

# -- Indicators, you can edit every value --
df['EMA200'] = ta.trend.ema_indicator(close=df['close'], window=200)
# -- Trix Indicator --
trixLength = 9
trixSignal = 21
df['TRIX'] = ta.trend.ema_indicator(ta.trend.ema_indicator(ta.trend.ema_indicator(close=df['close'], window=trixLength), window=trixLength), window=trixLength)
df['TRIX_PCT'] = df["TRIX"].pct_change()*100
df['TRIX_SIGNAL'] = ta.trend.sma_indicator(df['TRIX_PCT'],trixSignal)
df['TRIX_HISTO'] = df['TRIX_PCT'] - df['TRIX_SIGNAL']

# -- Stochasitc RSI --
df['STOCH_RSI'] = ta.momentum.stochrsi(close=df['close'], window=14, smooth1=3, smooth2=3)

print("Indicators loaded 100%")

# -- Uncomment the line below if you want to check your dataset with indicators --
df

# Run the spot Backtest

dfTest = df.copy()

# -- If you want to run your BackTest on a specific period, uncomment the line below --
# dfTest = df['2021-09-01':]

# -- Definition of dt, that will be the dataset to do your trades analyses --
dt = None
dt = pd.DataFrame(columns=['date', 'position', 'reason', 'price', 'frais', 'fiat', 'coins', 'wallet', 'drawBack'])

# -- You can change variables below --
usdt = 1000
makerFee = 0.0002
takerFee = 0.0007

# -- Do not touch these values --
initalWallet = usdt
wallet = usdt
coin = 0
lastAth = 0
previousRow = dfTest.iloc[0]
stopLoss = 0
takeProfit = 500000
buyReady = True
sellReady = True


# -- Condition to BUY market --
def buyCondition(row, previousRow):
    if row['TRIX_HISTO'] > 0 and row['STOCH_RSI'] < 0.8:
        return True
    else:
        return False


# -- Condition to SELL market --
def sellCondition(row, previousRow):
    if row['TRIX_HISTO'] < 0 and row['STOCH_RSI'] > 0.2:
        return True
    else:
        return False


# -- Iteration on all your price dataset (df) --
for index, row in dfTest.iterrows():
    # -- Buy market order --
    if buyCondition(row, previousRow) and usdt > 0 and buyReady == True:
        # -- You can define here at what price you buy --
        buyPrice = row['close']

        # -- Define the price of you SL and TP or comment it if you don't want a SL or TP --
        # stopLoss = buyPrice - 0.02 * buyPrice
        # takeProfit = buyPrice + 0.04 * buyPrice

        coin = usdt / buyPrice
        fee = takerFee * coin
        coin = coin - fee
        usdt = 0
        wallet = coin * row['close']

        # -- Check if your wallet hit a new ATH to know the drawBack --
        if wallet > lastAth:
            lastAth = wallet

        # -- You can uncomment the line below if you want to see logs --
        # print("Buy COIN at",buyPrice,'$ the', index)

        # -- Add the trade to DT to analyse it later --
        myrow = {'date': index, 'position': "Buy", 'reason': 'Buy Market Order', 'price': buyPrice, 'frais': fee * row['close'], 'fiat': usdt, 'coins': coin, 'wallet': wallet,
                 'drawBack': (wallet - lastAth) / lastAth}
        dt = dt.append(myrow, ignore_index=True)

    # -- Stop Loss --
    elif row['low'] < stopLoss and coin > 0:
        sellPrice = stopLoss
        usdt = coin * sellPrice
        fee = makerFee * usdt
        usdt = usdt - fee
        coin = 0
        buyReady = False
        wallet = usdt

        # -- Check if your wallet hit a new ATH to know the drawBack --
        if wallet > lastAth:
            lastAth = wallet

        # -- You can uncomment the line below if you want to see logs --
        # print("Sell COIN at Stop Loss",sellPrice,'$ the', index)

        # -- Add the trade to DT to analyse it later --
        myrow = {'date': index, 'position': "Sell", 'reason': 'Sell Stop Loss', 'price': sellPrice, 'frais': fee, 'fiat': usdt, 'coins': coin, 'wallet': wallet,
                 'drawBack': (wallet - lastAth) / lastAth}
        dt = dt.append(myrow, ignore_index=True)

        # -- Sell Market Order --
    elif sellCondition(row, previousRow) and coin > 0 and sellReady == True:

        # -- You can define here at what price you buy --
        sellPrice = row['close']
        usdt = coin * sellPrice
        fee = takerFee * usdt
        usdt = usdt - fee
        coin = 0
        buyReady = True
        wallet = usdt

        # -- Check if your wallet hit a new ATH to know the drawBack --
        if wallet > lastAth:
            lastAth = wallet

        # -- You can uncomment the line below if you want to see logs --
        # print("Sell COIN at",sellPrice,'$ the', index)

        # -- Add the trade to DT to analyse it later --
        myrow = {'date': index, 'position': "Sell", 'reason': 'Sell Market Order', 'price': sellPrice, 'frais': fee, 'fiat': usdt, 'coins': coin, 'wallet': wallet,
                 'drawBack': (wallet - lastAth) / lastAth}
        dt = dt.append(myrow, ignore_index=True)

    previousRow = row

# -- BackTest Analyses --
dt = dt.set_index(dt['date'])
dt.index = pd.to_datetime(dt.index)
dt['resultat'] = dt['wallet'].diff()
dt['resultat%'] = dt['wallet'].pct_change() * 100
dt.loc[dt['position'] == 'Buy', 'resultat'] = None
dt.loc[dt['position'] == 'Buy', 'resultat%'] = None

dt['tradeIs'] = ''
dt.loc[dt['resultat'] > 0, 'tradeIs'] = 'Good'
dt.loc[dt['resultat'] <= 0, 'tradeIs'] = 'Bad'

iniClose = dfTest.iloc[0]['close']
lastClose = dfTest.iloc[len(dfTest) - 1]['close']
holdPercentage = ((lastClose - iniClose) / iniClose) * 100
algoPercentage = ((wallet - initalWallet) / initalWallet) * 100
vsHoldPercentage = ((algoPercentage - holdPercentage) / holdPercentage) * 100

dt['hold'] = dt['price'] * initalWallet/iniClose

try:
    tradesPerformance = round(dt.loc[(dt['tradeIs'] == 'Good') | (dt['tradeIs'] == 'Bad'), 'resultat%'].sum()
                              / dt.loc[(dt['tradeIs'] == 'Good') | (dt['tradeIs'] == 'Bad'), 'resultat%'].count(), 2)
except:
    tradesPerformance = 0
    print("/!\ There is no Good or Bad Trades in your BackTest, maybe a problem...")

try:
    totalGoodTrades = dt.groupby('tradeIs')['date'].nunique()['Good']
    AveragePercentagePositivTrades = round(dt.loc[dt['tradeIs'] == 'Good', 'resultat%'].sum()
                                           / dt.loc[dt['tradeIs'] == 'Good', 'resultat%'].count(), 2)
    idbest = dt.loc[dt['tradeIs'] == 'Good', 'resultat%'].idxmax()
    bestTrade = str(
        round(dt.loc[dt['tradeIs'] == 'Good', 'resultat%'].max(), 2))
except:
    totalGoodTrades = 0
    AveragePercentagePositivTrades = 0
    idbest = ''
    bestTrade = 0
    print("/!\ There is no Good Trades in your BackTest, maybe a problem...")

try:
    totalBadTrades = dt.groupby('tradeIs')['date'].nunique()['Bad']
    AveragePercentageNegativTrades = round(dt.loc[dt['tradeIs'] == 'Bad', 'resultat%'].sum()
                                           / dt.loc[dt['tradeIs'] == 'Bad', 'resultat%'].count(), 2)
    idworst = dt.loc[dt['tradeIs'] == 'Bad', 'resultat%'].idxmin()
    worstTrade = round(dt.loc[dt['tradeIs'] == 'Bad', 'resultat%'].min(), 2)
except:
    totalBadTrades = 0
    AveragePercentageNegativTrades = 0
    idworst = ''
    worstTrade = 0
    print("/!\ There is no Bad Trades in your BackTest, maybe a problem...")

totalTrades = totalBadTrades + totalGoodTrades
winRateRatio = (totalGoodTrades / totalTrades) * 100

reasons = dt['reason'].unique()

dt

# Print Complete BackTest Analyses

print("Pair Symbol :",pairName)
print("Period : [" + str(dfTest.index[0]) + "] -> [" +
      str(dfTest.index[len(dfTest)-1]) + "]")
print("Starting balance :", initalWallet, "$")

print("\n----- General Informations -----")
print("Final balance :", round(wallet, 2), "$")
print("Performance vs US Dollar :", round(algoPercentage, 2), "%")
print("Buy and Hold Performence :", round(holdPercentage, 2), "%")
print("Performance vs Buy and Hold :", round(vsHoldPercentage, 2), "%")
print("Best trade : +"+bestTrade, "%, the", idbest)
print("Worst trade :", worstTrade, "%, the", idworst)
print("Worst drawBack :", str(100*round(dt['drawBack'].min(), 2)), "%")
print("Total fees : ", round(dt['frais'].sum(), 2), "$")

print("\n----- Trades Informations -----")
print("Total trades on period :",totalTrades)
print("Number of positive trades :", totalGoodTrades)
print("Number of negative trades : ", totalBadTrades)
print("Trades win rate ratio :", round(winRateRatio, 2), '%')
print("Average trades performance :",tradesPerformance,"%")
print("Average positive trades :", AveragePercentagePositivTrades, "%")
print("Average negative trades :", AveragePercentageNegativTrades, "%")

print("\n----- Trades Reasons -----")
reasons = dt['reason'].unique()
for r in reasons:
    print(r+" number :", dt.groupby('reason')['date'].nunique()[r])

dt[['wallet', 'hold', 'price']].plot(subplots=True, figsize=(12, 10))
plt.show()
