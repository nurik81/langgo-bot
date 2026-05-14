import os
import asyncio
import pandas as pd
from datetime import time
import pytz

from flask import Flask
from threading import Thread

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =====================
# TOKEN
# =====================

TOKEN = "8649876958:AAFP4e95wQ45DUMySaQmBgCcXXJPTnF2Wmo"

# =====================
# 🇩🇪 GERMAN WORDS
# =====================

de_data = [

["kitob","Buch","das","Bücher"],
["stol","Tisch","der","Tische"],
["stul","Stuhl","der","Stühle"],
["uy","Haus","das","Häuser"],
["maktab","Schule","die","Schulen"],
["o‘qituvchi","Lehrer","der","Lehrer"],
["o‘quvchi","Schüler","der","Schüler"],
["mashina","Auto","das","Autos"],
["telefon","Telefon","das","Telefone"],
["kompyuter","Computer","der","Computer"],
["eshik","Tür","die","Türen"],
["oyna","Fenster","das","Fenster"],
["non","Brot","das","Brote"],
["suv","Wasser","das","-"],
["choy","Tee","der","-"],
["sut","Milch","die","-"],
["shahar","Stadt","die","Städte"],
["qishloq","Dorf","das","Dörfer"],
["yo‘l","Straße","die","Straßen"],
["daryo","Fluss","der","Flüsse"],
["tog‘","Berg","der","Berge"],
["dengiz","Meer","das","Meere"],
["quyosh","Sonne","die","-"],
["oy","Mond","der","-"],
["yulduz","Stern","der","Sterne"],
["odam","Mensch","der","Menschen"],
["ayol","Frau","die","Frauen"],
["erkak","Mann","der","Männer"],
["bola","Kind","das","Kinder"],
["do‘st","Freund","der","Freunde"],
["ota","Vater","der","Väter"],
["ona","Mutter","die","Mütter"],
["aka","Bruder","der","Brüder"],
["opa","Schwester","die","Schwestern"],
["xola","Tante","die","Tanten"],
["tog‘a","Onkel","der","Onkel"],
["jiyan","Neffe","der","Neffen"],
["qiz jiyan","Nichte","die","Nichten"],
["o‘g‘il","Sohn","der","Söhne"],
["qiz","Tochter","die","Töchter"],
["o‘g‘il bola","Junge","der","Jungen"],
["qiz bola","Mädchen","das","Mädchen"],
["amma","Tante","die","Tanten"],
["buvi","Großmutter","die","Großmütter"],
["bobo","Großvater","der","Großväter"],
["o‘qimoq","lernen","-","-"],
["yozmoq","schreiben","-","-"],
["gapirmoq","sprechen","-","-"],
["eshitmoq","hören","-","-"],
["ko‘rmoq","sehen","-","-"],
["yemoq","essen","-","-"],
["ichmoq","trinken","-","-"],
["pul","Geld","das","-"],
["vaqt","Zeit","die","-"],
["ish","Arbeit","die","-"],
["ovqat","Essen","das","-"],
["til","Sprache","die","Sprachen"],
["uyqu","Schlaf","der","-"],
["bozor","Markt","der","Märkte"],
["do‘kon","Laden","der","Läden"],
["park","Park","der","Parks"],
["samolyot","Flugzeug","das","Flugzeuge"],
["poezd","Zug","der","Züge"],
["avtobus","Bus","der","Busse"],
["velosiped","Fahrrad","das","Fahrräder"],
["rang","Farbe","die","Farben"],
["qizil","rot","-","-"],
["yashil","grün","-","-"],
["ko‘k","blau","-","-"],
["oq","weiß","-","-"],
["qora","schwarz","-","-"],
["katta","groß","-","-"],
["kichik","klein","-","-"],
["tez","schnell","-","-"],
["sekin","langsam","-","-"],
["yangi","neu","-","-"],
["eski","alt","-","-"],
["chiroyli","schön","-","-"],
["baxtli","glücklich","-","-"],
["musiqa","Musik","die","-"],
["film","Film","der","Filme"],
["o‘yin","Spiel","das","Spiele"],
["internet","Internet","das","-"],
["dars","Unterricht","der","-"],
["sinov","Test","der","Tests"],
["natija","Ergebnis","das","Ergebnisse"],
["maqsad","Ziel","das","Ziele"],
["orzu","Traum","der","Träume"]

]

while len(de_data) < 200:
    i = len(de_data) + 1
    de_data.append([f"so‘z{i}", f"Wort{i}", "das", "-"])

# =====================
# 🇬🇧 ENGLISH WORDS
# =====================

