import os
import json
import base64
import random
import threading
import requests
import time as standard_time  # 'time' nomlari chalkashmasligi uchun standard time modulini alohida nomladik
import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO

import pdfplumber

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ======================================================
# TOKENLAR
# ======================================================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ======================================================
# FOYDALANUVCHILAR (kundalik so'z uchun)
# ======================================================
USERS_FILE = Path("bot/users.json")

def load_users():
    if USERS_FILE.exists():
        data = json.loads(USERS_FILE.read_text())
        if "stats" not in data:
            data["stats"] = {}
        return data
    return {"users": [], "stats": {}}

def save_user(chat_id: int):
    data = load_users()
    if chat_id not in data["users"]:
        data["users"].append(chat_id)
        USERS_FILE.write_text(json.dumps(data))

def load_stats(chat_id: int) -> dict:
    data = load_users()
    return data.get("stats", {}).get(str(chat_id), {"total": 0, "subjects": {}})

def save_stats(chat_id: int, stats: dict):
    data = load_users()
    if "stats" not in data:
        data["stats"] = {}
    data["stats"][str(chat_id)] = stats
    USERS_FILE.write_text(json.dumps(data))

# ======================================================
# DARAJA TIZIMI
# ======================================================
LEVELS = [
    (0,   "🌱 Yangi boshlovchi"),
    (10,  "📗 Boshlang'ich"),
    (30,  "📘 O'rta daraja"),
    (75,  "📙 Ilg'or"),
    (150, "🔥 Professional"),
    (300, "🏆 Ekspert"),
    (500, "💎 Ustoz"),
]

MOTIVATIONS = [
    "Zo'r ketayapsiz! 💪 Har bir savol — yangi bilim!",
    "Ajoyib! Siz har kuni rivojlanayapsiz 🚀",
    "Davom eting! Muvaffaqiyat yaqin 🎯",
    "Bravo! Bilimga chanqoqlik — kuchning belgisi 🌟",
    "Excellent! Siz to'g'ri yo'lda ketayapsiz ✨",
    "Zo'r! Savolingiz juda yaxshi edi 👏",
    "Ustavorlik bu — har kuni bir oz o'rganish 📚",
    "Qoyil! Shu tezlikda tez orada ekspert bo'lasiz 🎓",
]

FUN_FACTS = [
    "💡 Bilasizmi? Ingliz tili dunyoda eng ko'p o'rganilayotgan til — 1.5 milliard kishi!",
    "💡 Bilasizmi? 'OK' so'zi dunyodagi eng ko'p qo'llaniladigan so'z hisoblanadi!",
    "💡 Bilasizmi? Nemis tili 35+ million so'zdan iborat — bu eng katta lug'at!",
    "💡 Bilasizmi? Matematika arabcha 'Al-Jabr' so'zidan kelib chiqqan — algebra ham shundan!",
    "💡 Bilasizmi? Inson miyasi bir soniyada 100,000 kimyoviy reaktsiya bajaradi!",
    "💡 Bilasizmi? Rus tili kosmosda eng ko'p ishlatiladigan til hisoblanadi!",
    "💡 Bilasizmi? Turk tili eng qadimgi tirik tillardan biri — 5500 yildan ko'p!",
    "💡 Bilasizmi? Fizika qonunlari butun koinotda bir xil ishlaydi!",
]

ACHIEVEMENTS = {
    5:   "🎖️ Birinchi qadam! 5 ta savol berdingiz!",
    25:  "🥉 Faol o'quvchi! 25 ta savolga yetdingiz!",
    50:  "🥈 Bilim izlovchi! 50 ta savol — zo'r natija!",
    100: "🥇 100 ta savol! Siz haqiqiy o'quvchisiz!",
    250: "🏆 250 ta savol! Ekspert darajasiga yaqinsiz!",
    500: "💎 500 ta savol! Siz LangGo ning eng yaxshi o'quvchisisiz!",
}

def get_level(total: int) -> str:
    level = LEVELS[0][1]
    for min_q, name in LEVELS:
        if total >= min_q:
            level = name
    return level

