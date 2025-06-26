

### indicators.py
import pandas as pd
import numpy as np
import ta


def calculate_indicators(df):
    df = df.copy()
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['ma_short'] = df['close'].rolling(window=7).mean()
    df['ma_long'] = df['close'].rolling(window=21).mean()
    df['volume_avg'] = df['volume'].rolling(window=5).mean()
    df['is_breakout'] = df['close'] > df['high'].rolling(window=5).max().shift(1)
    df['volume_spike'] = df['volume'] > (df['volume_avg'] * 1.5)
    return df


def detect_buy_signal(df):
    last = df.iloc[-1]
    if (
        last['rsi'] < 30 and
        last['ma_short'] > last['ma_long'] and
        last['is_breakout'] and
        last['volume_spike']
    ):
        return True
    return False