import os
import asyncio
import requests  # To'g'ridan-to'g'ri Google API bilan bog'lanish uchun

from flask import Flask

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
# TOKENLAR (Render tizimidan xavfsiz o'qiladi)
# ====================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

SYSTEM_INSTRUCTION = """
Siz 'LangGo Academy' platformasining professional, bilimdon va strategik virtual ustozisiz.
Sizning maqsadianiz foydalanuvchiga tayyor javobni berish emas, balki uni fikrlashga majbur qilish va yo'naltirishdir.

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

# ====================================
# WEB SERVER
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

    # Navigatsiya menyulari
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

    # Fan yoki til tanlanganini aniqlash
    subjects = ["Nemis", "Ingliz", "Rus", "Turk", "Matematika", "Fizika", "Kimyo", "Biologiya", "Adabiyot", "Ona tili"]
    
    is_subject_button = any(s.lower() in text.lower() for s in subjects) and (
        "tili" in text.lower() or any(text == btn for row in science_menu for btn in row)
    )

    if is_subject_button:
        context.user_data["subject"] = text
        await update.message.reply_text(
            f"✅ {text} bo‘limi tanlandi.\n\n"
            "📩 Endi savolingizni yuboring."
        )
        return

    # Foydalanuvchi savol yuborganda tekshirish
    subject = context.user_data.get("subject")
    if not subject:
        await update.message.reply_text("⚠️ Iltimos, avval menyudan biror bir til yoki fanni tanlang!")
        return

    prompt = f"""
Tanlangan fan/yo'nalish: {subject}
Foydalanuvchi yuborgan matn yoki savol: {text}

Eslatma: 'SYSTEM_INSTRUCTION' ichidagi o'z bo'limingizga tegishli qoidalarga qat'iy amal qiling!
"""

    try:
        if not GEMINI_KEY:
            await update.message.reply_text("⚠️ API kalit (GEMINI_API_KEY) serverga kiritilmagan!")
            return

        # Chet el serverlaridagi mintaqa taqiqlarini aylanib o'tuvchi xavfsiz HTTP API
        url = f"https://googleapis.com{GEMINI_KEY}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]}
        }
        
        # Server qotib qolmasligi uchun sinxron so'rovni alohida oqimga joylaymiz
        response = await asyncio.to_thread(requests.post, url, json=payload, timeout=20)
        res_data = response.json()

        # Javobni tekshirish
        if response.status_code == 200 and "candidates" in res_data:
            ai_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            await update.message.reply_text(ai_text)
        else:
            # Muammo bo'lsa Google qaytargan aniq xatolik matnini ko'rsatish
            err_msg = res_data.get("error", {}).get("message", "Noma'lum xatolik")
            await update.message.reply_text(f"⚠️ Google API xatoligi: {err_msg}")

    except Exception as e:
        print(f"API ERROR: {e}")
        await update.message.reply_text(f"⚠️ Texnik xatolik yuz berdi: {str(e)[:50]}")

# ====================================
# VEB SERVERNI ALOHIDA OQIMDA ISHGA TUSHIRISH
# ====================================
def start_flask():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ====================================
# MAIN (BOTNI YOQISH)
# ====================================
def main():
    if not BOT_TOKEN:
        print("🔴 Xatolik: TELEGRAM_BOT_TOKEN muhit o'zgaruvchisi topilmadi!")
        return

    # Render o'chib qolmasligi uchun Flask veb-serverini alohida oqimda yoqamiz
    flask_thread = Thread(target=start_flask, daemon=True)
    flask_thread.start()
    print("🚀 Flask veb-server orqa fonda ishga tushdi")

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 LangGo Academy Telegram Bot ishga tushdi")
    app.run_polling()

if __name__ == "__main__":
    from threading import Thread
    main()
