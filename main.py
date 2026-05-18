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

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# ====================================
# TOKENLAR (Render tizimidan o'qiladi)
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
Foydalanuvchi fan yuzasidan savol yoki maven yuborganida:
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
    context.user_data.clear()

    await update.message.reply_text(
        welcome_text,
        reply_markup=ReplyKeyboardMarkup(
            main_menu,
            resize_keyboard=True
        )
    )

# ====================================
# HANDLE MESSAGE & PHOTO
# ====================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ""
    is_photo = False
    photo_bytes = None

    if update.message.photo:
        is_photo = True
        text = update.message.caption.strip() if update.message.caption else ""
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
    
    elif update.message.text:
        text = update.message.text.strip()

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

        subjects = ["Nemis", "Ingliz", "Rus", "Turk", "Matematika", "Fizika", "Kimyo", "Biologiya", "Adabiyot", "Ona tili"]
        is_subject_button = any(s.lower() in text.lower() for s in subjects) and (
            "tili" in text.lower() or any(text == btn for row in science_menu for btn in row)
        )

        if is_subject_button:
            context.user_data["subject"] = text
            context.user_data["history"] = []
            await update.message.reply_text(
                f"✅ {text} bo‘limi tanlandi.\n\n"
                "📩 Endi savolingizni matn yoki rasm ko‘rinishida yuboring."
            )
            return

    subject = context.user_data.get("subject")
    if not subject:
        await update.message.reply_text("⚠️ Iltimos, avval menyudan biror bir til yoki fanni tanlang!")
        return

    if is_photo and not text:
        text = "Ushbu rasm ichidagi topshiriq yoki savolni tushuntirib bering."

    if "history" not in context.user_data:
        context.user_data["history"] = []
    
    chat_history = context.user_data["history"]

    try:
        if not GEMINI_KEY:
            await update.message.reply_text("⚠️ API kalit (GEMINI_API_KEY) serverga kiritilmagan!")
            return

        url = "https://googleapis.com"
        headers = {"Content-Type": "application/json"}
        
        contents_payload = []
        
        for hist in chat_history:
            contents_payload.append({
                "role": hist["role"],
                "parts": [{"text": hist["text"]}]
            })
            
        current_parts = []
        if is_photo and photo_bytes:
            base64_image = base64.b64encode(photo_bytes).decode('utf-8')
            current_parts.append({
                "inlineData": {
                    "mimeType": "image/jpeg",
                    "data": base64_image
                }
            })
        
        prompt_text = f"Tanlangan fan/yo'nalish: {subject}\nFoydalanuvchi murojaati: {text}"
        current_parts.append({"text": prompt_text})
        
        contents_payload.append({
            "role": "user",
            "parts": current_parts
        })
        
        payload = {
            "contents": contents_payload,
            "systemInstruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}]
            }
        }
        
        params = {"key": GEMINI_KEY}
        
        response = await asyncio.to_thread(requests.post, url, json=payload, headers=headers, params=params, timeout=30)
        res_data = response.json()

        if response.status_code == 200:
            if "candidates" in res_data and len(res_data["candidates"]) > 0:
                content_obj = res_data["candidates"][0].get("content", {})
                parts = content_obj.get("parts", [])
                
                # PARSLASH TO'LIQ TUZATILDI: Ro'yxat elementidan kalit xavfsiz olindi
                if parts and len(parts) > 0:
                    ai_text = parts[0].get("text", "")
                    if ai_text:
                        chat_history.append({"role": "user", "text": f"Savol: {text}"})
                        chat_history.append({"role": "model", "text": ai_text})
                        
                        if len(chat_history) > 12:
                            context.user_data["history"] = chat_history[-12:]
                        
                        await update.message.reply_text(ai_text)
                        return
            
            await update.message.reply_text("⚠️ AI tuzilmasidan noto'g'ri javob keldi.")
        else:
            err_msg = res_data.get("error", {}).get("message", "Noma'lum xatolik")
            await update.message.reply_text(f"⚠️ Google API xatoligi: {err_msg}")

    except Exception as e:
        print(f"API ERROR: {e}")
        await update.message.reply_text("⚠️ Texnik xatolik yuz berdi.")

# ====================================
# VEB SERVERNI ALOHIDA OQIMDA ISHGA TUSHIRISH
# ====================================
def start_flask():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ====================================
# MAIN
# ====================================
def main():
    if not BOT_TOKEN:
        print("🔴 Xatolik: TELEGRAM_BOT_TOKEN topilmadi!")
        return

    flask_thread = Thread(target=start_flask, daemon=True)
    flask_thread.start()

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_message))

    print("🚀 LangGo Academy Telegram Bot ishga tushdi")
    app.run_polling()

if __name__ == "__main__":
    main()
