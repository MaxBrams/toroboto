# -- Import --
import pandas as pd
from binance.client import Client
import ta
import matplotlib.pyplot as plt
import numpy as np


# Define indicator
def tbtrixatr(df, initCond):
    # initCond = [pairName, initalWallet, wallet, coin, lastAth, stopLoss, takeProfit, buyReady, sellReady, makerFee, takerFee]
    pairName = initCond[0]
    initalWallet = initCond[1]
    wallet = initCond[2]
    coin = initCond[3]
    lastAth = initCond[4]
    stopLoss = initCond[5]
    takeProfit = initCond[6]
    buyReady = initCond[7]
    sellReady = initCond[8]
    makerFee = initCond[9]
    takerFee = initCond[10]
    usdt = initalWallet

    # -- Drop all columns we do not need --
    df.drop(df.columns.difference(['open', 'high', 'low', 'close', 'volume']), axis=1, inplace=True)

    # -- Indicators, you can edit every value --
    df['EMA200'] = ta.trend.ema_indicator(close=df['close'], window=200)
    # -- Trix Indicator --
    trixLength = 9
    trixSignal = 21
    df['TRIX'] = ta.trend.ema_indicator(ta.trend.ema_indicator(ta.trend.ema_indicator(close=df['close'], window=trixLength), window=trixLength), window=trixLength)
    df['TRIX_PCT'] = df["TRIX"].pct_change() * 100
    df['TRIX_SIGNAL'] = ta.trend.sma_indicator(df['TRIX_PCT'], trixSignal)
    df['TRIX_HISTO'] = df['TRIX_PCT'] - df['TRIX_SIGNAL']

    # -- Stochasitc RSI --
    df['STOCH_RSI'] = ta.momentum.stochrsi(close=df['close'], window=14, smooth1=3, smooth2=3)

    # -- ATR --
    df['ATR'] = ta.volatility.average_true_range(high=df['high'], low=df['low'], close=df['close'], window=14)

    def get_chop(high, low, close, window):
        tr1 = pd.DataFrame(high - low).rename(columns={0: 'tr1'})
        tr2 = pd.DataFrame(abs(high - close.shift(1))).rename(columns={0: 'tr2'})
        tr3 = pd.DataFrame(abs(low - close.shift(1))).rename(columns={0: 'tr3'})
        frames = [tr1, tr2, tr3]
        tr = pd.concat(frames, axis=1, join='inner').dropna().max(axis=1)
        atr = tr.rolling(1).mean()
        highh = high.rolling(window).max()
        lowl = low.rolling(window).min()
        ci = 100 * np.log10((atr.rolling(window).sum()) / (highh - lowl)) / np.log10(window)
        return ci

    # -- Choppiness --
    df['CHOP'] = get_chop(high=df['high'], low=df['low'], close=df['close'], window=14)

    print("Indicators loaded 100%")

    # -- Uncomment the line below if you want to check your dataset with indicators --
    df

    # Run the spot Backtest

    dfTest = df.copy()
    previousRow = dfTest.iloc[0]

    # -- If you want to run your BackTest on a specific period, uncomment the line below --
    # dfTest = df['2021-09-01':]

    # -- Definition of dt, that will be the dataset to do your trades analyses --
    dt = None
    dt = pd.DataFrame(columns=['date', 'position', 'reason', 'price', 'frais', 'fiat', 'coins', 'wallet', 'drawBack'])

    # -- Condition to BUY market --
    def buyCondition(row, previousRow):
        if row['TRIX_HISTO'] > 0 and row['STOCH_RSI'] < 0.8 :
            return True
        elif row['STOCH_RSI'] > 0.8 and row['CHOP'] < 40 :
            return True
        else:
            return False

    # -- Condition to SELL market --
    def sellCondition(row, previousRow):
        if row['TRIX_HISTO'] < 0 and row['STOCH_RSI'] > 0.2:
            return True
        elif row['STOCH_RSI'] < 0.2 and row['CHOP'] > 60 :
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
            #stopLoss = buyPrice - row['ATR']
            #takeProfit = buyPrice + 10*row['ATR']
            #stopLoss = buyPrice - 0.02 * buyPrice
            #takeProfit = buyPrice + 0.04 * buyPrice

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

        # -- Take Profit --
        elif row['high'] > takeProfit and coin > 0:
            sellPrice = takeProfit
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
            # print("Sell COIN at Take Profit",sellPrice,'$ the', index)

            # -- Add the trade to DT to analyse it later --
            myrow = {'date': index, 'position': "Sell", 'reason': 'Sell Take Profit', 'price': sellPrice, 'frais': fee, 'fiat': usdt, 'coins': coin, 'wallet': wallet,
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
    dt['hold'] = dt['price'] * initalWallet / iniClose

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

    # Print Complete BackTest Analyses
    print("\n\n#### Trix ATR Method ####")
    print("Pair Symbol :", pairName)
    print("Period : [" + str(dfTest.index[0]) + "] -> [" +
          str(dfTest.index[len(dfTest) - 1]) + "]")
    print("Starting balance :", initalWallet, "$")

    print("\n----- General Informations -----")
    print("Final balance :", round(wallet, 2), "$")
    print("Performance vs US Dollar :", round(algoPercentage, 2), "%")
    print("Buy and Hold Performance :", round(holdPercentage, 2), "%")
    print("Performance vs Buy and Hold :", round(vsHoldPercentage, 2), "%")
    print("Best trade : +" + bestTrade, "%, the", idbest)
    print("Worst trade :", worstTrade, "%, the", idworst)
    print("Worst drawBack :", str(100 * round(dt['drawBack'].min(), 2)), "%")
    print("Total fees : ", round(dt['frais'].sum(), 2), "$")

    print("\n----- Trades Informations -----")
    print("Total trades on period :", totalTrades)
    print("Number of positive trades :", totalGoodTrades)
    print("Number of negative trades : ", totalBadTrades)
    print("Trades win rate ratio :", round(winRateRatio, 2), '%')
    print("Average trades performance :", tradesPerformance, "%")
    print("Average positive trades :", AveragePercentagePositivTrades, "%")
    print("Average negative trades :", AveragePercentageNegativTrades, "%")

    print("\n----- Trades Reasons -----")
    reasons = dt['reason'].unique()
    for r in reasons:
        print(r + " number :", dt.groupby('reason')['date'].nunique()[r])

    return dt, dfTest
