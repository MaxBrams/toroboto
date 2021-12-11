import pandas as pd
from binance.client import Client
import ta
import matplotlib.pyplot as plt

client = Client()

klinesT = client.get_historical_klines("EGLDUSDT", Client.KLINE_INTERVAL_15MINUTE, "01 september 2020")

df = pd.DataFrame(klinesT, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore' ])
df['close'] = pd.to_numeric(df['close'])
df['high'] = pd.to_numeric(df['high'])
df['low'] = pd.to_numeric(df['low'])
df['open'] = pd.to_numeric(df['open'])

del df['ignore']
del df['close_time']
del df['quote_av']
del df['trades']
del df['tb_base_av']
del df['tb_quote_av']

df = df.set_index(df['timestamp'])
df.index = pd.to_datetime(df.index, unit='ms')
del df['timestamp']
print(df)

# Backtest Execution

df.drop(df.columns.difference(['open','high','low','close','volume']), axis=1, inplace=True)
df['EMA50']=ta.trend.ema_indicator(df['close'], 50)
# df['RSI'] =ta.momentum.rsi(df['close'],14)
# df['Hrsi'] =df['rsi'].rolling(14).max()
# df['Lrsi'] =df['rsi'].rolling(14).min()
# df['stoch_rsi'] = (df['rsi'] - df['Lrsi']) / (df['Hrsi'] - df['Lrsi'])
# df['histo_macd']=ta.trend.macd_diff(df['close'], 26, 12, 9)
# df['EMA28']=ta.trend.ema_indicator(df['close'], 28)
# df['EMA48']=ta.trend.ema_indicator(df['close'], 48)
# df['MACD']=ta.trend.macd(df['close'], 26, 12, 9)
# df['MACD_SIGNAL']=ta.trend.macd_signal(df['close'], 26, 12, 9)
# df['MACD_HISTO']= df['MACD'] - df['MACD_SIGNAL']
# df['EMA8']=ta.trend.ema_indicator(df['close'], 8)
# df['EMA14']=ta.trend.ema_indicator(df['close'], 14)
# df['EMA50']=ta.trend.ema_indicator(df['close'], 50)
df['STOCH_RSI']=ta.momentum.stochrsi(df['close'])
# df['MEAN_STOCH_RSI'] = ta.trend.sma_indicator(df['STOCH_RSI'], 3)
# df['SIGNAL_MEAN_STOCH_RSI'] = ta.trend.sma_indicator(df['MEAN_STOCH_RSI'], 3)
# df["TRIX0"] = ta.trend.ema_indicator(ta.trend.ema_indicator(ta.trend.ema_indicator(df['close'], 9, fillna=False), 9, fillna=False), 9, fillna=False)
# df['TRIX1'] =  df["TRIX0"].pct_change()*100
# df['TRIX2'] = ta.trend.sma_indicator(df['TRIX1'],22)
# df['histo'] = df['TRIX1'] - df['TRIX2']
# df['MAX_RECTANGLE9'] = df['high'].rolling(9).max()
# df['MAX_RECTANGLE26'] = df['high'].rolling(26).max()
# df['MAX_RECTANGLE52'] = df['high'].rolling(52).max()
# df['MAX_RECTANGLE9']=df['MAX_RECTANGLE9'].shift(periods=1)
# df['MAX_RECTANGLE26']=df['MAX_RECTANGLE26'].shift(periods=1)
# df['MAX_RECTANGLE52']=df['MAX_RECTANGLE52'].shift(periods=1)
df['KIJUN'] = ta.trend.ichimoku_base_line(df['high'],df['low'])
df['TENKAN'] = ta.trend.ichimoku_conversion_line(df['high'],df['low'])
df['SSA'] = ta.trend.ichimoku_a(df['high'],df['low'],3,38).shift(periods=48)
df['SSB'] = ta.trend.ichimoku_b(df['high'],df['low'],38,46).shift(periods=48)
# df['TENKAN26'] = df['TENKAN'].shift(periods=25)
# df['SHIFT26']=df['close'].shift(periods=-25)
# df['HISTO'] = df['SHIFT26']-df['TENKAN']
# df['HISTO'] = df['HISTO'].shift(periods=25)
# df['SHIFT26']=df['SHIFT26'].shift(periods=26)
df

# Extract best parameters

dt = None
dt = pd.DataFrame(columns = ['i', 'result'])
count=0

for i in range(38,90):
    df['SSA'] = ta.trend.ichimoku_a(df['high'],df['low'],3,38).shift(periods=48)
    df['SSB'] = ta.trend.ichimoku_b(df['high'],df['low'],38,46).shift(periods=48)
    dfTest = df.copy()
    usdt = 1000
    coin = 0
    fee = 0.0007
    wallet = 1000

    for index, row in dfTest.iterrows():
        #BUY
        if row['close']>row['SSA'] and row['close']>row['SSB'] and row['STOCH_RSI'] < 0.8 and row['close']>row['EMA50'] and usdt > 0:
            buyPrice = row['close']
            coin = usdt/buyPrice
            coin = coin - fee*coin
            usdt = 0
            wallet = coin * row['close']
            #print("buy btc at ",df['close'][index]," || ",df['timestamp'][index], " || I have ",fiat,"$ and ",btc," btc")
        #SELL
        if (row['close'] < row['SSA'] or row['close'] < row['SSB']) and row['STOCH_RSI'] > 0.2 and coin > 0:
            sellPrice = row['close']
            usdt = coin*sellPrice
            usdt = usdt - fee*usdt
            coin = 0
            wallet = usdt
            #print("sell btc at ",df['close'][index]," || ",df['timestamp'][index], "|| I have ",fiat,"$ and ",btc," btc")
    myrow = {'i': i,'result': wallet}
    dt = dt.append(myrow,ignore_index=True)
print(dt.sort_values(by=['result']))
dt.plot.scatter(x='i',y=1,c='result',s=50,colormap='rainbow')
plt.show()

dfTest = df.copy()
# dfTest = df['2021-01-01':]
dt = None
dt = pd.DataFrame(columns=['date', 'position', 'price', 'frais', 'fiat', 'coins', 'wallet', 'drawBack'])

usdt = 1000
initalWallet = usdt
coin = 0
wallet = 1000
lastAth = 0
lastRow = dfTest.iloc[0]
fee = 0.0007
stopLoss = 0

for index, row in dfTest.iterrows():
    # Buy
    if row['close'] > row['SSA'] and row['close'] > row['SSB'] and row['STOCH_RSI'] < 0.8 and row['close'] > row['EMA50'] and usdt > 0:
        buyPrice = row['close']
        # stopLoss = buyPrice - 0.05 * buyPrice
        coin = usdt / buyPrice
        frais = fee * coin
        coin = coin - frais
        usdt = 0
        wallet = coin * row['close']
        if wallet > lastAth:
            lastAth = wallet
        # print("Buy COIN at",buyPrice,'$ the', index)
        myrow = {'date': index, 'position': "Buy", 'price': buyPrice, 'frais': frais, 'fiat': usdt, 'coins': coin, 'wallet': wallet, 'drawBack': (wallet - lastAth) / lastAth}
        dt = dt.append(myrow, ignore_index=True)

    # Stop Loss
    # elif row['low'] < stopLoss and coin > 0:
    #   sellPrice = stopLoss
    #   usdt = coin * sellPrice
    #   frais = 0.0002 * usdt
    #   usdt = usdt - frais
    #   coin = 0
    #   wallet = usdt
    #   if wallet > lastAth:
    #     lastAth = wallet
    #   # print("Sell COIN at",sellPrice,'$ the', index)
    #   myrow = {'date': index,'position': "Sell",'price': sellPrice,'frais': frais,'fiat': usdt,'coins': coin,'wallet': wallet,'drawBack':(wallet-lastAth)/lastAth}
    #   dt = dt.append(myrow,ignore_index=True)

    # Sell
    elif (row['close'] < row['SSA'] or row['close'] < row['SSB']) and row['STOCH_RSI'] > 0.2 and coin > 0:
        sellPrice = row['close']
        usdt = coin * sellPrice
        frais = fee * usdt
        usdt = usdt - frais
        coin = 0
        wallet = usdt
        if wallet > lastAth:
            lastAth = wallet
        # print("Sell COIN at",sellPrice,'$ the', index)
        myrow = {'date': index, 'position': "Sell", 'price': sellPrice, 'frais': frais, 'fiat': usdt, 'coins': coin, 'wallet': wallet, 'drawBack': (wallet - lastAth) / lastAth}
        dt = dt.append(myrow, ignore_index=True)

    lastRow = row

# ///////////////////////////////////////
print("Period : [" + str(dfTest.index[0]) + "] -> [" + str(dfTest.index[len(dfTest) - 1]) + "]")
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
holdPorcentage = ((lastClose - iniClose) / iniClose) * 100
algoPorcentage = ((wallet - initalWallet) / initalWallet) * 100
vsHoldPorcentage = ((algoPorcentage - holdPorcentage) / holdPorcentage) * 100

print("Starting balance : 1000 $")
print("Final balance :", round(wallet, 2), "$")
print("Performance vs US Dollar :", round(algoPorcentage, 2), "%")
print("Buy and Hold Performence :", round(holdPorcentage, 2), "%")
print("Performance vs Buy and Hold :", round(vsHoldPorcentage, 2), "%")
print("Number of negative trades : ", dt.groupby('tradeIs')['date'].nunique()['Bad'])
print("Number of positive trades : ", dt.groupby('tradeIs')['date'].nunique()['Good'])
print("Average Positive Trades : ", round(dt.loc[dt['tradeIs'] == 'Good', 'resultat%'].sum() / dt.loc[dt['tradeIs'] == 'Good', 'resultat%'].count(), 2), "%")
print("Average Negative Trades : ", round(dt.loc[dt['tradeIs'] == 'Bad', 'resultat%'].sum() / dt.loc[dt['tradeIs'] == 'Bad', 'resultat%'].count(), 2), "%")
idbest = dt.loc[dt['tradeIs'] == 'Good', 'resultat%'].idxmax()
idworst = dt.loc[dt['tradeIs'] == 'Bad', 'resultat%'].idxmin()
print("Best trade +" + str(round(dt.loc[dt['tradeIs'] == 'Good', 'resultat%'].max(), 2)), "%, the ", dt['date'][idbest])
print("Worst trade", round(dt.loc[dt['tradeIs'] == 'Bad', 'resultat%'].min(), 2), "%, the ", dt['date'][idworst])
print("Worst drawBack", str(100 * round(dt['drawBack'].min(), 2)), "%")
print("Total fee : ", round(dt['frais'].sum(), 2), "$")

dt[['wallet', 'price']].plot(subplots=True, figsize=(12, 10))
print('PLOT')
# dt