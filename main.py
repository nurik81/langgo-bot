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

# =========================================
# TOKENLAR
# =========================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

# =========================================
# AI SYSTEM (SIZNING O‘ZGARMAGAN KODINGIZ)
# =========================================
SYSTEM_INSTRUCTION = """
Siz 'LangGo Academy' platformasining professional, bilimdon va strategik virtual virtual ustozisiz.

Sizning vazifangiz foydalanuvchiga tayyor javobni berish emas, balki uni o‘qitish, tushuntirish va yo‘naltirishdir.

======================================
1. TILLAR BO'LIMI
======================================

Siz:
- Ingliz
- Nemis
- Rus
- Turk

tillarini professional darajada bilasiz.

Agar foydalanuvchi:
- bitta so‘z
- so‘z birikmasi
- gap
- katta matn
- ibora
- idiom
- slang
- kundalik suhbat

yuborsa:

- tabiiy tarjima qiling
- ma'nosi bilan tushuntiring
- kerak bo‘lsa grammatik izoh bering
- misol yozing

Agar idiom yoki ibora bo‘lsa:
- asl ma'nosini tushuntiring
- qachon ishlatilishini ayting
- misol yozing

Agar grammatika savoli bo‘lsa:
- professional tushuntiring
- kamida 3 ta misol yozing
- tarjimasini yozing
- oxirida mashq bering

Agar speaking yoki writing yuborsa:
- grammar
- vocabulary
- coherence
- naturalness

bo‘yicha professional feedback bering.

======================================
2. ANIQ FANLAR
======================================

- To‘g‘ridan-to‘g‘ri javob bermang
- Formulani tushuntiring
- Nazariyani oddiy tilda izohlang
- Misol ishlang
- Keyin mashq bering
- Bosqichma-bosqich tushuntiring

======================================
3. SPEAKING VA WRITING
======================================

- IELTS ustozidek yordam bering
- Writingni professional tekshiring
- Speaking uchun tabiiy javob yozing

======================================
4. RASM YUBORILGANDA
======================================

- Rasm ichidagi savolni tushuntiring
- Yo‘l ko‘rsating
- Final javobni bermang

======================================
5. CHAT XOTIRASI
======================================

- Oldingi savollarni eslab qoling
- Suhbatni tabiiy davom ettiring

======================================
USLUB
======================================

- Doim “Siz” deb murojaat qiling
- Professional ustozdek yozing
- Juda ko‘p emoji ishlatmang
"""

# =========================================
# FLASK
# =========================================
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "LangGo Academy ishlayapti 🚀"

# =========================================
# MENYU
# =========================================
main_menu = [
    ['🌍 Jahon tillari', '🔢 Aniq fanlar']
]

# =========================================
# GEMINI (TO‘G‘RI VERSION)
# =========================================
async def ask_gemini(prompt, history, image_bytes=None):

    # 🔥 ENG BARQAROR ENDPOINT
    url = (
        "https://generativelanguage.googleapis.com/v1/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    )

    contents = []

    # HISTORY
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

    # ⚠️ systemInstruction O‘CHIRILDI (xatoni shu beradi)
    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.95,
            "topK": 40,
            "maxOutputTokens": 2048
        }
    }

    try:
        response = await asyncio.to_thread(
            requests.post,
            url,
            json=payload,
            timeout=60
        )

        print("STATUS:", response.status_code)
        print("TEXT:", response.text)

        if response.status_code != 200:
            return f"⚠️ API XATOLIK:\n{response.text}"

        data = response.json()

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return f"⚠️ ERROR: {str(e)}"

# =========================================
# HANDLER
# =========================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text or "Rasm savoli"

    subject = context.user_data.get("subject", "Umumiy")

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    prompt = f"{SYSTEM_INSTRUCTION}\n\nBo‘lim: {subject}\nSavol: {text}"

    answer = await ask_gemini(prompt, context.user_data.get("history", []))

    await update.message.reply_text(answer)

# =========================================
# START
# =========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "LangGo Academy AI tayyor 🚀",
        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    )

# =========================================
# FLASK RUN
# =========================================
def run_flask():
    app_web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# =========================================
# MAIN
# =========================================
def main():

    if not BOT_TOKEN or not GEMINI_KEY:
        print("TOKEN YO‘Q")
        return

    Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    print("🚀 BOT ISHLADI")
    app.run_polling()

if __name__ == "__main__":
    main()
