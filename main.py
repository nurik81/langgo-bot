import os
from flask import Flask
import threading
import pandas as pd
from datetime import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# Flaskni alohida oqimda ishga tushirish
threading.Thread(target=run, daemon=True).start()

# Mana shu yerdan keyin TOKEN qismi boshlanadi
TOKEN = os.getenv("BOT_TOKEN")
# =====================
TOKEN = os.getenv("BOT_TOKEN")

# =====================
# 🇩🇪 100 WORDS
# =====================
de_data = [
["kitob","Buch","das","Bücher"],["stol","Tisch","der","Tische"],
["stul","Stuhl","der","Stühle"],["uy","Haus","das","Häuser"],
["maktab","Schule","die","Schulen"],["o‘qituvchi","Lehrer","der","Lehrer"],
["o‘quvchi","Schüler","der","Schüler"],["mashina","Auto","das","Autos"],
["telefon","Telefon","das","Telefone"],["kompyuter","Computer","der","Computer"],
["non","Brot","das","Brote"],["suv","Wasser","das","-"],
["choy","Tee","der","-"],["sut","Milch","die","-"],
["shahar","Stadt","die","Städte"],["qishloq","Dorf","das","Dörfer"],
["yo‘l","Straße","die","Straßen"],["daryo","Fluss","der","Flüsse"],
["tog‘","Berg","der","Berge"],["dengiz","Meer","das","Meere"],
["quyosh","Sonne","die","-"],["oy","Mond","der","-"],
["yulduz","Stern","der","Sterne"],["pul","Geld","das","-"],
["vaqt","Zeit","die","-"],["ish","Arbeit","die","-"],
["ovqat","Essen","das","-"],["til","Sprache","die","Sprachen"],
["do‘st","Freund","der","Freunde"],["ota","Vater","der","Väter"],
["ona","Mutter","die","Mütter"],["bola","Kind","das","Kinder"],
["erkak","Mann","der","Männer"],["ayol","Frau","die","Frauen"],
["kalit","Schlüssel","der","Schlüssel"],["sumka","Tasche","die","Taschen"],
["ko‘cha","Straße","die","Straßen"],["park","Park","der","Parks"],
["samolyot","Flugzeug","das","Flugzeuge"],["poezd","Zug","der","Züge"],
["avtobus","Bus","der","Busse"],["velosiped","Fahrrad","das","Fahrräder"],
["kitob javoni","Bücherregal","das","Bücherregale"],["kasalxona","Krankenhaus","das","Krankenhäuser"],
["rang","Farbe","die","Farben"],["qizil","rot","-","-"],
["yashil","grün","-","-"],["ko‘k","blau","-","-"],
["oq","weiß","-","-"],["qora","schwarz","-","-"],
["katta","groß","-","-"],["kichik","klein","-","-"],
["tez","schnell","-","-"],["sekin","langsam","-","-"],
["yangi","neu","-","-"],["eski","alt","-","-"],
["chiroyli","schön","-","-"],["baxtli","glücklich","-","-"],
["charchagan","müde","-","-"],["och","hungrig","-","-"],
["chanqagan","durstig","-","-"],["musiqa","Musik","die","-"],
["film","Film","der","Filme"],["o‘yin","Spiel","das","Spiele"],
["internet","Internet","das","-"],["dars","Unterricht","der","-"],
["sinov","Test","der","Tests"],["natija","Ergebnis","das","Ergebnisse"],
["maqsad","Ziel","das","Ziele"],["orzu","Traum","der","Träume"]
]