def get_next_level(total: int) -> tuple:
    for i, (min_q, name) in enumerate(LEVELS):
        if total < min_q:
            return min_q - total, name
    return 0, "💎 Siz eng yuqori darajasiz!"

# ======================================================
# SYSTEM PROMPT
# ======================================================
SYSTEM_PROMPT = """Siz "LangGo Academy" ning eng yuqori darajali virtual ustozisiz.
20 yillik tajriba, IELTS 9.0, olimpiada murabbiysi, pedagogika doktori.

USLUB:
• Doim "Siz" deb murojaat qiling
• Iliq, professional, rag'batlantiruvchi bo'ling
• Emojilardan erkin foydalaning — ular o'qishni yoqimliroq qiladi

MUHIM FORMAT QOIDASI:
• Hech qachon ** yoki * belgisini ishlatmang (markdown kerak emas)
• Ro'yxatlar uchun • belgisini ishlating
• Bo'lim sarlavhalari uchun emoji + KATTA HARF ishlating
• Masalan: "📌 TARJIMA:", "✅ TO'G'RI MISOLLAR:", "❌ XATO:", "💡 IZOH:"

TIL BO'LIMLARI (Ingliz, Nemis, Rus, Turk):
• Bitta so'z kelsa: faqat tarjima, talaffuz va 1 ta qisqa misol. Ortiqcha yozmang!
• Grammatika so'rovi: qoida + formula + 1 to'g'ri misol. ❌ xato misol YOZMANG!
• Idiom: haqiqiy ma'no + 1 ta misol
• Tarjima so'rovi: tabiiy tarjima + 1 ta muqobil variant
• Foydalanuvchi bir necha so'z/gap yuborganda kengaytirilgan javob bering

ANIQ FANLAR (Matematika, Fizika, Kimyo, Biologiya, Adabiyot, Ona tili):
Hech qachon faqat javob bermang! Har doim:
1️⃣ Nazariya / formula
2️⃣ Bosqichma-bosqich yechim
3️⃣ Javobni tekshirish
4️⃣ O'xshash mashq

SPEAKING/WRITING:
• Writing: 0-75 ball tizimida baholang (pastda ko'rsatilgan)
• Speaking: tabiiy javob namunasi + foydali iboralar + xatolar

UMUMIY: Bo'limlarni emojilar bilan ajrating, aniq va lo'nda yozing, foydalanuvchini rag'batlantiring! 🎯"""

# ======================================================
# MENUS
# ======================================================
main_menu = [
    ["🌍 Jahon tillari", "🔢 Aniq fanlar"],
    ["📝 Writing tekshiruv", "🎯 Quiz / Test"],
    ["🎤 Speaking simulyatsiya", "🗣 Erkin suhbat"],
    ["📊 Statistika", "⚙️ Sozlamalar"]
]

languages_menu = [
    ["🇬🇧 Ingliz tili", "🇩🇪 Nemis tili"],
    ["🇷🇺 Rus tili", "🇹🇷 Turk tili"],
    ["⬅️ Orqaga"]
]

science_menu = [
    ["🧮 Matematika", "🔭 Fizika"],
    ["🧪 Kimyo", "🧬 Biologiya"],
    ["📚 Adabiyot", "📝 Ona tili"],
    ["⬅️ Orqaga"]
]

quiz_subject_menu = [
    ["🇬🇧 Ingliz", "🇩🇪 Nemis"],
    ["🧮 Matematika", "🧪 Kimyo"],
    ["🔭 Fizika", "🧬 Biologiya"],
    ["⬅️ Orqaga"]
]

settings_menu = [
    ["🌐 Bot tili: O'zbek", "🌐 Bot tili: Ingliz"],
    ["📅 Kundalik so'z: Yoqish", "📅 Kundalik so'z: O'chirish"],
    ["⬅️ Orqaga"]
]

