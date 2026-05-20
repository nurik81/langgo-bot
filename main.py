import os
import asyncio
import base64
import requests
from threading import Thread
from flask import Flask

from telegram import Update, ReplyKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# ====================================
# TOKENLAR
# ====================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

# ====================================
# AI SYSTEM (BIRLASHTIRILGAN)
# ====================================
SYSTEM_INSTRUCTION = """
Siz 'LangGo Academy' platformasining professional, bilimdon va strategik virtual ustozisiz.

Sizning asosiy maqsadingiz — foydalanuvchiga tayyor javob berish emas, balki uni fikrlashga majbur qilish va yo'naltirishdir.

======================================
1. TILLAR BO'LIMI
======================================

Agar BIR SO‘Z yuborilsa:
- Tarjima
- 1 misol gap
- Tarjima

Agar GRAMMATIKA so‘ralsa:
- Tushuntirish
- 3+ misol
- Mashq berish

======================================
2. ANIQ FANLAR
======================================

- To‘g‘ridan-to‘g‘ri javob bermang
- Tushuntiring
- Formula izohlang
- 1 misol ishlang
- 1 masala bering

======================================
3. SPEAKING & WRITING
======================================

- IELTS ustozidek tekshiring
- Grammar, vocabulary, structure tushuntiring

======================================
4. RASM
======================================

- Tahlil qiling
- Yo‘l ko‘rsating
- Final javobni bermang

======================================
USLUB:
- “Siz” deb murojaat qiling
- Ustoz kabi yozing
- Professional ohang
"""

# ====================================
# FLASK
# ====================================
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "LangGo Academy ishlayapti 🚀"

# ====================================
# MENULAR
# ====================================
main_menu = [
    ['🌍 Jahon tillari', '🔢 Aniq fanlar']
]

languages_menu = [
    ['🇩🇪 Nemis tili', '🇬🇧 Ingliz tili'],
    ['🇷🇺 Rus tili', '🇹🇷 Turk tili'],
    ['⬅️ Orqaga']
]

science_menu = [
    ['🧮 Matematika', '🔭 Fizika'],
    ['🧪 Kimyo', '🧬 Biologiya'],
    ['📚 Adabiyot', '📝 Ona tili'],
    ['⬅️ Orqaga']
]

# ====================================
# START
# ====================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    text = (
        "🎓 LangGo Academy ga xush kelibsiz.\n\n"
        "📚 Tillar va fanlarni professional o‘rganing.\n\n"
        "📌 Bo‘lim tanlang:"
    )

    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    )

# ====================================
# GEMINI
# ====================================
async def ask_gemini(prompt, history, image_bytes=None):

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    )

    contents = []

    for item in history:
        contents.append({
            "role": item["role"],
            "parts": [{"text": item["text"]}]
        })

    parts = []

    if image_bytes:
        parts.append({
            "inlineData": {
                "mimeType": "image/jpeg",
                "data": base64.b64encode(image_bytes).decode()
            }
        })

    parts.append({"text": prompt})

    contents.append({
        "role": "user",
        "parts": parts
    })

    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.95,
            "maxOutputTokens": 2048
        }
    }

    response = await asyncio.to_thread(
        requests.post,
        url,
        json=payload,
        timeout=60
    )

    if response.status_code != 200:
        return "API xatolik"

    try:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "AI javob bermadi"

# ====================================
# MESSAGE HANDLER
# ====================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = ""
    photo_bytes = None

    # PHOTO
    if update.message.photo:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        photo_bytes = await file.download_as_bytearray()

        text = update.message.caption or "Rasmni tushuntiring"

    # TEXT
    elif update.message.text:
        text = update.message.text.strip()

        if text == "🌍 Jahon tillari":
            await update.message.reply_text(
                "Til tanlang:",
                reply_markup=ReplyKeyboardMarkup(languages_menu, resize_keyboard=True)
            )
            return

        if text == "🔢 Aniq fanlar":
            await update.message.reply_text(
                "Fan tanlang:",
                reply_markup=ReplyKeyboardMarkup(science_menu, resize_keyboard=True)
            )
            return

        if text == "⬅️ Orqaga":
            await update.message.reply_text(
                "Asosiy menyu:",
                reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
            )
            return

        subjects = ["Nemis", "Ingliz", "Rus", "Turk", "Matematika", "Fizika", "Kimyo", "Biologiya"]

        if any(s.lower() in text.lower() for s in subjects):
            context.user_data["subject"] = text
            context.user_data["history"] = []
            await update.message.reply_text("Bo‘lim tanlandi. Savol yuboring")
            return

    subject = context.user_data.get("subject")

    if not subject:
        await update.message.reply_text("Avval bo‘lim tanlang")
        return

    if "history" not in context.user_data:
        context.user_data["history"] = []

    history = context.user_data["history"]

    final_prompt = f"Bo‘lim: {subject}\nSavol: {text}"

    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    answer = await ask_gemini(final_prompt, history, photo_bytes)

    history.append({"role": "user", "text": text})
    history.append({"role": "model", "text": answer})

    context.user_data["history"] = history[-12:]

    await update.message.reply_text(answer)

# ====================================
# FLASK
# ====================================
def run_flask():
    app_web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# ====================================
# MAIN
# ====================================
def main():

    if not BOT_TOKEN or not GEMINI_KEY:
        print("Tokenlar yo‘q")
        return

    Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    print("Bot ishga tushdi 🚀")
    app.run_polling()

# ====================================
# RUN
# ====================================
if __name__ == "__main__":
    main()