en_data = [

["kitob","book"],
["stol","table"],
["stul","chair"],
["uy","house"],
["maktab","school"],
["o‘qituvchi","teacher"],
["o‘quvchi","student"],
["mashina","car"],
["telefon","phone"],
["kompyuter","computer"],
["non","bread"],
["suv","water"],
["choy","tea"],
["sut","milk"],
["shahar","city"],
["qishloq","village"],
["yo‘l","road"],
["daryo","river"],
["tog‘","mountain"],
["dengiz","sea"],
["quyosh","sun"],
["oy","moon"],
["yulduz","star"],
["pul","money"],
["vaqt","time"],
["ish","work"],
["ovqat","food"],
["til","language"],
["do‘st","friend"],
["ota","father"],
["ona","mother"],
["aka","brother"],
["opa","sister"],
["xola","aunt"],
["tog‘a","uncle"],
["jiyan","nephew"],
["qiz jiyan","niece"],
["o‘g‘il","son"],
["qiz","daughter"],
["o‘g‘il bola","boy"],
["qiz bola","girl"],
["amma","aunt"],
["buvi","grandmother"],
["bobo","grandfather"],
["o‘qimoq","study"],
["yozmoq","write"],
["gapirmoq","speak"],
["eshitmoq","hear"],
["ko‘rmoq","see"],
["yemoq","eat"],
["ichmoq","drink"],
["erkak","man"],
["ayol","woman"],
["kalit","key"],
["sumka","bag"],
["ko‘cha","street"],
["park","park"],
["samolyot","plane"],
["poezd","train"],
["avtobus","bus"],
["velosiped","bicycle"],
["kasalxona","hospital"],
["rang","color"],
["qizil","red"],
["yashil","green"],
["ko‘k","blue"],
["oq","white"],
["qora","black"],
["katta","big"],
["kichik","small"],
["tez","fast"],
["sekin","slow"],
["yangi","new"],
["eski","old"],
["chiroyli","beautiful"],
["baxtli","happy"],
["musiqa","music"],
["film","movie"],
["o‘yin","game"],
["internet","internet"],
["dars","lesson"],
["sinov","test"],
["natija","result"],
["maqsad","goal"],
["orzu","dream"]

]

while len(en_data) < 200:
    i = len(en_data) + 1
    en_data.append([f"so‘z{i}", f"word{i}"])

# =====================
# DATAFRAME
# =====================

de_df = pd.DataFrame(
    de_data,
    columns=["uz","ger","article","plural"]
)

en_df = pd.DataFrame(
    en_data,
    columns=["uz","en"]
)

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

    stats.setdefault(uid, {"de":0, "en":0})

    keyboard = [
        ["🇩🇪 Nemis tili", "🇬🇧 English"]
    ]

    await update.message.reply_text(
        "👋 Assalomu alaykum!\n\n"
        "🌟 LangGo Botga xush kelibsiz.\n"
        "📚 Nemis va ingliz tilini birga o‘rganamiz.\n\n"
        "🚀 O‘rganmoqchi bo‘lgan tilingizni tanlang 🙂",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

# =====================
# DAILY REPORT
# =====================

async def send_report(context):

    for uid, d in stats.items():

        total = d["de"] + d["en"]

        msg = (
            f"🌙 Kunlik hisobot\n\n"
            f"🇩🇪 Nemischa: {d['de']}\n"
            f"🇬🇧 Inglizcha: {d['en']}\n"
            f"📚 Jami: {total}\n\n"
        )

        if total < 5:

            msg += (
                "💪 Bugun biroz kamroq ishladingiz.\n\n"
                "📚 O‘zingiz ustingizda yana ham ko‘proq ishlang.\n"
                "🚀 Har kuni oz bo‘lsa ham oldinga yurish katta natija beradi 🙂"
            )

        else:

            msg += (
                "🌟 Barakalla!\n\n"
                "🔥 Bugun juda yaxshi ishladingiz.\n"
                "📚 Siz asta-sekin kuchli levelga chiqyapsiz 🚀\n"
                "👏 Shunday davom eting!"
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

        await update.message.reply_text(
            "🇩🇪 Nemis tili tanlandi 🙂\n\n"
            "📚 Nemis tilini o‘rganishda sizga omad tilaymiz!\n"
            "✨ Endi so‘z yuboring."
        )

        return

    if "english" in text:

        user_lang[uid] = "en"

        await update.message.reply_text(
            "🇬🇧 English selected 🙂\n\n"
            "📚 We wish you success in learning English!\n"
            "✨ Send a word."
        )

        return

    lang = user_lang.get(uid)

    if not lang:

        return await update.message.reply_text(
            "🙂 Avval til tanlang."
        )

    # 🇩🇪 GERMAN

    if lang == "de":

        r = de_df[
            (de_df["uz"] == text) |
            (de_df["ger"].str.lower() == text)
        ]

        if not r.empty:

            r = r.iloc[0]

            stats[uid]["de"] += 1

            return await update.message.reply_text(
                f"📘 Nemischa: {r['ger']}\n"
                f"📌 Artikl: {r['article']}\n"
                f"📚 Plural: {r['plural']}\n"
                f"🇺🇿 Tarjimasi: {r['uz']}\n\n"
                f"🌟 Davom eting!"
            )

        return await update.message.reply_text(
            "😔 Kechirasiz, bu so‘z bazada topilmadi."
        )

    # 🇬🇧 ENGLISH

    if lang == "en":

        r = en_df[
            (en_df["uz"] == text) |
            (en_df["en"] == text)
        ]

        if not r.empty:

            r = r.iloc[0]

            stats[uid]["en"] += 1

            return await update.message.reply_text(
                f"📘 English: {r['en']}\n"
                f"🇺🇿 Uzbek: {r['uz']}\n\n"
                f"🌟 Keep going!"
            )

        return await update.message.reply_text(
            "😔 Sorry, this word was not found."
        )

# =====================
# WEB SERVER
# =====================

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "LangGo Bot ishlayapti 🚀"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host='0.0.0.0', port=port)

# =====================
# RUN BOT
# =====================

async def main():

    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle
        )
    )

    uz_tz = pytz.timezone("Asia/Tashkent")

    if application.job_queue:
        application.job_queue.run_daily(
            send_report,
            time=time(hour=22, minute=0, tzinfo=uz_tz)
        )

    print("🚀 Bot ishlayapti...")

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    await asyncio.Event().wait()

# =====================
# START SERVER + BOT
# =====================

if __name__ == "__main__":

    Thread(target=run_web).start()

    asyncio.run(main())
