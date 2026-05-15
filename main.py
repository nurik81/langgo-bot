import asyncio
import google.generativeai as genai

from telegram import (
    Update,
    ReplyKeyboardMarkup
)

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

BOT_TOKEN = "BOT_TOKENINGIZ"
GEMINI_KEY = "GEMINI_API_KEYINGIZ"

# ====================================
# GEMINI
# ====================================

genai.configure(api_key=GEMINI_KEY)

SYSTEM_INSTRUCTION = """
Siz 'LangGo AI' virtual akademiyasining professional ustozisiz.

ASOSIY QOIDALAR:

1. Siz hech qachon tayyor javob bermaysiz.

2. Foydalanuvchini o‘ylashga majbur qilasiz.

3. Agar foydalanuvchi:
- test
- variant
- homework
- speaking
- writing
- esse
- insho
- imtihon savoli
yuborsa:

❌ tayyor javobni aytmang
❌ variantni aytmang
❌ final answer yozmang

✅ mavzuni tushuntiring
✅ qadamlarni ko‘rsating
✅ qanday o‘ylashni o‘rgating
✅ grammar explain qiling
✅ useful phrases bering
✅ hint bering
✅ misollar bilan tushuntiring

4. Matematika va fizikada:
- formulani yozing
- formula nimani anglatishini tushuntiring
- ishlash usulini ko‘rsating
- qaysi formula ishlatilishini ayting
- lekin oxirgi javobni chiqarmang

5. Kimyo va biologiyada:
- reaction
- process
- terminology
- formula
- theory
tushuntiring.

6. Tillar:
Siz:
- o‘zbek
- ingliz
- nemis
- rus
- turk
tillarini tushunasiz.

7. Agar foydalanuvchi rasm tashlasa:
- savolni analiz qiling
- tushuntiring
- lekin javobni aytmang

8. Foydalanuvchiga doim:
"Siz"
deb murojaat qiling.

9. Professional va ustozlardek gapiring.

10. Emojilar juda kam ishlatilsin.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

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

    await update.message.reply_text(
        "🎓 LangGo AI akademiyasiga xush kelibsiz.\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=ReplyKeyboardMarkup(
            main_menu,
            resize_keyboard=True
        )
    )

# ====================================
# HANDLE MESSAGE
# ====================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    # MAIN MENU

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

    # SUBJECT SAVE

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

    if any(s.lower() in text.lower() for s in subjects):

        context.user_data["subject"] = text

        await update.message.reply_text(
            f"✅ {text} bo‘limi tanlandi.\n\n"
            "📩 Savolingizni yuboring."
        )

        return

    # SUBJECT

    subject = context.user_data.get("subject", "Umumiy")

    try:

        prompt = f"""
Fan: {subject}

Foydalanuvchi savoli:
{text}

MUHIM:
- Tayyor javobni bermang
- Variantni aytmang
- Final answer yozmang
- O‘quvchini o‘ylashga majbur qiling
- Ustozdek tushuntiring
- Step-by-step yo‘l ko‘rsating
"""

        response = await asyncio.to_thread(
            model.generate_content,
            prompt
        )

        ai_text = getattr(response, "text", None)

        if not ai_text:
            ai_text = "⚠️ AI javob qaytarmadi."

        await update.message.reply_text(ai_text)

    except Exception as e:

        print("ERROR:", e)

        await update.message.reply_text(
            "⚠️ Texnik xatolik yuz berdi."
        )

# ====================================
# MAIN
# ====================================

def main():

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("🚀 LangGo AI ishga tushdi")

    app.run_polling()

# ====================================
# START
# ====================================

if __name__ == "__main__":
    main()
