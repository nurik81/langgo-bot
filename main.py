import os
import asyncio
import google.generativeai as genai

from flask import Flask
from threading import Thread

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
BOT_TOKEN = "8649876958:AAGH5r85Qnamgh5bZ6G09Z96r5k-bU7dxHA"
GEMINI_KEY = "AIzaSyA8d5erXLy-k6Y6eNLZvZ5O9RI14vkkWPY"

# ====================================
# GEMINI AI
# ====================================
genai.configure(api_key=GEMINI_KEY)

SYSTEM_INSTRUCTION = """
Siz 'LangGo Academy' platformasining professional, bilimdon va strategik virtual ustozisiz.
Sizning maqsadingiz foydalanuvchiga tayyor javobni berish emas, balki uni fikrlashga majbur qilish va yo'naltirishdir.

======================================
QAT'IY METODIK MAJBURIYATLARINGIZ:
======================================

1. JAHON TILLARI BO'LIMI (Ingliz, Nemis, Rus, Turk tillari):
Siz ushbu tillarni mukammal bilasiz. Foydalanuvchi murojaat qilganda faqat quyidagi 2 ta holat bo'yicha javob bering:

   A. Agar foydalanuvchi FAQAT BITTA SO'Z yuborsa (Masalan: "olma", "kitob", "qalam"):
      - Shu so'zning foydalanuvchi tanlagan tildagi to'g'ri tarjimasini (artikli yoki o'ziga xos xususiyatlari bilan) yozing.
      - Shu so'z qatnashgan bitta chiroyli va tushunarli MISOL GAP (ustozlar darajasida) tuzing va uning o'zbekcha tarjimasini bering.
      - Ortqicha gap yozmang, qisqa va lo'nda bo'ling.

   B. Agar foydalanuvchi GRAMMATIK SAVOL so'rasa (Masalan: "Akkusativ nima", "Present Simple haqida tushuntir"):
      - Grammatik qoidani o'ta professional, sodda va to'liq tushuntirib bering.
      - Tushuntirish tugagach, gapni qat'iy ravishda mana shu gap bilan yakunlang:
        "Ushbu grammatik qoida bo'yicha mana shu o'zbekcha gapni tarjima qiling, men tekshirib beraman: [SHU YERGA MAVZUGA OID BITTA O'ZBEKCHA GAPNI YOZING]"

2. ANIQ VA TABIIY FANLAR BO'LIMI (Matematika, Fizika, Kimyo, Biologiya, Adabiyot, Ona tili):
Foydalanuvchi fan yuzasidan savol yoki mavzu yuborganida:
   - Hech qachon yakuniy javobni, tayyor yechimni yoki variantni aytmang.
   - Mavzuning mohiyatini, formulasini yoki teoriyasini professional tarzda tushuntiring.
   - Mavzuga doir to'liq yechilgan BITTA MISOL (namuna) ko'rsating.
   - Foydalanuvchi o'zi mustaqil fikrlashi uchun BITTA SAVOL yoki MASALA bering va undan javobni kuting.

======================================
UMUMIY USLUBIY QOIDALAR:
======================================
- Foydalanuvchiga doim hurmat bilan "Siz" deb murojaat qiling.
- Haqiqiy jonli ustoz muhitini yarating, lekin emojilarni juda kam va faqat kerakli o'rinlarda ishlating.
- Agar foydalanuvchi rasm yuborsa ham, ushbu qoidalar doirasida rasm ichidagi savolni tushuntirib, yo'l ko'rsating, lekin yakuniy javobni yozmang.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

# ====================================
# WEB SERVER
# ====================================
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "LangGo Academy ishlayapti 🚀"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
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
            reply_markup=ReplyKeyboardMarkup(languages_menu, resize_keyboard=True)
        )
        return

    if text == "🔢 Aniq fanlar":
        await update.message.reply_text(
            "📚 Fanni tanlang:",
            reply_markup=ReplyKeyboardMarkup(science_menu, resize_keyboard=True)
        )
        return

    if text == "⬅️ Orqaga":
        await update.message.reply_text(
            "🏠 Asosiy menyu:",
            reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
        )
        return

    # =========================
    # SUBJECT SAVE
    # =========================
    subjects = ["Nemis", "Ingliz", "Rus", "Turk", "Matematika", "Fizika", "Kimyo", "Biologiya", "Adabiyot", "Ona tili"]

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
    subject = context.user_data.get("subject", "Umumiy")

    # =========================
    # AI PROMPT
    # =========================
    prompt = f"""
Tanlangan fan/yo'nalish: {subject}
Foydalanuvchi yuborgan matn yoki savol: {text}

Eslatma: 'SYSTEM_INSTRUCTION' ichidagi o'z bo'limingizga tegishli qoidalarga (bitta so'zga tarjima + bitta misol gap; grammatikaga to'liq izoh + bitta o'zbekcha gap topshiriq; fanlarga tushuntirish + bitta misol + bitta savol) qat'iy amal qiling!
"""

    try:
        # Eski to_thread o'rniga xavfsiz va toza asinxron metoddan foydalanamiz
        response = await model.generate_content_async(prompt)
        ai_text = getattr(response, "text", None)

        if not ai_text:
            ai_text = "⚠️ AI javob qaytarmadi.\nKeyinroq qayta urinib ko‘ring."

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
    # Web serverni asinxron xavfsiz oqimda daemon rejimda yoqamiz
    t = Thread(target=run_web, daemon=True)
    t.start()

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 LangGo Academy ishga tushdi")
    app.run_polling()

# ====================================
# START
# ====================================
if __name__ == "__main__":
    main()
