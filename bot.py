
import os
import requests
import pandas as pd
import time

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def get_data():
    urls = [
        "https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval=15m&range=5d",
        "https://query2.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval=15m&range=5d"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for url in urls:
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=20
            )

            if response.status_code != 200:
                continue

            data = response.json()

            result = data["chart"]["result"]

            if not result:
                continue

            quote = result[0]["indicators"]["quote"][0]

            df = pd.DataFrame({
                "close": quote["close"]
            }).dropna()

            if len(df) >= 50:
                return df

        except Exception:
            time.sleep(2)

    raise Exception("EUR/USD verisi alınamadı.")


def rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()

    rs = gain / loss

    return 100 - (100 / (1 + rs))


def send_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=20
    )

    if response.status_code != 200:
        raise Exception("Telegram mesaj gönderilemedi.")


df = get_data()

df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
df["rsi"] = rsi(df["close"])

price = df["close"].iloc[-1]
ema20 = df["ema20"].iloc[-1]
ema50 = df["ema50"].iloc[-1]
rsi_value = df["rsi"].iloc[-1]


if ema20 > ema50 and 52 < rsi_value < 70:

    signal = "🟢 BUY"
    entry = price
    sl = price - 0.0010
    tp1 = price + 0.0015
    tp2 = price + 0.0025

elif ema20 < ema50 and 30 < rsi_value < 48:

    signal = "🔴 SELL"
    entry = price
    sl = price + 0.0010
    tp1 = price - 0.0015
    tp2 = price - 0.0025

else:

    signal = "⚪ WAIT"
    entry = price
    sl = None
    tp1 = None
    tp2 = None


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
