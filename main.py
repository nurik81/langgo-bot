import os
import asyncio
from google import genai
from telegram import Update, ReplyKeyboardMarkup
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
GEMINI_KEY = "AIzaSyDJotEGXkw0WDe19pf5limMkp35o9Qpt8s"

# ====================================
# YANGI GOOGLE GENAI CLIENT
# ====================================
client = genai.Client(api_key=GEMINI_KEY)

SYSTEM_INSTRUCTION = """
Siz 'LangGo AI' virtual akademiyasining professional ustozisiz.

ASOSIY QOIDALAR:
1. Siz hech qachon tayyor javob bermaysiz.
2. Foydalanuvchini o‘ylashga majbur qilasiz.
3. Agar foydalanuvchi: test, variant, homework, speaking, writing, esse, insho, imtihon savoli yuborsa:
❌ tayyor javobni aytmang, variantni aytmang, final answer yozmang
✅ mavzuni tushuntiring, qadamlarni ko‘rsating, qanday o‘ylashni o‘rgating, grammar explain qiling, useful phrases bering, hint bering, misollar bilan tushuntiring
4. Matematika va fizikada: formulani yozing, formula nimani anglatishini tushuntiring, ishlash usulini ko‘rsating, qaysi formula ishlatilishini ayting, lekin oxirgi javobni chiqarmang
5. Kimyo va biologiyada: reaction, process, terminology, formula, theory tushuntiring.
6. Tillar: Siz o‘zbek, ingliz, nemis, rus, turk tillarini tushunasiz.
7. Agar foydalanuvchi rasm tashlasa: savolni analiz qiling, tushuntiring, lekin javobni aytmang
8. Foydalanuvgaga doim "Siz" deb murojaat qiling.
9. Professional va ustozlardek gapiring.
10. Emojilar juda kam ishlatilsin.
"""

# ====================================
# MENULAR
# ====================================
main_menu = [['🌍 Jahon tillari', '🔢 Aniq fanlar']]
languages_menu = [['🇩🇪 Nemis tili', '🇬🇧 Ingliz tili'], ['🇷🇺 Rus tili', '🇹🇷 Turk tili'], ['⬅️ Orqaga']]
science_menu = [['🧮 Matematika', '🔭 Fizika'], ['🧪 Kimyo', '🧬 Biologiya'], ['📚 Adabiyot', '📝 Ona tili'], ['⬅️ Orqaga']]

USER_SUBJECTS = {}

# Matndagi harflarni standartlashtirish funksiyasi (ogil -> o'g'il, nemis tili -> nemis)
def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    # Kiritilishi mumkin bo'lgan har xil harf xatoliklarini to'g'rilash
    replacements = {
        "o‘": "o'", "o‘": "o'", "o’": "o'", "o`": "o'", "g‘": "g'", "g`": "g'", "g’": "g'",
        "o’": "o'", "ö": "o", "ü": "u", "sh": "sh", "ch": "ch", "ng": "ng",
        "o": "o", "g": "g" # o' va g' harflari oddiy o va g deb yozilganda ham tushunishi uchun
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

# ====================================
# START COMMAND
# ====================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎓 LangGo AI akademiyasiga xush kelibsiz.\n\nKerakli bo‘limni tanlang:",
        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    )

# ====================================
# HANDLE MESSAGE
# ====================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    # Matnni tozalash va kichik harflarga o'tkazish
    clean_text = normalize_text(text)

    if "jahon tillari" in clean_text or "tilni tanlang" in clean_text:
        await update.message.reply_text("🌍 Tilni tanlang:", reply_markup=ReplyKeyboardMarkup(languages_menu, resize_keyboard=True))
        return

    if "aniq fanlar" in clean_text or "fanni tanlang" in clean_text:
        await update.message.reply_text("📚 Fanni tanlang:", reply_markup=ReplyKeyboardMarkup(science_menu, resize_keyboard=True))
        return

    if "orqaga" in clean_text or "asosiy menyu" in clean_text:
        await update.message.reply_text("🏠 Asosiy menyu:", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
        return

    # Fanlar lug'ati (Foydalanuvchi har xil yozsa ham qaysi fanga tegishliligini topadi)
    subject_map = {
        "nemis": "Nemis tili",
        "german": "Nemis tili",
        "ingliz": "Ingliz tili",
        "english": "Ingliz tili",
        "rus": "Rus tili",
        "russian": "Rus tili",
        "turk": "Turk tili",
        "turkish": "Turk tili",
        "matem": "Matematika",
        "math": "Matematika",
        "fizika": "Fizika",
        "physics": "Fizika",
        "kimyo": "Kimyo",
        "ximiya": "Kimyo",
        "biologiya": "Biologiya",
        "bio": "Biologiya",
        "adabiyot": "Adabiyot",
        "ona tili": "Ona tili",
        "onatili": "Ona tili"
    }

    # Foydalanuvchi tugmani bosganda yoki fan nomini xato yozganda ham tekshirish
    matched_subject = None
    for key, full_name in subject_map.items():
        if key in clean_text:
            matched_subject = full_name
            break

    if matched_subject:
        USER_SUBJECTS[user_id] = matched_subject
        await update.message.reply_text(
            f"✅ {matched_subject} bo‘limi tanlandi.\n\n"
            f"📩 {matched_subject} bo'yicha savolingizni yuboring."
        )
        return

    # Savol yuborilganda fanni aniqlash
    subject = USER_SUBJECTS.get(user_id, "Umumiy tushunchalar")

    try:
        # Prompt yaratishda AI ga foydalanuvchi xato yozgan bo'lishi mumkinligini eslatamiz
        prompt = f"""
Fan: {subject}
Foydalanuvchi savoli: {text}

ESLATMA: Foydalanuvchi so'zlarida imlo xatolari (masalan: o' o'rniga o, g' o'rniga g yoki x o'rniga h) qilgan bo'lishi mumkin. Savol mazmunini tushunib, to'g'ri yo'nalish bering.

MUHIM:
- Tayyor javobni bermang
- Variantni aytmang
- Final answer yozmang
- O‘quvchini o‘ylashga majbur qiling
- Ustozdek tushuntiring
- Step-by-step yo‘l ko‘rsating
"""
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"system_instruction": SYSTEM_INSTRUCTION}
            )
        )

        ai_text = getattr(response, "text", None)
        if not ai_text:
            ai_text = "⚠️ AI hozircha javob qaytara olmadi."

        await update.message.reply_text(ai_text)

    except Exception as e:
        print("ERROR:", e)
        await update.message.reply_text("⚠️ Texnik xatolik yuz berdi. API kalit ruxsatlarini tekshiring.")

# ====================================
# MAIN
# ====================================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 LangGo AI imlo xatolarini tushunadigan versiyada ishga tushdi")

    PORT = int(os.environ.get("PORT", 10000))
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

    if RENDER_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{RENDER_URL}/{BOT_TOKEN}"
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    main()
