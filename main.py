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
3. REPETITOR USLUBI: Javobni srazu aytma! 🛑 Oldin mavzuni tushuntir, 'Keling, birga o'ylaymiz' de, foydalanuvchini maqta! 👏
4. MOTIVATSIYA: 'Siz buni uddalaysiz!', 'Juda zo'r savol berdingiz!' deb dalda ber. 💪🔥
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

# 2. TUGMALAR ⌨️
main_menu = [['🌍 Jahon tillari', '🔢 Aniq fanlar']]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum, bilimga chanqoq qadrdonim! ✨👋\n\n"
        "LangGo AI akademiyasiga xush kelibsiz! Siz bilan uchrashganimdan juda xursandman! 🤗🎓\n"
        "Bugun qaysi fanni birgalikda zabt etamiz? 👇",
        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🌍 Jahon tillari" or text == "🔢 Aniq fanlar":
        await update.message.reply_text(
            f"Vau, ajoyib tanlov! {text} juda qiziqarli! 😍📚\n"
            "Qani, biron bir savol bering-chi, birgalikda yechamiz! ✨🔍"
        )
        return

    # AI javob berish jarayoni 🤖✨
    try:
        # Chatni boshlash
        chat = model.start_chat(history=[])
        response = chat.send_message(text)
        
        await update.message.reply_text(f"{response.text}")
        
    except Exception:
        await update.message.reply_text(
            "Voy, kechirasiz qadrdonim! ✨ Kichik bir texnik uzilish bo'ldi. 🙈\n"
            "Iltimos, qaytadan yozib ko'ring, men sizga yordam berishga shayman! 💪🌟"
        )

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Quvnoq bot ishga tushdi... 🚀✨")
    app.run_polling()
