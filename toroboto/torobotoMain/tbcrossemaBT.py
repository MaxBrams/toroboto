import pandas as pd
import ta


def tbcrossema(df, initCond):
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

    # Backtest Execution

    # dfTest = df['2020-07-16':]
    dfTest = df.copy()

    dfTest['EMA28'] = ta.trend.ema_indicator(dfTest['close'], 28)
    dfTest['EMA48'] = ta.trend.ema_indicator(dfTest['close'], 48)
    dfTest['STOCH_RSI'] = ta.momentum.stochrsi(dfTest['close'])

    dt = None
    dt = pd.DataFrame(columns=['date', 'position', 'price', 'fees', 'fiat', 'coins', 'wallet', 'drawBack'])

    lastIndex = df.first_valid_index()

    for index, row in dfTest.iterrows():
        # Buy
        if row['EMA28'] > row['EMA48'] and row['STOCH_RSI'] < 0.8 and usdt > 0:
            coin = usdt / row['close']
            fees = takerFee * coin
            coin = coin - fees
            usdt = 0
            wallet = coin * row['close']
            if wallet > lastAth:
                lastAth = wallet
            # print("Buy COIN at",df['close'][index],'$ the', index)
            myrow = {'date': index, 'position': "Buy", 'price': row['close'], 'fees': fees * row['close'], 'fiat': usdt, 'coins': coin, 'wallet': wallet, 'drawBack': (wallet - lastAth) / lastAth}
            dt = dt.append(myrow, ignore_index=True)

        # Sell
        if row['EMA28'] < row['EMA48'] and row['STOCH_RSI'] > 0.2 and coin > 0:
            usdt = coin * row['close']
            fees = takerFee * usdt
            usdt = usdt - fees
            coin = 0
            wallet = usdt
            if wallet > lastAth:
                lastAth = wallet
            # print("Sell COIN at",df['close'][index],'$ the', index)
            myrow = {'date': index, 'position': "Sell", 'price': row['close'], 'fees': fees, 'fiat': usdt, 'coins': coin, 'wallet': wallet, 'drawBack': (wallet - lastAth) / lastAth}
            dt = dt.append(myrow, ignore_index=True)

        lastIndex = index

    # Print Complete BackTest Analyses
    print("\n\n#### Cross EMA RSI Method ####")
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
    print("Total fee : ", round(dt['fees'].sum(), 2), "$")

    return dt, dfTest
