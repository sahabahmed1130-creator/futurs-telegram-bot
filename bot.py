import requests
import pandas as pd
import ta
import time
from telegram import Bot

# ===== TELEGRAM SETTINGS =====
TOKEN = "8472815895:AAFwbXFwNSmsnZBckNtz55d_qVCacThD8e0"
CHAT_ID = 8578798916
bot = Bot(token=TOKEN)

# ===== COINS LIST =====
COINS = [
"BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
"ADAUSDT","DOGEUSDT","AVAXUSDT","MATICUSDT","LINKUSDT",
"LTCUSDT","ATOMUSDT","FILUSDT","NEARUSDT","APTUSDT",
"ARBUSDT","OPUSDT","INJUSDT","SUIUSDT","TIAUSDT"
]

# ===== SETTINGS =====
TRADE_LIMIT = 10
trade_count = 0

# ===== TELEGRAM SEND SAFE =====
def send(msg):
    try:
        bot.send_message(chat_id=CHAT_ID,text=msg)
        print("Signal Sent")
    except Exception as e:
        print("Telegram Error:", e)

# ===== BINANCE DATA =====
def get_data(symbol):

    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=5m&limit=250"
    data = requests.get(url).json()

    df = pd.DataFrame(data)

    df = df[[0,1,2,3,4]]
    df.columns = ["time","Open","High","Low","Close"]

    df = df.astype(float)

    # Indicators
    df["EMA50"] = ta.trend.ema_indicator(df["Close"],50)
    df["EMA200"] = ta.trend.ema_indicator(df["Close"],200)
    df["RSI"] = ta.momentum.rsi(df["Close"],14)
    df["ATR"] = ta.volatility.average_true_range(df["High"],df["Low"],df["Close"],14)

    return df.dropna()

# ===== SIGNAL LOGIC =====
def check_signal(df):

    last = df.iloc[-1]
    entry = last["Close"]
    atr = last["ATR"]

    strength = 0

    # ===== TREND =====
    if last["EMA50"] > last["EMA200"]:
        direction = "LONG 📈"
        strength += 35
    else:
        direction = "SHORT 📉"
        strength += 35

    # ===== RSI MOMENTUM =====
    if last["RSI"] > 60 or last["RSI"] < 40:
        strength += 25

    # ===== CANDLE POWER =====
    body = abs(last["Close"] - last["Open"])
    wick = last["High"] - last["Low"]

    if body > wick * 0.5:
        strength += 25

    # ===== VOLATILITY =====
    if atr > entry * 0.002:
        strength += 15

    # ===== SL TP =====
    if direction == "LONG 📈":
        sl = entry - atr * 1.5
        tp = entry + atr * 2.5
    else:
        sl = entry + atr * 1.5
        tp = entry - atr * 2.5

    return direction,strength,entry,sl,tp

# ===== START =====
print("Futures Bot Started")
send("🚀 Futures Smart Bot Connected")

# ===== MAIN LOOP =====
while True:

    try:

        if trade_count >= TRADE_LIMIT:
            send("✅ Daily Trade Limit Reached — Cooling Down")
            time.sleep(3600)
            trade_count = 0

        best_coin = None
        best_strength = 0
        best_signal = None

        for coin in COINS:

            try:
                df = get_data(coin)
                direction,strength,entry,sl,tp = check_signal(df)

                if strength > best_strength:
                    best_coin = coin
                    best_strength = strength
                    best_signal = (direction,entry,sl,tp)

            except:
                continue

        # ===== SEND ONLY STRONG SIGNAL =====
        if best_strength >= 70:

            direction,entry,sl,tp = best_signal

            msg = f"""
🔥 HUMAN STYLE FUTURES SIGNAL

Coin: {best_coin}
Direction: {direction}

Entry: {round(entry,4)}
Stop Loss: {round(sl,4)}
Take Profit: {round(tp,4)}

Confidence: {best_strength}%
Timeframe: 5M Futures
"""

            send(msg)
            trade_count += 1

        time.sleep(300)

    except Exception as e:
        print("Loop Error:", e)
        time.sleep(60)