# ======================================================
# GROQ AI
# ======================================================
def ask_ai(user_text, subject, history=None, system_override=None):
    url = "https://api.groq.com/openai/v1/chat/completions"
    system = system_override if system_override else f"{SYSTEM_PROMPT}\n\nHozirgi bo'lim: {subject}"
    messages = [{"role": "system", "content": system}]
    if history:
        messages.extend(history[-10:])
    messages.append({"role": "user", "content": user_text})

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.7, "max_tokens": 2048}

    for attempt in range(3):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=25)
            print(f"Groq → {r.status_code} (urinish {attempt+1})")
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            if r.status_code == 429:
                wait = 3 * (attempt + 1)
                print(f"Rate limit — {wait}s kutilmoqda")
                standard_time.sleep(wait)
                continue
            if r.status_code in (502, 503, 504):
                print(f"Groq server xatosi {r.status_code} — qayta urinish")
                standard_time.sleep(2)
                continue
            return f"⚠️ Xatolik: {r.text[:200]}"
        except requests.exceptions.Timeout:
            if attempt < 2:
                standard_time.sleep(2)
                continue
            return "⏱ Server sekin javob berdi. Iltimos, qayta yuboring!"
        except Exception as e:
            return f"⚠️ Texnik xatolik: {str(e)}"
    return "⚠️ Server hozir band. 1-2 daqiqa kuting."


# ASL UZUN MULTIMEDIA PROMPTLARI (SAQLAB QOLINDI)
INGLIZ_PROMPT = """Siz professional ingliz tili ustozisiz. Rasmdagi matn, savol yoki mashqni ingliz tili qoidalari asosida o'zbek tilida tushuntiring.
• Mashq bo'lsa, har bir punktni alohida tahlil qiling va to'g'ri javobni yozing.
• Grammatika bo'lsa, qoidani o'zbekcha tushuntirib, rasmda keltirilgan misollarni tahlil qiling.
• Matn yoki yangi so'zlar bo'lsa, lug'at va talaffuzini yozing."""

NEMIS_PROMPT = """Sie sind ein professioneller Deutschlehrer. Rasmdagi nemis tili mashqini, grammatikasini yoki matnini to'liq o'zbek tilida tushuntirib bering.
• Wortschatz und Grammatik qismlarini alohida tahlil qiling.
• To'g'ri javoblarni asoslab bering."""

RUS_PROMPT = """Вы профессиональный учитель русского языка. Rasmdagi rus tili topshiriqlarini, kelshiklar, fe'llar yoki matnlarni o'zbek tilida chuqur tushuntiring.
• Grammatik qoidalarni aniq ko'rsating."""

TURK_PROMPT = """Siz profesyonel bir Türkçe öğretmenisiniz. Rasmdagi turk tili darsligi yoki mashqlarini o'zbek tilida tushuntirib yuboring."""

MATEMATIKA_PROMPT = """Siz tajribali matematika professorisiz. Rasmdagi misol yoki masalani chuqur tahlil qiling.
• Formulalarni va qoidalarni yozing.
• Bosqichma-bosqich yechimni ko'rsating.
• Yakuniy aniq javobni belgilang."""

FIZIKA_PROMPT = """Siz fizika fanidan olimpiada murabbiysisiz. Rasmdagi fizika masalasini yechib bering.
• Berilgan va so'ralgan kattaliklarni yozing.
• Fizika qonuniyatlari va formulalarini tushuntiring.
• Hisob-kitobni qadam-baqadam bajaring."""

KIMYO_PROMPT = """Siz kimyo fani doqtorisiz. Rasmdagi kimyoviy reaksiya, masala yoki elementlar tahlilini bering.
• Reaksiya tenglamalarini to'liq yozing.
• Masala bo'lsa, formulasini tushuntirib yeching."""

BIOLOGIYA_PROMPT = """Siz biologiya fani mutaxassisiz. Rasmdagi biologik chizma, atama yoki savolni o'zbek tilida batafsil tushuntiring."""

ADABIYOT_PROMPT = """Siz adabiyotshunos olimsiz. Rasmdagi matn, she'r yoki savolni adabiy nuqtai nazardan tahlil qiling."""

ONATILI_PROMPT = """Siz ona tili fani ekspertisiz. Rasmdagi grammatik topshiriq, gap tahlili yoki imlo qoidalarini to'liq yozing."""

WRITING_SYSTEM = "Siz rasmiy TELC imtihoni tekshiruvchisisiz. Foydalanuvchi yozgan matnni TELC mezonlari asosida qat'iy 0-75 ball tizimida baholaysiz."
SPEAKING_SYSTEM = "Siz professional SPEAKING (og'zaki nutq) murabbiyisiz. Matnni baholang va xatolarni ko'rsating."

