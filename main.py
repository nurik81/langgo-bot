import os
import asyncio
import pandas as pd
from datetime import time
import pytz

from flask import Flask
from threading import Thread

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Alohida fayllardan so'zlarni import qilish
try:
    from german_words import de_data
    from english_words import en_data
except ImportError:
    de_data = []
    en_data = []

# =====================
# 🔑 YANGI TOKEN
# =====================
TOKEN = "8649876958:AAF3HaeCbT_qOMo2e052kJ-mpNOpoLqPhYA"

# =====================
# 📊 DATAFRAME TAYYORLASH
# =====================
de_df = pd.DataFrame(de_data, columns=["uz", "ger", "article", "plural"])
en_df = pd.DataFrame(en_data, columns=["uz", "en"])

# =====================
# 🧠 MEMORY
# =====================
user_lang = {}
stats = {}

# =====================
# 🚀 START KOMANDASI
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.chat_id
    stats.setdefault(uid, {"de": 0, "en": 0})

    keyboard = [["🇩🇪 Nemis tili", "🇬🇧 English"]]

    await update.message.reply_text(
        "👋 Assalomu alaykum!\n\n"
        "🌟 LangGo Botga xush kelibsiz.\n"
        "📚 Nemis va ingliz tilini birga o‘rganamiz.\n\n"
        "🚀 O‘rganmoqchi bo‘lgan tilingizni tanlang 🙂",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# =====================
# 🌙 KUNLIK HISOBOT
# =====================
async def send_report(context: ContextTypes.DEFAULT_TYPE):
    for uid, d in stats.items():
        total = d["de"] + d["en"]
        msg = (
            f"🌙 Kunlik hisobot\n\n"
            f"🇩🇪 Nemischa: {d['de']}\n"
            f"🇬🇧 Inglizcha: {d['en']}\n"
            f"📚 Jami: {total}\n\n"
        )
        if total < 5:
            msg += (
                "💪 Bugun biroz kamroq ishladingiz.\n\n"
                "📚 O‘zingiz ustingizda yana ham ko‘proq ishlang.\n"
                "🚀 Har kuni oz bo‘lsa ham oldinga yurish katta natija beradi 🙂"
            )
        else:
            msg += (
                "🌟 Barakalla!\n\n"
                "🔥 Bugun juda yaxshi ishladingiz.\n"
                "📚 Siz asta-sekin kuchli levelga chiqyapsiz 🚀\n"
                "👏 Shunday davom eting!"
            )
        try:
            await context.bot.send_message(uid, msg)
        except:
            pass
        stats[uid] = {"de": 0, "en": 0}

# =====================
# 🔍 SO'ZLARNI QIDIRISH (HANDLE)
# =====================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.chat_id
    text = update.message.text.lower().strip()
    stats.setdefault(uid, {"de": 0, "en": 0})

    if "nemis" in text:
        user_lang[uid] = "de"
        await update.message.reply_text(
            "🇩🇪 Nemis tili tanlandi 🙂\n\n"
            "📚 Nemis tilini o‘rganishda sizga omad tilaymiz!\n"
            "✨ Endi so‘z yuboring."
        )
        return

    if "english" in text:
        user_lang[uid] = "en"
        await update.message.reply_text(
            "🇬🇧 English selected 🙂\n\n"
            "📚 We wish you success in learning English!\n"
            "✨ Send a word."
        )
        return

    lang = user_lang.get(uid)
    if not lang:
        return await update.message.reply_text("🙂 Avval til tanlang.")

    # 🇩🇪 Nemischa qidiruv
    if lang == "de":
        r = de_df[(de_df["uz"] == text) | (de_df["ger"].str.lower() == text)]
        if not r.empty:
            r = r.iloc[0]
            stats[uid]["de"] += 1
            return await update.message.reply_text(
                f"📘 Nemischa: {r['ger']}\n📌 Artikl: {r['article']}\n"
                f"📚 Plural: {r['plural']}\n🇺🇿 Tarjimasi: {r['uz']}\n\n🌟 Davom eting!"
            )
        return await update.message.reply_text("😔 Kechirasiz, bu so‘z bazada topilmadi.")

    # 🇬🇧 Inglizcha qidiruv
    if lang == "en":
        r = en_df[(en_df["uz"] == text) | (en_df["en"].str.lower() == text)]
        if not r.empty:
            r = r.iloc[0]
            stats[uid]["en"] += 1
            return await update.message.reply_text(
                f"📘 English: {r['en']}\n🇺🇿 Uzbek: {r['uz']}\n\n🌟 Keep going!"
            )
        return await update.message.reply_text("😔 Sorry, this word was not found.")

# =====================
# 🌐 WEB SERVER (Anti-Sleep)
# =====================
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "LangGo Bot is Online! 🚀"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host='0.0.0.0', port=port)

# =====================
# 🏁 ASOSIY ISHGA TUSHIRISH
# =====================
async def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    uz_tz = pytz.timezone("Asia/Tashkent")
    if application.job_queue:
        application.job_queue.run_daily(
            send_report,
            time=time(hour=22, minute=0, tzinfo=uz_tz)
        )

    print("🚀 Bot ishga tushdi...")

    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        await asyncio.Event().wait()

if __name__ == "__main__":
    # Web serverni alohida thread'da ishga tushirish
    t = Thread(target=run_web)
    t.daemon = True
    t.start()
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")
