import ta
import pandas_ta as pda


def SMA(df):
    # Simple Moving Average
    df['SMA'] = ta.trend.sma_indicator(df['close'], window=12)
    return df


def EMA(df):
    # Exponential Moving Average
    df['EMA1'] = ta.trend.ema_indicator(close=df['close'], window=13)
    df['EMA2'] = ta.trend.ema_indicator(close=df['close'], window=38)
    return df


def RSI(df):
    # #Relative Strength Index (RSI)
    df['RSI'] = ta.momentum.rsi(close=df['close'], window=14)
    return df


def MACD(df):
    # #MACD
    MACD = ta.trend.MACD(close=df['close'], window_fast=12, window_slow=26, window_sign=9)
    df['MACD'] = MACD.macd()
    df['MACD_SIGNAL'] = MACD.macd_signal()
    df['MACD_DIFF'] = MACD.macd_diff()  # Histogramme MACD
    return df


def SRSI(df):
    # #Stochastic RSI
    df['STOCH_RSI'] = ta.momentum.stochrsi(close=df['close'], window=14, smooth1=3, smooth2=3)  # Non moyenné
    df['STOCH_RSI_D'] = ta.momentum.stochrsi_d(close=df['close'], window=14, smooth1=3, smooth2=3)  # Orange sur TradingView
    df['STOCH_RSI_K'] = ta.momentum.stochrsi_k(close=df['close'], window=14, smooth1=3, smooth2=3)  # Bleu sur TradingView
    return df


def ICHI(df):
    # #Ichimoku
    df['KIJUN'] = ta.trend.ichimoku_base_line(high=df['high'], low=df['low'], window1=9, window2=26)
    df['TENKAN'] = ta.trend.ichimoku_conversion_line(high=df['high'], low=df['low'], window1=9, window2=26)
    df['SSA'] = ta.trend.ichimoku_a(high=df['high'], low=df['low'], window1=9, window2=26)
    df['SSB'] = ta.trend.ichimoku_b(high=df['high'], low=df['low'], window2=26, window3=52)
    return df


def BOLLINGER(df):
    # #Bollinger Bands
    BOL_BAND = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
    df['BOL_H_BAND'] = BOL_BAND.bollinger_hband()  # Bande Supérieur
    df['BOL_L_BAND'] = BOL_BAND.bollinger_lband()  # Bande inférieur
    df['BOL_MAVG_BAND'] = BOL_BAND.bollinger_mavg()  # Bande moyenne
    return df


def ATR(df):
    # #Average True Range (ATR)
    df['ATR'] = ta.volatility.average_true_range(high=df['high'], low=df['low'], close=df['close'], window=14)
    return df


def SUPERT(df):
    # #Super Trend
    ST_length = 10
    ST_multiplier = 3.0
    superTrend = pda.supertrend(high=df['high'], low=df['low'], close=df['close'], length=ST_length, multiplier=ST_multiplier)
    df['SUPER_TREND'] = superTrend['SUPERT_' + str(ST_length) + "_" + str(ST_multiplier)]  # Valeur de la super trend
    df['SUPER_TREND_DIRECTION'] = superTrend['SUPERTd_' + str(ST_length) + "_" + str(ST_multiplier)]  # Retourne 1 si vert et -1 si rouge
    return df


def AWOSC(df):
    # #Awesome Oscillator
    df['AWESOME_OSCILLATOR'] = ta.momentum.awesome_oscillator(high=df['high'], low=df['low'], window1=5, window2=34)
    return df


def KAMA(df):
    # # Kaufman’s Adaptive Moving Average (KAMA)
    df['KAMA'] = ta.momentum.kama(close=df['close'], window=10, pow1=2, pow2=30)
    return df


def CHOP(df):
    # #Choppiness index
    df['CHOP'] = ta.volatility.get_chop(high=df['high'], low=df['low'], close=df['close'], window=14)
    return df