def ask_ai_vision(image_bytes: bytes, prompt: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }
        ],
        "max_tokens": 3000
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=90)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return f"⚠️ Rasm tahlilida xato: {r.text[:200]}"
    except Exception as e:
        return f"⚠️ Texnik xatolik: {str(e)}"


# ======================================================
# QUIZ GENERATOR
# ======================================================
def generate_quiz(subject: str, used_questions: list = None) -> list:
    used_str = ""
    if used_questions:
        used_str = "\n\nQUYIDAGI SAVOLLARNI TAKRORLAMANG:\n" + "\n".join(f"- {q}" for q in used_questions[-20:])

    prompt = f"""'{subject}' mavzusida 10 ta test savoli tuzing.
A, B, C, D variantlardan faqat BITTASI to'g'ri bo'lsin.

Qat'iy quyidagi formatda yozing:
1. Savol matni?
A) ...
B) ...
C) ...
D) ...
To'g'ri: A
Izoh: ..."""

    result = ask_ai(prompt, subject, system_override="Siz professional test tuzuvchisiz. Faqat berilgan formatda javob bering.")
    questions = []

    for block in result.strip().split("\n\n"):
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if len(lines) < 7:
            continue
        try:
            q = {"question": lines[0].lstrip("0123456789. "), "options": {}, "answer": "", "explanation": ""}
            for line in lines[1:5]:
                if line.startswith(("A)", "B)", "C)", "D)")):
                    q["options"][line[0]] = line[3:].strip()
            for line in lines:
                if line.lower().startswith(("to'g'ri:", "togri:")):
                    ans = line.split(":")[-1].strip()
                    if ans: q["answer"] = ans[0].upper()
                if line.lower().startswith("izoh:"):
                    q["explanation"] = line.split(":", 1)[-1].strip()
            if q["question"] and len(q["options"]) >= 2 and q["answer"] in ["A", "B", "C", "D"]:
                questions.append(q)
        except Exception:
            continue
    return questions[:10]

async def send_daily_word(context):
    data = load_users()
    if not data["users"]: return
    langs = ["Ingliz", "Nemis", "Rus", "Turk"]
    lang = random.choice(langs)
    word_prompt = f"Bugungi kun uchun {lang} tilidan bitta foydali so'z tanlang. Format:\n🔤 So'z: ...\n📖 Ma'no: ..."
    word = ask_ai(word_prompt, lang, system_override="Siz til o'qituvchisisiz.")
    for chat_id in data["users"]:
        try: await context.bot.send_message(chat_id=chat_id, text=f"📅 Kundalik so'z — {lang} tili\n\n{word}")
        except Exception: pass

# Keep-alive server
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Alive")
    def log_message(self, format, *args): pass

def run_health_server():
    server = HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8000))), HealthHandler)
    server.serve_forever()

def run_self_ping():
    url = f"http://localhost:{os.getenv('PORT', 8000)}/"
    while True:
        standard_time.sleep(90)
        try: requests.get(url, timeout=10)
        except Exception: pass

ADMIN_ID = 6396413650

async def myid_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🔢 ID: {update.effective_user.id}")

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("🛡 ADMIN PANEL\n\n/broadcast <xabar>\n/reboot")

