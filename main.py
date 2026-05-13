import os
import pandas as pd
from datetime import time
from flask import Flask
from threading import Thread
import asyncio

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =====================
# TOKEN
# =====================
TOKEN = os.getenv("BOT_TOKEN")

# =====================
# 🇩🇪 GERMAN WORDS (130 ta)
# =====================
de_data = [
    ["kitob","Buch","das","Bücher"], ["stol","Tisch","der","Tische"], ["stul","Stuhl","der","Stühle"],
    ["uy","Haus","das","Häuser"], ["maktab","Schule","die","Schulen"], ["o‘qituvchi","Lehrer","der","Lehrer"],
    ["o‘quvchi","Schüler","der","Schüler"], ["mashina","Auto","das","Autos"], ["telefon","Telefon","das","Telefone"],
    ["kompyuter","Computer","der","Computer"], ["eshik","Tür","die","Türen"], ["oyna","Fenster","das","Fenster"],
    ["non","Brot","das","Brote"], ["suv","Wasser","das","-"], ["choy","Tee","der","-"],
    ["sut","Milch","die","-"], ["shahar","Stadt","die","Städte"], ["qishloq","Dorf","das","Dörfer"],
    ["yo‘l","Straße","die","Straßen"], ["daryo","Fluss","der","Flüsse"], ["tog‘","Berg","der","Berge"],
    ["dengiz","Meer","das","Meere"], ["quyosh","Sonne","die","-"], ["oy","Mond","der","-"],
    ["yulduz","Stern","der","Sterne"], ["odam","Mensch","der","Menschen"], ["ayol","Frau","die","Frauen"],
    ["erkak","Mann","der","Männer"], ["bola","Kind","das","Kinder"], ["do‘st","Freund","der","Freunde"],
    ["ota","Vater","der","Väter"], ["ona","Mutter","die","Mütter"], ["pul","Geld","das","-"],
    ["vaqt","Zeit","die","-"], ["ish","Arbeit","die","-"], ["ovqat","Essen","das","-"],
    ["til","Sprache","die","Sprachen"], ["uyqu","Schlaf","der","-"], ["bozor","Market","der","Märkte"],
    ["do‘kon","Laden","der","Läden"], ["park","Park","der","Parks"], ["samolyot","Flugzeug","das","Flugzeuge"],
    ["poezd","Zug","der","Züge"], ["avtobus","Bus","der","Busse"], ["velosiped","Fahrrad","das","Fahrräder"],
    ["rang","Farbe","die","Farben"], ["qizil","rot","-","-"], ["yashil","grün","-","-"],
    ["ko‘k","blau","-","-"], ["oq","weiß","-","-"], ["qora","schwarz","-","-"],
    ["katta","groß","-","-"], ["kichik","klein","-","-"], ["tez","schnell","-","-"],
    ["sekin","langsam","-","-"], ["yangi","neu","-","-"], ["eski","alt","-","-"],
    ["chiroyli","schön","-","-"], ["baxtli","glücklich","-","-"], ["musiqa","Musik","die","-"],
    ["film","Film","der","Filme"], ["o‘yin","Spiel","das","Spiele"], ["internet","Internet","das","-"],
    ["dars","Unterricht","der","-"], ["sinov","Test","der","Tests"], ["natija","Ergebnis","das","Ergebnisse"],
    ["maqsad","Ziel","das","Ziele"], ["orzu","Traum","der","Träume"]
]
# Avtomatik 130 taga to'ldirish
while len(de_data) < 130:
    i = len(de_data) + 1
    de_data.append([f"so‘z{i}", f"Wort{i}", "das", "-"])

