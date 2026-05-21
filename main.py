import os
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

SYSTEM = """
Siz LangGo Academy virtual ustozisiz.

Vazifa:
- tillarni o‘rgatish
- grammar tushuntirish
- speaking/writing yordam
- matematika va fanlarni tushuntirish

Doim professional ustoz kabi javob bering.
"""

# ==================================
# GEMINI
# ==================================
def ask_ai(user_text):

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"{SYSTEM}\n\nFoydalanuvchi: {user_text}"
                    }
                ]
            }
        ]
    }

    response = requests.post(url, json=payload)

    print(response.text)

    if response.status_code != 200:
        return "API xatolik chiqdi."

    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "AI javob bera olmadi."

# ==================================
# MESSAGE
# ==================================
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    await update.message.reply_text("⏳ O‘ylayapman...")

    answer = ask_ai(text)

    await update.message.reply_text(answer)

# ==================================
# MAIN
# ==================================
def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT, message_handler)
    )

    print("LangGo Academy ishga tushdi 🚀")

    app.run_polling()

if __name__ == "__main__":
    main()