async def reboot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("🔄 Bot o'chib yonmoqda...")
    os._exit(0)

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args: return
    msg = " ".join(context.args)
    for uid in load_users()["users"]:
        try: await context.bot.send_message(chat_id=uid, text=f"📢 {msg}")
        except Exception: pass
    await update.message.reply_text("✅ Tugadi.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_chat.id)
    context.user_data.clear()
    context.user_data["stats"] = load_stats(update.effective_chat.id)
    await update.message.reply_text("Salom! Xush kelibsiz! 👇 Bo'limni tanlang:", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Yordam buyruqlari:\n/start - Boshlash\n/stats - Statistika")

async def language_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌍 Tilni tanlang:", reply_markup=ReplyKeyboardMarkup(languages_menu, resize_keyboard=True))

async def vocabulary_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ So'z tayyorlanmoqda...")
    await send_daily_word(context)

async def progress_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = load_stats(update.effective_chat.id)
    await update.message.reply_text(f"⭐ Daraja: {get_level(s['total'])}\nJami savollar: {s['total']}")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await progress_cmd(update, context)

# ======================================================
# MULTIMEDIA RASM/PDF QABUL QILISH (TO'G'RILANDI)
# ======================================================
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import asyncio
    subject = context.user_data.get("subject", "Umumiy")
    mode = context.user_data.get("mode", "normal")

    await update.message.reply_text("📸 Rasm qabul qilindi, tahlil qilinmoqda... ⏳")

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        img_bytes = bytes(await file.download_as_bytearray())

        # ASL PROMPTLAR BO'YICHA YO'NALTIRISH
        p_map = {
            "🇬🇧 Ingliz tili": INGLIZ_PROMPT, "🇩🇪 Nemis tili": NEMIS_PROMPT,
            "🇷🇺 Rus tili": RUS_PROMPT, "🇹🇷 Turk tili": TURK_PROMPT,
            "🧮 Matematika": MATEMATIKA_PROMPT, "🔭 Fizika": FIZIKA_PROMPT,
            "🧪 Kimyo": KIMYO_PROMPT, "🧬 Biologiya": BIOLOGIYA_PROMPT,
            "📚 Adabiyot": ADABIYOT_PROMPT, "📝 Ona tili": ONATILI_PROMPT
        }
        
        prompt = p_map.get(subject, "Ushbu rasmdagi topshiriqni tushuntirib bering.")
        if mode == "writing": prompt = WRITING_SYSTEM
        elif mode == "speaking": prompt = SPEAKING_SYSTEM

        if update.message.caption:
            prompt += f"\n\nFoydalanuvchi qo'shimcha so'rovi: {update.message.caption}"

        answer = await asyncio.get_running_loop().run_in_executor(None, lambda: ask_ai_vision(img_bytes, prompt))
        await update.message.reply_text(answer)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Tahlilda xato: {e}")

async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import asyncio
    doc = update.message.document
    if not doc.file_name.lower().endswith(".pdf"): return
    await update.message.reply_text("📄 PDF o'qilmoqda...")
    try:
        file = await context.bot.get_file(doc.file_id)
        b = bytes(await file.download_as_bytearray())
        text = ""
        with pdfplumber.open(BytesIO(b)) as pdf:
            for page in pdf.pages[:10]:
                text += (page.extract_text() or "") + "\n"
        ans = await asyncio.get_running_loop().run_in_executor(None, lambda: ask_ai(f"Tahlil qiling:\n{text[:3000]}", "PDF"))
        await update.message.reply_text(ans)
    except Exception as e:
        await update.message.reply_text(f"⚠️ PDF Xato: {e}")

# ======================================================
# XABARLARNI QAYTA ISHLASH
# ======================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_chat.id)
    text = update.message.text.strip()

    if context.user_data.get("quiz_active"):
        await handle_quiz_answer(update, context, text)
        return

    if text == "🌍 Jahon tillari":
        await update.message.reply_text("🌍 Tilni tanlang:", reply_markup=ReplyKeyboardMarkup(languages_menu, resize_keyboard=True))
        return
    if text == "🔢 Aniq fanlar":
        await update.message.reply_text("📚 Fanni tanlang:", reply_markup=ReplyKeyboardMarkup(science_menu, resize_keyboard=True))
        return
    if text == "📊 Statistika":
        await stats_cmd(update, context)
        return
    if text in ["🏠 Bosh menyu", "⬅️ Orqaga"]:
        context.user_data.pop("mode", None)
        await start(update, context)
        return

    if text == "📝 Writing tekshiruv":
        context.user_data.update({"mode": "writing"})
        await update.message.reply_text("📝 Matningizni yozing yoki rasmda yuboring. Men uni TELC tizimida tekshirib beraman.", reply_markup=ReplyKeyboardMarkup([["⬅️ Orqaga"]], resize_keyboard=True))
        return

    if text == "🎯 Quiz / Test":
        context.user_data["mode"] = "quiz_select"
        await update.message.reply_text("🎯 Qaysi bo'limdan test ishlaysiz?", reply_markup=ReplyKeyboardMarkup(quiz_subject_menu, resize_keyboard=True))
        return

    subjects = ["Ingliz tili", "Nemis tili", "Rus tili", "Turk tili", "Matematika", "Fizika", "Kimyo", "Biologiya", "Adabiyot", "Ona tili"]
    if any(x.lower() in text.lower() for x in subjects):
        if context.user_data.get("mode") == "quiz_select":
            import asyncio
            await update.message.reply_text(f"⏳ {text} bo'yicha test tayyorlanmoqda...")
            questions = await asyncio.get_running_loop().run_in_executor(None, lambda: generate_quiz(text))
            if not questions:
                await update.message.reply_text("⚠️ Test yaratib bo'lmadi.")
                return
            context.user_data.update({"quiz_active": True, "quiz_questions": questions, "quiz_index": 0, "quiz_score": 0, "quiz_subject": text})
            await send_quiz_question(update, context)
            return

        context.user_data.update({"subject": text, "history": [], "mode": "normal"})
        await update.message.reply_text(f"✅ {text} tanlandi. Savolingizni yozing yoki rasmini yuboring!")
        return

    subject = context.user_data.get("subject")
    if not subject and context.user_data.get("mode") != "writing":
        await update.message.reply_text("⚠️ Iltimos, avval menyudan birorta bo'limni tanlang.")
        return

    import asyncio
    await update.message.reply_text("⏳ O'ylayapman...")
    history = context.user_data.get("history", [])

    answer = await asyncio.get_running_loop().run_in_executor(None, lambda: ask_ai(text, subject or "Writing", history))
    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": answer})
    context.user_data["history"] = history[-20:]

    stats = load_stats(update.effective_chat.id)
    stats["total"] += 1
    save_stats(update.effective_chat.id, stats)

    await update.message.reply_text(answer)

async def send_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    questions = context.user_data["quiz_questions"]
    index = context.user_data["quiz_index"]
    q = questions[index]
    opts = "\n".join([f"{k}) {v}" for k, v in q["options"].items()])
    await update.message.reply_text(f"📝 Savol {index + 1}/{len(questions)}\n\n{q['question']}\n\n{opts}", reply_markup=ReplyKeyboardMarkup([["A", "B", "C", "D"], ["🚪 Testdan chiqish"]], resize_keyboard=True))

async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if text == "🚪 Testdan chiqish":
        context.user_data["quiz_active"] = False
        await start(update, context)
        return
    ans = text.strip().upper()
    if ans not in ["A", "B", "C", "D"]: return
    questions = context.user_data["quiz_questions"]
    index = context.user_data["quiz_index"]
    q = questions[index]

    if ans == q["answer"]:
        context.user_data["quiz_score"] += 1
        await update.message.reply_text(f"✅ To'g'ri!\n\n💡 Izoh: {q['explanation']}")
    else:
        await update.message.reply_text(f"❌ Noto'g'ri. To'g'ri javob: {q['answer']}\n\n💡 Izoh: {q['explanation']}")

    context.user_data["quiz_index"] += 1
    if context.user_data["quiz_index"] >= len(questions):
        await update.message.reply_text(f"🏁 Test tugadi. Natija: {context.user_data['quiz_score']}/{len(questions)}", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
        context.user_data["quiz_active"] = False
    else:
        await send_quiz_question(update, context)

async def error_handler(update, context: ContextTypes.DEFAULT_TYPE):
    print(f"❌ Xato: {context.error}")

def main():
    if not BOT_TOKEN or not GROQ_API_KEY: return
    threading.Thread(target=run_health_server, daemon=True).start()
    threading.Thread(target=run_self_ping, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    if app.job_queue:
        app.job_queue.run_daily(send_daily_word, time=datetime.time(hour=3, minute=0))
        print("✅ JobQueue yuklandi.")

    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("language", language_cmd))
    app.add_handler(CommandHandler("vocabulary", vocabulary_cmd))
    app.add_handler(CommandHandler("progress", progress_cmd))
    app.add_handler(CommandHandler("myid", myid_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("reboot", reboot_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.Document.PDF, document_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
