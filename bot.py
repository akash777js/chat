from telegram.ext import Updater, CommandHandler
import requests, json
from math import sqrt

# --- Load token ---
with open("token.txt","r") as f:
    TOKEN = f.read().strip()

# --- Helpers ---
def get_btc_price():
    try:
        data = requests.get("https://api.coindesk.com/v1/bpi/currentprice/BTC.json").json()
        return f"${data['bpi']['USD']['rate']}"
    except Exception:
        return "Error fetching price"

# /start
def start(update, context):
    update.message.reply_text("👋 Welcome! Try /predict, /candle, /predictcandle, /newsanalysis or /fullpredict")

# /predict
def predict(update, context):
    update.message.reply_text(f"📈 Current BTC Price: {get_btc_price()}")

# Candle data
def get_latest_candles():
    try:
        data = requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=5").json()
        out=[]
        for i,c in enumerate(data):
            o,cl,vol=float(c[1]),float(c[4]),float(c[5])
            direction="🔼 UP" if cl>o else "🔽 DOWN"
            out.append(f"🕒 Min-{i+1}: {direction}\nOpen:{o}, Close:{cl}, Volume:{vol}")
        return "\n\n".join(out)
    except Exception:
        return "⚠️ Could not fetch candle data."

def candle(update, context):
    update.message.reply_text(f"🟩 BTC Last 5 Minute Candles:\n\n{get_latest_candles()}")

# Pattern matching
def load_patterns():
    with open("patterns.json") as f:
        return json.load(f)

def euclid(a,b): return sqrt(sum((x-y)**2 for x,y in zip(a,b)))

def predict_next(pattern):
    best=None;dist=float('inf')
    for p in load_patterns():
        d=euclid(pattern,p["pattern"])
        if d<dist: dist,best=d,p
    return best["next"] if best else "Unknown"

def get_prediction():
    closes=[float(c[4]) for c in requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=5").json()]
    return predict_next(closes)

def predict_candle(update, context):
    update.message.reply_text(f"🔮 Next 1‑min candle will likely go: {get_prediction()}")

# News
def fetch_news():
    try:
        data=requests.get("https://cryptopanic.com/api/v1/posts/?auth_token=demo&public=true").json()
        return [it["title"] for it in data["results"][:5]]
    except Exception:
        return ["Could not fetch news."]

def sentiment(news):
    pos=['surge','bull','rise','pump','gain','green','adoption']
    neg=['fall','crash','bear','dip','sell-off','ban','regulation']
    score=sum((1 if any(w in n.lower() for w in pos) else -1 if any(w in n.lower() for w in neg) else 0) for n in news)
    return "UP" if score>0 else "DOWN" if score<0 else "NEUTRAL"

def news_analysis(update, context):
    news=fetch_news()
    update.message.reply_text("📰 Last 5 Crypto News:\n- "+"\n- ".join(news)+f"\n\n🧠 Sentiment suggests: {sentiment(news)}")

# Combine
def full_predict(update, context):
    chart,news_pred=get_prediction(),sentiment(fetch_news())
    score=(1 if chart=='UP' else -1 if chart=='DOWN' else 0)+(1 if news_pred=='UP' else -1 if news_pred=='DOWN' else 0)
    final='UP ✅' if score>0 else 'DOWN ❌' if score<0 else 'NEUTRAL ⚖️'
    conf='High 🔼' if abs(score)==2 else 'Medium' if abs(score)==1 else 'Low'
    update.message.reply_text(f"📊 Chart: {chart}\n📰 News: {news_pred}\n🔮 Prediction: {final}\n📉 Confidence: {conf}")

# --- Main ---
updater=Updater(TOKEN,use_context=True)
dp=updater.dispatcher
dp.add_handler(CommandHandler("start",start))
dp.add_handler(CommandHandler("predict",predict))
dp.add_handler(CommandHandler("candle",candle))
dp.add_handler(CommandHandler("predictcandle",predict_candle))
dp.add_handler(CommandHandler("newsanalysis",news_analysis))
dp.add_handler(CommandHandler("fullpredict",full_predict))

updater.start_polling()
updater.idle()