# =====================
# 🇬🇧 100 WORDS
# =====================
en_data = [
["kitob","book"],["stol","table"],["stul","chair"],["uy","house"],
["maktab","school"],["o‘qituvchi","teacher"],["o‘quvchi","student"],
["mashina","car"],["telefon","phone"],["kompyuter","computer"],
["non","bread"],["suv","water"],["choy","tea"],["sut","milk"],
["shahar","city"],["qishloq","village"],["yo‘l","road"],
["daryo","river"],["tog‘","mountain"],["dengiz","sea"],
["quyosh","sun"],["oy","moon"],["yulduz","star"],
["pul","money"],["vaqt","time"],["ish","work"],
["ovqat","food"],["til","language"],["do‘st","friend"],
["ota","father"],["ona","mother"],["bola","child"],
["erkak","man"],["ayol","woman"],["kalit","key"],
["sumka","bag"],["ko‘cha","street"],["park","park"],
["samolyot","plane"],["poezd","train"],["avtobus","bus"],
["velosiped","bicycle"],["kasalxona","hospital"],["rang","color"],
["qizil","red"],["yashil","green"],["ko‘k","blue"],
["oq","white"],["qora","black"],["katta","big"],
["kichik","small"],["tez","fast"],["sekin","slow"],
["yangi","new"],["eski","old"],["chiroyli","beautiful"],
["baxtli","happy"],["charchagan","tired"],["och","hungry"],
["chanqagan","thirsty"],["musiqa","music"],["film","movie"],
["o‘yin","game"],["internet","internet"],["dars","lesson"],
["sinov","test"],["natija","result"],["maqsad","goal"],
["orzu","dream"],["yoz","summer"],["qish","winter"],
["bahor","spring"],["kuz","autumn"]
]

de_df = pd.DataFrame(de_data, columns=["uz","ger","article","plural"])
en_df = pd.DataFrame(en_data, columns=["uz","en"])

# =====================
# MEMORY
# =====================
user_lang = {}
stats = {}

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.chat_id
    stats.setdefault(uid, {"de":0,"en":0})

    keyboard = [["🇩🇪 Nemis tili","🇬🇧 English"]]

    await update.message.reply_text(
        "👋 LangGo Bot\n\n📚 Til tanlang 🙂",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# =====================
# REPORT 22:00
# =====================
async def send_report(context):
    for uid, d in stats.items():

        total = d["de"] + d["en"]

        msg = (
            f"🌙 Kunlik hisobot\n\n"
            f"🇩🇪 {d['de']} | 🇬🇧 {d['en']}\n"
        )

        if total < 5:
            msg += (
                "💪 Bugun kam ishladingiz.\n"
                "📚 Ko‘proq mashq qiling!"
            )
        else:
            msg += (
                "🌟 AJOYIB!\n🔥 Juda yaxshi natija!"
            )

        try:
            await context.bot.send_message(uid, msg)
        except:
            pass

        stats[uid] = {"de":0,"en":0}

# =====================
# HANDLE
# =====================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.message.chat_id
    text = update.message.text.lower().strip()

    stats.setdefault(uid, {"de":0,"en":0})

    if "nemis" in text:
        user_lang[uid] = "de"
        await update.message.reply_text("🇩🇪 OK")
        return

    if "english" in text:
        user_lang[uid] = "en"
        await update.message.reply_text("🇬🇧 OK")
        return

    lang = user_lang.get(uid)
    if not lang:
        return await update.message.reply_text("Til tanla 🙂")

    if lang == "de":
        r = de_df[(de_df["uz"]==text)|(de_df["ger"].str.lower()==text)]
        if not r.empty:
            r=r.iloc[0]
            stats[uid]["de"]+=1
            return await update.message.reply_text(f"{r['ger']} | {r['article']} | {r['plural']} | {r['uz']}")

    else:
        r = en_df[(en_df["uz"]==text)|(en_df["en"]==text)]
        if not r.empty:
            r=r.iloc[0]
            stats[uid]["en"]+=1
            return await update.message.reply_text(f"{r['en']} | {r['uz']}")

# =====================
# RUN
# =====================
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.job_queue.run_daily(send_report, time=time(hour=17, minute=0))

    print("BOT READY 24/7 🚀")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
