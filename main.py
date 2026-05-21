import os
import asyncio
import base64
import requests
from threading import Thread
from flask import Flask

from telegram import (
    Update,
    ReplyKeyboardMarkup
)

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
# AI SYSTEM
# =========================================
SYSTEM_INSTRUCTION = """
Siz 'LangGo Academy' platformasining professional, bilimdon va strategik virtual ustozisiz.

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

- To‘g‘ridan-to‘g‘ri final javobni bermang
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
# MENULAR
# =========================================
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

# =========================================
# START
# =========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    text = (
        "🎓 LangGo Academy platformasiga xush kelibsiz.\n\n"
        "📚 Bu bot:\n"
        "• tarjima qiladi\n"
        "• grammatika tushuntiradi\n"
        "• speaking/writing tekshiradi\n"
        "• matematika va fanlarni o‘rgatadi\n"
        "• rasmli savollarni tahlil qiladi\n\n"
        "📌 Kerakli bo‘limni tanlang:"
    )

    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(
            main_menu,
            resize_keyboard=True
        )
    )

# =========================================
# GEMINI FUNCTION
# =========================================
async def ask_gemini(prompt, history, image_bytes=None):

    url = (
        "https://generativelanguage.googleapis.com/v1/models/"
        f"gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    )

    headers = {
        "Content-Type": "application/json"
    }

    contents = []

    # HISTORY
    for item in history:

        contents.append({
            "role": item["role"],
            "parts": [
                {
                    "text": item["text"]
                }
            ]
        })

    current_parts = []

    # IMAGE
    if image_bytes:

        image_base64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        current_parts.append({
            "inlineData": {
                "mimeType": "image/jpeg",
                "data": image_base64
            }
        })

    current_parts.append({
        "text": prompt
    })

    contents.append({
        "role": "user",
        "parts": current_parts
    })

    payload = {
        "contents": contents,

        "systemInstruction": {
            "parts": [
                {
                    "text": SYSTEM_INSTRUCTION
                }
            ]
        },

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
            headers=headers,
            json=payload,
            timeout=60
        )

        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)

        if response.status_code != 200:
            return f"⚠️ API XATOLIK:\n{response.text}"

        data = response.json()

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:

        return f"⚠️ TEXNIK XATOLIK:\n{str(e)}"

# =========================================
# HANDLE MESSAGE
# =========================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = ""
    photo_bytes = None

    # PHOTO
    if update.message.photo:

        photo = update.message.photo[-1]

        file = await photo.get_file()

        photo_bytes = await file.download_as_bytearray()

        text = (
            update.message.caption.strip()
            if update.message.caption
            else "Rasm ichidagi savolni tushuntiring."
        )

    # TEXT
    elif update.message.text:

        text = update.message.text.strip()

        # MENU
        if text == "🌍 Jahon tillari":

            await update.message.reply_text(
                "🌍 Tilni tanlang:",
                reply_markup=ReplyKeyboardMarkup(
                    languages_menu,
                    resize_keyboard=True
                )
            )
            return

        if text == "🔢 Aniq fanlar":

            await update.message.reply_text(
                "📚 Fanni tanlang:",
                reply_markup=ReplyKeyboardMarkup(
                    science_menu,
                    resize_keyboard=True
                )
            )
            return

        if text == "⬅️ Orqaga":

            await update.message.reply_text(
                "🏠 Asosiy menyu:",
                reply_markup=ReplyKeyboardMarkup(
                    main_menu,
                    resize_keyboard=True
                )
            )
            return

        # SUBJECT
        subjects = [
            "Nemis",
            "Ingliz",
            "Rus",
            "Turk",
            "Matematika",
            "Fizika",
            "Kimyo",
            "Biologiya",
            "Adabiyot",
            "Ona tili"
        ]

        is_subject = any(
            s.lower() in text.lower()
            for s in subjects
        )

        if is_subject:

            context.user_data["subject"] = text
            context.user_data["history"] = []

            await update.message.reply_text(
                f"✅ {text} bo‘limi tanlandi.\n\n"
                "📩 Endi savolingizni yuboring."
            )

            return

    # SUBJECT CHECK
    subject = context.user_data.get("subject")

    if not subject:

        await update.message.reply_text(
            "⚠️ Avval bo‘lim tanlang!"
        )

        return

    # HISTORY
    if "history" not in context.user_data:
        context.user_data["history"] = []

    history = context.user_data["history"]

    # FINAL PROMPT
    final_prompt = (
        f"Tanlangan bo‘lim: {subject}\n\n"
        f"Foydalanuvchi savoli:\n{text}"
    )

    try:

        if not GEMINI_KEY:

            await update.message.reply_text(
                "⚠️ GEMINI_API_KEY topilmadi!"
            )

            return

        # TYPING
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )

        # AI
        answer = await ask_gemini(
            prompt=final_prompt,
            history=history,
            image_bytes=photo_bytes
        )

        # SAVE HISTORY
        history.append({
            "role": "user",
            "text": text
        })

        history.append({
            "role": "model",
            "text": answer
        })

        context.user_data["history"] = history[-12:]

        # SEND
        if len(answer) > 4096:

            for i in range(0, len(answer), 4096):

                await update.message.reply_text(
                    answer[i:i + 4096]
                )

        else:

            await update.message.reply_text(answer)

    except Exception as e:

        print("ERROR:", e)

        await update.message.reply_text(
            "⚠️ Texnik xatolik yuz berdi."
        )

# =========================================
# FLASK START
# =========================================
def run_flask():

    port = int(
        os.environ.get("PORT", 10000)
    )

    app_web.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )

# =========================================
# MAIN
# =========================================
def main():

    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN topilmadi")
        return

    if not GEMINI_KEY:
        print("❌ GEMINI_API_KEY topilmadi")
        return

    # FLASK
    flask_thread = Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()

    # BOT
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.PHOTO)
            & ~filters.COMMAND,
            handle_message
        )
    )

    print("🚀 LangGo Academy ishga tushdi")

    app.run_polling()

# =========================================
# RUN
# =========================================
if __name__ == "__main__":
    main()
