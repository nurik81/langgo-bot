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

BOT_TOKEN = "8649876958:AAEkEUERLE2rbXEQTcPcqgeDhOftv7_viuw"
GEMINI_KEY = "AIzaSyA8d5erXLy-k6Y6eNLZvZ5O9RI14vkkWPY"

# ====================================
# GEMINI AI
# ====================================

genai.configure(api_key=GEMINI_KEY)

SYSTEM_INSTRUCTION = """
Siz 'LangGo Academy' platformasining professional virtual ustozisiz.

Sizning asosiy vazifangiz:
- foydalanuvchini o‘rgatish
- tushuntirish
- fikrlashga majbur qilish
- yo‘l ko‘rsatish

Siz hech qachon oddiy javob mashinasi emassiz.

======================================
MUHIM QOIDALAR
======================================

1. Siz hech qachon tayyor javob bermaysiz.

2. Agar foydalanuvchi:
- test
- variant
- homework
- speaking
- writing
- esse
- insho
- imtihon savoli
- worksheet
yuborsa:

❌ to‘g‘ridan-to‘g‘ri javobni aytmang
❌ variantni aytmang
❌ final answer yozmang

✅ mavzuni tushuntiring
✅ step-by-step yo‘l ko‘rsating
✅ qanday fikrlash kerakligini o‘rgating
✅ useful phrases bering
✅ grammar explain qiling
✅ hint bering
✅ misollar bilan tushuntiring

3. Matematika va fizikada:
- formulani yozing
- formula nimani anglatishini tushuntiring
- qaysi formuladan foydalanishni ayting
- ishlash yo‘lini ko‘rsating
- lekin oxirgi javobni chiqarmang

4. Kimyo va biologiyada:
- process
- reaction
- terminology
- formula
- theory
tushuntiring.

5. Tillar:
Siz:
- o‘zbek
- ingliz
- nemis
- rus
- turk
tillarini tushunasiz.

6. Agar foydalanuvchi rasm tashlasa:
- rasm ichidagi savolni analiz qiling
- savolni tushuntiring
- qanday ishlashni ayting
- lekin javobni aytmang

7. Speaking va writing:
❌ tayyor speaking yozib bermang
❌ tayyor esse yozib bermang

✅ idea bering
✅ structure bering
✅ useful words bering
✅ grammar explain qiling

8. Foydalanuvchiga doim:
"Siz"
deb murojaat qiling.

9. Professional ustoz kabi gapiring.

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

    welcome_text = (
        "🎓 LangGo Academy platformasiga xush kelibsiz.\n\n"
        "📚 Bu yerda siz:\n"
        "• tillarni\n"
        "• matematika va fizikani\n"
        "• kimyo va biologiyani\n"
        "• speaking va writingni\n"
        "professional tarzda o‘rganishingiz mumkin.\n\n"
        "📌 Kerakli bo‘limni tanlang:"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=ReplyKeyboardMarkup(
            main_menu,
            resize_keyboard=True
        )
    )

# ====================================
# HANDLE MESSAGE
# ====================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()

    # =========================
    # MAIN MENU
    # =========================

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

    # =========================
    # SUBJECT SAVE
    # =========================

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
            "📩 Endi savolingizni yuboring."
        )

        return

    # =========================
    # SUBJECT
    # =========================

    subject = context.user_data.get(
        "subject",
        "Umumiy"
    )

    # =========================
    # AI PROMPT
    # =========================

    prompt = f"""
Fan yoki yo‘nalish:
{subject}

Foydalanuvchi savoli:
{text}

MUHIM:
- Tayyor javobni bermang
- Variantni aytmang
- Final answer yozmang
- O‘quvchini fikrlashga majbur qiling
- Professional ustozdek tushuntiring
- Step-by-step yo‘l ko‘rsating
"""

    try:

        # =========================
        # GEMINI REQUEST
        # =========================

        response = await asyncio.to_thread(
            model.generate_content,
            prompt
        )

        ai_text = getattr(
            response,
            "text",
            None
        )

        if not ai_text:
            ai_text = (
                "⚠️ AI javob qaytarmadi.\n"
                "Keyinroq qayta urinib ko‘ring."
            )

        await update.message.reply_text(ai_text)

    except Exception as e:

        print("ERROR:", e)

        await update.message.reply_text(
            "⚠️ Texnik xatolik yuz berdi.\n"
            "Keyinroq qayta urinib ko‘ring."
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
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("🚀 LangGo Academy ishga tushdi")

    app.run_polling()

# ====================================
# START
# ====================================

if __name__ == "__main__":
    main()
