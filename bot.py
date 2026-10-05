import os
import requests
import pandas as pd

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def get_data():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval=15m&range=5d"
    data = requests.get(url, timeout=15).json()["chart"]["result"][0]

    df = pd.DataFrame({
        "close": data["indicators"]["quote"][0]["close"]
    }).dropna()

    return df

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def send_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message
    })

df = get_data()

df["ema20"] = df["close"].ewm(span=20).mean()
df["ema50"] = df["close"].ewm(span=50).mean()
df["rsi"] = rsi(df["close"])

price = df["close"].iloc[-1]
ema20 = df["ema20"].iloc[-1]
ema50 = df["ema50"].iloc[-1]
rsi_value = df["rsi"].iloc[-1]

if ema20 > ema50 and rsi_value > 52 and rsi_value < 70:
    signal = "🟢 BUY"
    entry = price
    sl = price - 0.0010
    tp1 = price + 0.0015
    tp2 = price + 0.0025

elif ema20 < ema50 and rsi_value < 48 and rsi_value > 30:
    signal = "🔴 SELL"
    entry = price
    sl = price + 0.0010
    tp1 = price - 0.0015
    tp2 = price - 0.0025

else:
    signal = "⚪ WAIT"
    entry = price
    sl = tp1 = tp2 = None

if signal != "⚪ WAIT":
    message = f"""EUR/USD SIGNAL

{signal}

Entry: {entry:.5f}
Stop Loss: {sl:.5f}
TP1: {tp1:.5f}
TP2: {tp2:.5f}

RSI: {rsi_value:.1f}
EMA20: {ema20:.5f}
EMA50: {ema50:.5f}

⚠️ Demo hesabında test et.
"""
else:
    message = f"""EUR/USD

⚪ WAIT

Current price: {price:.5f}
RSI: {rsi_value:.1f}
EMA20: {ema20:.5f}
EMA50: {ema50:.5f}

Henüz yeterince güçlü BUY/SELL sinyali yok.
"""

send_message(message)
