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
# TOKENS
# ====================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

# ====================================
# AI SYSTEM (FULL USTOZ MODE)
# ====================================
SYSTEM_INSTRUCTION = """
Siz “LangGo Academy” platformasining eng professional, sabrli va kuchli virtual ustozisiz.

Vazifangiz:
- tayyor javob bermaslik
- o‘quvchini o‘ylashga majbur qilish
- bosqichma-bosqich o‘rgatish

==============================
TILLAR
==============================

■ 1 SO‘Z:
- tarjima
- 1 misol
- tarjima

■ IBORA / GAP:
- tabiiy tarjima
- ma’nosi
- misol

■ GRAMMATIKA:
- tushuntirish
- 3 misol
- mashq

==============================
FANLAR
==============================

- final javob bermang
- tushuntiring
- formula
- misol
- mashq

==============================
SPEAKING / WRITING
==============================

- IELTS style feedback
- grammar + vocabulary + structure

==============================
RASM
==============================

- tushuntir
- yo‘l ko‘rsat
- final javob bermang

==============================
USLUB
==============================

- “Siz” deb murojaat
- ustoz kabi yozing
- tushunarli va professional
"""

# ====================================
# FLASK
# ====================================
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "LangGo Academy ishlayapti 🚀"

# ====================================
# MENUS
# ====================================
main_menu = [
    ['🌍 Jahon tillari', '🔢 Aniq fanlar']
]

# ====================================
# GEMINI (FIXED + FALLBACK MODEL)
# ====================================
async def ask_gemini(prompt, history, image_bytes=None):

    models = [
        "gemini-1.5-pro",
        "gemini-pro"
    ]

    last_error = None

    for model in models:

        try:
            url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={GEMINI_KEY}"

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
                "systemInstruction": {
                    "parts": [{"text": SYSTEM_INSTRUCTION}]
                },
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.95,
                    "topK": 40,
                    "maxOutputTokens": 2048
                }
            }

            response = await asyncio.to_thread(
                requests.post,
                url,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

            last_error = response.text

        except Exception as e:
            last_error = str(e)

    return f"⚠️ AI xatolik:\n{last_error}"

# ====================================
# START
# ====================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        "🎓 LangGo Academy AI Ustoz ishga tayyor!",
        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    )

# ====================================
# MESSAGE HANDLER
# ====================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text or "Rasm savoli"
    photo_bytes = None

    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        photo_bytes = await file.download_as_bytearray()

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    subject = context.user_data.get("subject", "Umumiy")

    prompt = f"""
Bo‘lim: {subject}
Savol: {text}
"""

    history = context.user_data.get("history", [])

    answer = await ask_gemini(prompt, history, photo_bytes)

    history.append({"role": "user", "text": text})
    history.append({"role": "model", "text": answer})

    context.user_data["history"] = history[-10:]

    await update.message.reply_text(answer)

# ====================================
# FLASK RUN
# ====================================
def run_flask():
    app_web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# ====================================
# MAIN
# ====================================
def main():

    if not BOT_TOKEN or not GEMINI_KEY:
        print("❌ TOKEN YO‘Q")
        return

    Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    print("🚀 LANGGO ACADEMY BOT ISHLADI")
    app.run_polling()

if __name__ == "__main__":
    main()
