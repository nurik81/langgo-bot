import os
import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# 1. SOZLAMALAR (TOKEN va API KEY qo'yildi) ⚙️
BOT_TOKEN = "8649876958:AAG91R5UH5V_ILVQ2jc8VJ4clm54w269oh0"
GEMINI_KEY = "AIzaSyCHSSgiZZYVeUTFmLBGxmOEN8_GNhiqh38"

genai.configure(api_key=GEMINI_KEY)

# AI uchun vazmin va repetitorlik yo'riqnomasi 🏛️
SYSTEM_INSTRUCTION = """
Sen 'LangGo AI' akademiyasining tajribali va jiddiy o'qituvchisisan. 
Sening asosiy qoidalaring:
1. JAVOB BERMA: Foydalanuvchi savol yoki topshiriq yuborsa, tayyor JAVOBNI AYTMA. 🛑 
2. YO'NALISH BER: Foydalanuvchiga mavzuni tushuntir, qaysi qoidani eslash kerakligini ayt va uni o'zini yechim topishga unda.
3. HURMAT VA JIDDIY OHANG: Foydalanuvchiga 'Siz' deb murojaat qil. Professional va vazmin bo'l. Ortiqcha "azizim", "bilimdonim" kabi so'zlarni aslo ishlatma. 
4. EMOJILAR: Faqat zarur bo'lganda, matnni tartibga solish uchun juda kam ishlatilsin.
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

# 3. START BUYRUG'I 🚀
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum. LangGo AI akademiyasi tizimiga xush kelibsiz. 🎓\n"
        "Yo'nalishni tanlang: 👇",
        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    )

# 4. XABARLARNI QAYTA ISHLASH 💬
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data

    # Menyu mantiqi 🧭
    if text == "🌍 Jahon tillari":
        await update.message.reply_text("Kerakli tilni tanlang:", 
                                       reply_markup=ReplyKeyboardMarkup(languages_menu, resize_keyboard=True))
        return
    elif text == "🔢 Aniq fanlar":
        await update.message.reply_text("Fan yo'nalishini tanlang:", 
                                       reply_markup=ReplyKeyboardMarkup(science_menu, resize_keyboard=True))
        return
    elif text == "⬅️ Orqaga":
        await update.message.reply_text("Asosiy menyu.", 
                                       reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
        return

    # Fan tanlanganda saqlab qolish 🎓
    subjects = ["tili", "Matematika", "Fizika", "Biologiya", "Adabiyot", "Ona tili"]
    if any(s in text for s in subjects):
        user_data['subject'] = text
        await update.message.reply_text(f"{text} bo'limi faollashdi. Savolingizni yo'llashingiz mumkin. ✅")
        return

    # AI repetitorlik jarayoni 🤖
    subject = user_data.get('subject', 'Umumiy')
    try:
        # AI ga topshiriq berish
        prompt = f"Mavzu: {subject}. Foydalanuvchi so'rovi: {text}. (Eslatma: Tayyor javobni berish taqiqlanadi, faqat yo'nalish bering!)"
        response = model.generate_content(prompt)
        await update.message.reply_text(response.text)
    except Exception:
        await update.message.reply_text("Texnik xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring. ⚠️")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    app.run_polling()
