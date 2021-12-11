import pandas as pd


def backtestAnalysis(dt, dfTest, initCond):
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
    print("\n backtest analysis //////////////")
    print("Pair Symbol :", pairName)
    print("Period : [" + str(dfTest.index[0]) + "] -> [" +
          str(dfTest.index[len(dfTest) - 1]) + "]")
    print("Starting balance :", initalWallet, "$")

    print("\n----- General Informations -----")
    print("Final balance :", round(wallet, 2), "$")
    print("Performance vs US Dollar :", round(algoPercentage, 2), "%")
    print("Buy and Hold Performence :", round(holdPercentage, 2), "%")
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
