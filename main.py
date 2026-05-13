# =========================
# LANGGO ULTIMATE BOT
# FINAL VERSION FOR GITHUB
# =========================

!pip install python-telegram-bot==20.7 nest_asyncio pandas -q

import nest_asyncio
nest_asyncio.apply()

import asyncio
import pandas as pd
from datetime import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# =========================
# 🔐 TOKEN
# =========================
TOKEN = "8649876958:AAFO3LLn3IrL5GZ8-olnJkOpVQiGPMN4ozc"

# =========================
# 📊 DATABASES (Nemis va Ingliz tili)
# =========================
de_data = [
    ["kitob","Buch","das","Bücher"], ["stol","Tisch","der","Tische"],
    ["stul","Stuhl","der","Stühle"], ["uy","Haus","das","Häuser"],
    ["maktab","Schule","die","Schulen"], ["o‘qituvchi","Lehrer","der","Lehrer"],
    ["mashina","Auto","das","Autos"], ["non","Brot","das","Brote"],
    ["suv","Wasser","das","-"], ["ona","Mutter","die","Mütter"]
]

en_data = [
    ["kitob","book"], ["stol","table"], ["uy","house"],
    ["mashina","car"], ["suv","water"], ["non","bread"]
]

de_df = pd.DataFrame(de_data, columns=["uz","ger","article","plural"])
en_df = pd.DataFrame(en_data, columns=["uz","en"])

# Xotira va Statistika
user_lang = {}
stats = {}

# =========================
# 🏁 START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    if user_id not in stats:
        stats[user_id] = {"de":0, "en":0}

    keyboard = [["🇩🇪 Nemis tili", "🇬🇧 English"]]
    await update.message.reply_text(
        "👋 Assalomu alaykum, qadrli o'quvchim!\n\n"
        "🌟 LangGo Botga xush kelibsiz. Men sizga tillarni o‘rganishda yordam beraman.\n"
        "🚀 Marhamat, o'zingizga kerakli tilni tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# =========================
# 🌙 DAILY REPORT (MULOYIM TALQIN)
# =========================
async def send_report(context: ContextTypes.DEFAULT_TYPE):
    for user_id, data in stats.items():
        total = data["de"] + data["en"]
        text = (
            f"🌙 **Xayrli kech, aziz o'quvchim!**\n\n"
            f"Bugungi natijalaringiz:\n"
            f"🇩🇪 Nemischa: {data['de']} ta\n"
            f"🇬🇧 Inglizcha: {data['en']} ta\n"
            f"📊 Jami: {total} ta\n\n"
        )

        if total < 5:
            text += (
                "💪 **Bugun biroz kamroq ishladingiz, lekin bu xafa bo'lishga sabab emas.**\n"
                "📚 O‘zingiz ustingizda ishlashdan to'xtamang, men sizga ishonaman! 😊"
            )
        else:
            text += (
                "🌟 **Barakalla! Siz bilan faxrlanaman!**\n"
                "🔥 Bugun juda ajoyib natija ko'rsatdingiz. Shunday davom eting! 🚀"
            )

        try:
            await context.bot.send_message(chat_id=user_id, text=text, parse_mode='Markdown')
        except: pass
        stats[user_id] = {"de":0, "en":0}

# =========================
# ✍️ HANDLE MESSAGES
# =========================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    text = update.message.text.lower().strip()
    
    if user_id not in stats: stats[user_id] = {"de":0, "en":0}

    if "nemis" in text:
        user_lang[user_id] = "de"
        await update.message.reply_text("🇩🇪 Nemis tili tanlandi! O'rganishda omad tilayman! ✨")
        return
    if "english" in text:
        user_lang[user_id] = "en"
        await update.message.reply_text("🇬🇧 English selected! Keep going! 🚀")
        return

    lang = user_lang.get(user_id)
    if not lang:
        await update.message.reply_text("🙂 Avval tilni tanlang, azizim.")
        return

    if lang == "de":
        row = de_df[(de_df["uz"] == text) | (de_df["ger"].str.lower() == text)]
        if not row.empty:
            r = row.iloc[0]
            stats[user_id]["de"] += 1
            await update.message.reply_text(f"📘 {r['ger']}\n📌 Rodi: {r['article']}\n📚 Plural: {r['plural']}\n🇺🇿 Tarjima: {r['uz']}\n\n🌟 Davom eting!")
        else:
            await update.message.reply_text("😔 Bu so'z bazada yo'q.")
    
    elif lang == "en":
        row = en_df[(en_df["uz"] == text) | (en_df["en"] == text)]
        if not row.empty:
            r = row.iloc[0]
            stats[user_id]["en"] += 1
            await update.message.reply_text(f"📘 English: {r['en']}\n🇺🇿 Tarjima: {r['uz']}\n\n🌟 Keep going!")
        else:
            await update.message.reply_text("😔 Word not found.")

# =========================
# 🚀 RUN BOT
# =========================
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.job_queue.run_daily(send_report, time=time(hour=17, minute=0))

    print("🚀 Bot ishlayapti...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