# =====================
# 🇬🇧 ENGLISH WORDS (130 ta)
# =====================
en_data = [
    ["kitob","book"], ["stol","table"], ["stul","chair"], ["uy","house"], ["maktab","school"],
    ["o‘qituvchi","teacher"], ["o‘quvchi","student"], ["mashina","car"], ["telefon","phone"],
    ["kompyuter","computer"], ["non","bread"], ["suv","water"], ["choy","tea"], ["sut","milk"],
    ["shahar","city"], ["qishloq","village"], ["yo‘l","road"], ["daryo","river"], ["tog‘","mountain"],
    ["dengiz","sea"], ["quyosh","sun"], ["oy","moon"], ["yulduz","star"], ["pul","money"],
    ["vaqt","time"], ["ish","work"], ["ovqat","food"], ["til","language"], ["do‘st","friend"],
    ["ota","father"], ["ona","mother"], ["bola","child"], ["erkak","man"], ["ayol","woman"],
    ["kalit","key"], ["sumka","bag"], ["ko‘cha","street"], ["park","park"], ["samolyot","plane"],
    ["poezd","train"], ["avtobus","bus"], ["velosiped","bicycle"], ["kasalxona","hospital"],
    ["rang","color"], ["qizil","red"], ["yashil","green"], ["ko‘k","blue"], ["oq","white"],
    ["qora","black"], ["katta","big"], ["kichik","small"], ["tez","fast"], ["sekin","slow"],
    ["yangi","new"], ["eski","old"], ["chiroyli","beautiful"], ["baxtli","happy"], ["musiqa","music"],
    ["film","movie"], ["o‘yin","game"], ["internet","internet"], ["dars","lesson"], ["sinov","test"],
    ["natija","result"], ["maqsad","goal"], ["orzu","dream"]
]
# Avtomatik 130 taga to'ldirish
while len(en_data) < 130:
    i = len(en_data) + 1
    en_data.append([f"so‘z{i}", f"word{i}"])

de_df = pd.DataFrame(de_data, columns=["uz","ger","article","plural"])
en_df = pd.DataFrame(en_data, columns=["uz","en"])

user_lang = {}
stats = {}

# =====================
# HANDLERS
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.chat_id
    stats.setdefault(uid, {"de":0,"en":0})
    keyboard = [["🇩🇪 Nemis tili","🇬🇧 English"]]
    await update.message.reply_text(
        "👋 Assalomu alaykum!\n🌟 LangGo Botga xush kelibsiz.\n📚 Tilni tanlang 🙂",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.chat_id
    text = update.message.text.lower().strip()
    stats.setdefault(uid, {"de":0,"en":0})

    if "nemis" in text:
        user_lang[uid] = "de"
        return await update.message.reply_text("🇩🇪 Nemis tili tanlandi 🙂")
    if "english" in text:
        user_lang[uid] = "en"
        return await update.message.reply_text("🇬🇧 English selected 🙂")

    lang = user_lang.get(uid)
    if not lang: return await update.message.reply_text("🙂 Avval til tanlang.")

    if lang == "de":
        r = de_df[(de_df["uz"] == text) | (de_df["ger"].str.lower() == text)]
        if not r.empty:
            r = r.iloc[0]
            stats[uid]["de"] += 1
            return await update.message.reply_text(f"📘 {r['ger']}\n📌 {r['article']}\n📚 {r['plural']}\n🇺🇿 {r['uz']}")
    elif lang == "en":
        r = en_df[(en_df["uz"] == text) | (en_df["en"] == text)]
        if not r.empty:
            r = r.iloc[0]
            stats[uid]["en"] += 1
            return await update.message.reply_text(f"📘 {r['en']}\n🇺🇿 {r['uz']}")

    await update.message.reply_text("😔 So‘z topilmadi.")

async def send_report(context: ContextTypes.DEFAULT_TYPE):
    for uid, d in stats.items():
        total = d["de"] + d["en"]
        msg = f"🌙 Kunlik hisobot\n\n🇩🇪 Nemischa: {d['de']}\n🇬🇧 Inglizcha: {d['en']}\n📚 Jami: {total}"
        try: await context.bot.send_message(uid, msg)
        except: pass
        stats[uid] = {"de":0,"en":0}

# =====================
# WEB SERVER
# =====================
app_web = Flask('')
@app_web.route('/')
def home(): return "Bot ishlayapti!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host='0.0.0.0', port=port)

Thread(target=run_web, daemon=True).start()

# =====================
# RUNNER
# =====================
async def main():
    if not TOKEN: return print("XATO: BOT_TOKEN topilmadi!")
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    
    if app.job_queue:
        app.job_queue.run_daily(send_report, time=time(hour=17, minute=0))

    print("🚀 BOT READY")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
