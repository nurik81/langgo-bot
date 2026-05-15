import os
import logging
import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# 1. SOZLAMALAR (Kalitlar kiritildi ✅)
BOT_TOKEN = "8649876958:AAG91R5UH5V_ILVQ2jc8VJ4clm54w269oh0"
GEMINI_KEY = "AIzaSyCHSSgiZZYVeUTFmLBGxmOEN8_GNhiqh38"

genai.configure(api_key=GEMINI_KEY)

# AI uchun o'qituvchi yo'riqnomasi 🧠
SYSTEM_INSTRUCTION = """
Sen 'LangGo AI' virtual akademiyasining professional va juda aqlli o'qituvchisisan. 👨‍🏫👩‍🏫
Sening vazifalaring:
1. HAR QANDAY SAVOL: Foydalanuvchi tanlagan fan (Matem, Fizika, Ona tili va hk) yoki til (Nemis, Rus, Arab, Ingliz, Turk, Xitoy, Koreys) bo'yicha har qanday savolga mukammal javob berasan.
2. REPETITOR USLUBI: Agar foydalanuvchi test yoki masala tashlasa, JAVOBNI TAYYOR AYTMA! 🛑 Uni tushuntir, yo'nalish ber. 'O'zingiz harakat qiling' deb dalda ber.
3. XATOLARNI TUSHUNISH: Foydalanuvchi harflarni noto'g'ri yozsa ham gap nima haqidaligini tushun. 😊
4. SPRECHEN & SCHREIBEN: Tillarda imtihon vazifalari (masalan, xat yozish yoki suhbat) bo'lsa, kreativ ideyalar ber. 💡
5. OHANG: Juda muloyim bo'l va ko'p emojilar ishlat! ✨
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

# 2. TUGMALAR (MENYU) ⌨️
main_menu = [['🌍 Jahon tillari', '🔢 Aniq fanlar']]
languages_menu = [
    ['🇩🇪 Nemis tili', '🇬🇧 Ingliz tili', '🇷🇺 Rus tili'], 
    ['🇨🇳 Xitoy tili', '🇰🇷 Koreys tili', '🇸🇦 Arab tili'], 
    ['🇹🇷 Turk tili', '⬅️ Orqaga']
]
science_menu = [
    ['📝 Ona tili', '🧮 Matematika', '🔭 Fizika'], 
    ['🧬 Biologiya', '📚 Adabiyot'], 
    ['⬅️ Orqaga']
]

# 3. START BUYRUG'I 🚀
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! LangGo AI akademiyasiga xush kelibsiz! ✨\n\n"
        "Men sizga barcha tillarni va fanlarni o'rganishda yordam beraman. 🎓\n"
        "Qaysi yo'nalishni tanlaymiz? 👇",
        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    )

# 4. XABARLARNI QAYTA ISHLASH 💬
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data

    # Menyu mantiqi 🧭
    if text == "🌍 Jahon tillari":
        await update.message.reply_text("Tilni tanlang! Men sizga grammatika va har qanday savolda yordam beraman! 😊", 
                                       reply_markup=ReplyKeyboardMarkup(languages_menu, resize_keyboard=True))
        return
    elif text == "🔢 Aniq fanlar":
        await update.message.reply_text("Qaysi fanni tahlil qilamiz? 🔍", 
                                       reply_markup=ReplyKeyboardMarkup(science_menu, resize_keyboard=True))
        return
    elif text == "⬅️ Orqaga":
        await update.message.reply_text("Asosiy menyu: 🏠", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
        return

    # Fan yoki Til tanlanganda 🎓
    subjects = ["tili", "Matematika", "Fizika", "Biologiya", "Adabiyot"]
    if any(s in text for s in subjects):
        user_data['subject'] = text
        await update.message.reply_text(
            f"Tanlandi: {text}! ✅\n\n"
            "Endi bemalol menga qanday savolingiz bo'lsa yo'llang. Men tayyorman! 💪"
        )
        return

    # AI bilan muloqot ✨
    subject = user_data.get('subject', 'Umumiy bilimlar')
    prompt = f"Mavzu: {subject}. Foydalanuvchi so'rovi: {text}"
    
    try:
        response = model.generate_content(prompt)
        await update.message.reply_text(response.text)
    except Exception:
        await update.message.reply_text("Kechirasiz, tizimda ozgina uzilish bo'ldi. ✨ Qayta urinib ko'ring.")

# 5. ISHGA TUSHIRISH
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Bot muvaffaqiyatli ishga tushdi... 🚀")
    app.run_polling()
