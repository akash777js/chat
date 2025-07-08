import os
import requests
import json
from math import sqrt
from telegram.ext import Updater, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set")

def get_btc_price():
    try:
        url = "https://api.coindesk.com/v1/bpi/currentprice/BTC.json"
        response = requests.get(url)
        data = response.json()
        price = data['bpi']['USD']['rate']
        return f"${price}"
    except Exception:
        return "Error fetching price"

def start(update, context):
    update.message.reply_text("👋 Welcome! Use /predict, /candle, /predictcandle, /newsanalysis or /fullpredict")

def predict(update, context):
    btc_price = get_btc_price()
    update.message.reply_text(f"📈 Current BTC Price: {btc_price}")

def get_latest_candles():
    url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=5"
    try:
        response = requests.get(url)
        data = response.json()
        candles = []
        for i, candle in enumerate(data):
            o = float(candle[1])
            c = float(candle[4])
            v = float(candle[5])
            direction = "🔼 UP" if c > o else "🔽 DOWN"
            candles.append(f"🕒 Min-{i+1}: {direction}\nOpen: {o}, Close: {c}, Volume: {v}")
        return "\n\n".join(candles)
    except:
        return "⚠️ Could not fetch candle data."

def candle(update, context):
    result = get_latest_candles()
    update.message.reply_text(f"🟩 BTC Last 5 Minute Candles:\n\n{result}")

def load_patterns():
    with open("patterns.json", "r") as f:
        return json.load(f)

def euclid(a, b):
    return sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

def predict_next(pattern):
    patterns = load_patterns()
    best = None
    dist = float("inf")
    for entry in patterns:
        d = euclid(pattern, entry["pattern"])
        if d < dist:
            dist = d
            best = entry
    return best["next"] if best else "Unknown"

def get_prediction():
    url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=5"
    response = requests.get(url)
    data = response.json()
    closes = [float(candle[4]) for candle in data]
    return predict_next(closes)

def predict_candle(update, context):
    prediction = get_prediction()
    update.message.reply_text(f"🔮 Next 1-min candle will likely go: {prediction}")

def fetch_news():
    url = "https://cryptopanic.com/api/v1/posts/?auth_token=demo&public=true"
    try:
        response = requests.get(url)
        data = response.json()
        return [item["title"] for item in data["results"][:5]]
    except:
        return ["Could not fetch news."]

def sentiment(news):
    pos = ['surge', 'bull', 'rise', 'pump', 'gain', 'green', 'adoption']
    neg = ['fall', 'crash', 'bear', 'dip', 'sell-off', 'ban', 'regulation']
    score = 0
    for n in news:
        for w in pos:
            if w in n.lower():
                score += 1
        for w in neg:
            if w in n.lower():
                score -= 1
    if score > 0:
        return "UP"
    elif score < 0:
        return "DOWN"
    else:
        return "NEUTRAL"

def news_analysis(update, context):
    headlines = fetch_news()
    result = sentiment(headlines)
    update.message.reply_text("📰 Last 5 Crypto News:\n- " + "\n- ".join(headlines) + f"\n\n🧠 Sentiment suggests: {result}")

def full_predict(update, context):
    chart = get_prediction()
    news = fetch_news()
    news_sent = sentiment(news)
    score = (1 if chart == "UP" else -1 if chart == "DOWN" else 0) + (1 if news_sent == "UP" else -1 if news_sent == "DOWN" else 0)
    final = "UP ✅" if score > 0 else "DOWN ❌" if score < 0 else "NEUTRAL ⚖️"
    conf = "High 🔼" if abs(score) == 2 else "Medium" if abs(score) == 1 else "Low"
    update.message.reply_text(f"📊 Chart: {chart}\n📰 News: {news_sent}\n🔮 Prediction: {final}\n📉 Confidence: {conf}")

updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("predict", predict))
dp.add_handler(CommandHandler("candle", candle))
dp.add_handler(CommandHandler("predictcandle", predict_candle))
dp.add_handler(CommandHandler("newsanalysis", news_analysis))
dp.add_handler(CommandHandler("fullpredict", full_predict))
updater.start_polling()
updater.idle()
