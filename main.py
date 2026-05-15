import os
import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# 1. SOZLAMALAR ⚙️
BOT_TOKEN = "8649876958:AAG91R5UH5V_ILVQ2jc8VJ4clm54w269oh0"
GEMINI_KEY = "AIzaSyCHSSgiZZYVeUTFmLBGxmOEN8_GNhiqh38"

genai.configure(api_key=GEMINI_KEY)

# AI uchun o'ta muloyim va quvnoq yo'riqnoma 🌟
SYSTEM_INSTRUCTION = """
Sen 'LangGo AI' virtual akademiyasining eng mehribon va aqlli o'qituvchisisan! 🤗👨‍🏫👩‍🏫
Sening xaraktering:
1. HAR DOIM MULOYIM BO'L: Foydalanuvchiga 'Azizim', 'Qadrdonim', 'Bilimdonim' deb murojaat qil. ✨
2. EMOJILAR: Har bir gapda kamida 2-3 ta emoji ishlat! (🌟, ✅, 📚, 💪, 😊, 🚀, 🎓)
3. REPETITOR USLUBI (CHAYNAB BERISH): Javobni srazu aytma! 🛑 Oldin mavzuni tushuntir, foydalanuvchini maqta! 💪🔥
4. XATOLARNI TUSHUNISH: Foydalanuvchi xato yozsa ham gap nima haqidaligini tushunib javob ber. 😊
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

# 2. TUGMALAR (HAMMA MENYULAR) ⌨️
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

# 3. START 🚀
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum, bilimga chanqoq qadrdonim! ✨👋\n\n"
        "LangGo AI akademiyasiga xush kelibsiz! Siz bilan uchrashganimdan juda xursandman! 🤗🎓\n"
        "Bugun qaysi fanni birgalikda zabt etamiz? 👇",
        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    )

# 4. XABARLARNI QAYTA ISHLASH 💬
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data

    # Menyu mantiqi 🧭
    if text == "🌍 Jahon tillari":
        await update.message.reply_text("Vau, tillarni o'rganish juda ajoyib! ✨ Qaysi tilni tanlaymiz, bilimdonim? 😊", 
                                       reply_markup=ReplyKeyboardMarkup(languages_menu, resize_keyboard=True))
        return
    elif text == "🔢 Aniq fanlar":
        await update.message.reply_text("Aniq fanlar dunyosiga xush kelibsiz! 🔍 Qaysi yo'nalishda savollaringiz bor? 📚", 
                                       reply_markup=ReplyKeyboardMarkup(science_menu, resize_keyboard=True))
        return
    elif text == "⬅️ Orqaga":
        await update.message.reply_text("Asosiy menyuga qaytdik, qadrdonim! 🏠✨", 
                                       reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
        return

    # Fan tanlanganda saqlab qolish 🎓
    subjects = ["tili", "Matematika", "Fizika", "Biologiya", "Adabiyot", "Ona tili"]
    if any(s in text for s in subjects):
        user_data['subject'] = text
        await update.message.reply_text(
            f"Tanlandi: {text}! ✅\n\n"
            f"Endi bemalol menga savolingizni yo'llang, qadrdonim! Men sizga yordam berishga shayman! 💪🌟"
        )
        return

    # AI javobi 🤖
    subject = user_data.get('subject', 'Umumiy bilimlar')
    try:
        response = model.generate_content(f"Mavzu: {subject}. Foydalanuvchi so'rovi: {text}")
        await update.message.reply_text(response.text)
    except Exception:
        await update.message.reply_text("Voy, kichik bir xatolik bo'ldi! 🙈 Qayta yozing, bilimdonim! ✨")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Quvnoq va aqlli bot ishga tushdi... 🚀✨")
    app.run_polling()
