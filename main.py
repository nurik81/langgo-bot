import os
import json
import base64
import random
import threading
import requests
import time as standard_time  # Nom chalkashmasligi uchun standard time modulini alohida nomladik
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
            print(f"Groq timeout 25s (urinish {attempt+1})")
            if attempt < 2:
                standard_time.sleep(2)
                continue
            return "⏱ Server sekin javob berdi. Iltimos, qayta yuboring!"
        except requests.exceptions.ConnectionError:
            print(f"Groq ulanish xatosi (urinish {attempt+1})")
            if attempt < 2:
                standard_time.sleep(3)
                continue
            return "📡 Internet yoki server muammo. Biroz kuting va qayta yuboring!"
        except Exception as e:
            print(f"Groq kutilmagan xato: {e}")
            return f"⚠️ Texnik xatolik. /reboot yuboring yoki keyinroq urining."
    return "⚠️ Server hozir band. 1-2 daqiqadan so'ng qayta yuboring!"


SPEAKING_TOPICS = {
    "🇬🇧 Ingliz": [
        "Describe your hometown. What do you like or dislike about it?",
        "Talk about a person who has greatly influenced your life.",
        "Describe a memorable trip or journey you have taken.",
        "What are the advantages and disadvantages of social media?",
        "Talk about your favorite book or movie and why you like it.",
        "Describe a skill you would like to learn and explain why.",
        "Do you think technology makes our lives better or worse? Why?",
        "Talk about a challenge you have faced and how you overcame it.",
        "Describe your ideal job and explain what makes it appealing.",
        "Should universities be free for all students? Give your opinion.",
    ],
    "🇩🇪 Nemis": [
        "Beschreiben Sie Ihre Heimatstadt. Was gefällt Ihnen dort?",
        "Sprechen Sie über eine Person, die Ihr Leben beeinflusst hat.",
        "Beschreiben Sie eine unvergessliche Reise.",
        "Was sind die Vor- und Nachteile der sozialen Medien?",
        "Sprechen Sie über Ihr Lieblingshobbys und warum.",
        "Beschreiben Sie Ihren Traumjob.",
        "Soll das Studium kostenlos sein? Begründen Sie Ihre Meinung.",
        "Wie wichtig ist Sport in Ihrem Leben?",
        "Beschreiben Sie eine schwierige Situation und wie Sie sie gelöst haben.",
        "Was halten Sie von der Umweltverschmutzung? Was kann man tun?",
    ],
    "🇷🇺 Rus": [
        "Опишите ваш родной город. Что вам в нём нравится?",
        "Расскажите о человеку, который повлиял на вашу жизнь.",
        "Опишите незабываемую поездку.",
        "Каковы плюсы и минусы социальных сетей?",
        "Расскажите о вашем хобби и почему вам это нравится.",
        "Опишите вашу мечту о работе.",
        "Должно ли высшее образование быть бесплатным?",
        "Как технологии влияют на нашу жизнь?",
        "Расскажите о трудной ситуации и как вы с ней справились.",
        "Что вы думаете об охране окружающей среды?",
    ],
}

SPEAKING_SYSTEM = """Siz professional SPEAKING (og'zaki nutq) murabbiyisiz.
Foydalanuvchi yozma tarzda speaking javobini yuboryapti — uni baholaydi va o'rgatasan.

BAHOLASH (0-75 BALL):
1. MAZMUN VA G'OYA — 0-20 ball
2. RAVONLIK VA MANTIQ — 0-15 ball
3. LEKSIKA — 0-20 ball
4. GRAMMATIKA — 0-20 ball

JAVOB FORMATI (qat'iy shu tartibda):

🎤 SPEAKING BAHOSI: XX/75

📋 MAZMUN VA G'OYA: XX/20
🔗 RAVONLIK VA MANTIQ: XX/15
📚 LEKSIKA: XX/20
✏️ GRAMMATIKA: XX/20

✅ YAXSHI TOMONLAR:
• ...

❌ XATOLAR VA ZAIF JOYLAR:
• ...

🌟 NAMUNA JAVOB (Band 7-8 darajasida):
...

💡 FOYDALI IBORALAR:
• ...

MUHIM: ** yoki * ishlatmang. Rag'batlantiruvchi, adolatli va chuqur baho bering."""

WRITING_SYSTEM = """Siz rasmiy TELC imtihoni tekshiruvchisisiz. Foydalanuvchi yozgan matnni TELC mezonlari asosida qat'iy 0-75 ball tizimida baholaysiz.

TELC BAHOLASH MEZONLARI (jami 75 ball):
1. AUFGABENERFÜLLUNG — Topshiriqni bajarish: 0 dan 25 ball
2. KOMMUNIKATIVE GESTALTUNG — Uslub va tuzilish: 0 dan 25 ball
3. FORMALE RICHTIGKEIT — Grammatik to'g'rilik: 0 dan 25 ball

JAVOB FORMATI (qat'iy shu tartibda):

📊 UMUMIY BALL: XX/75

📋 Aufgabenerfüllung (Topshiriq): XX/25
🔗 Kommunikative Gestaltung (Uslub): XX/25
✏️ Formale Richtigkeit (Grammatika): XX/25

✅ KUCHLI TOMONLAR:
• ...

❌ XATOLAR:
• ...

📝 YAXSHILANGAN VERSIYA:
...

💡 MASLAHAT:
...

MUHIM: ** yoki * ishlatmang. TELC standartida adolatli va aniq baho bering."""

VISION_SYSTEM = """Siz LangGo Academy ning til va fan o'qituvchisisiz. 
Foydalanuvchi o'quv kitobi, darslik yoki mashq sahifasining rasmini yubordi.

VAZIFANGIZ — shunchaki rasm tavsifini emas, TO'LIQ TA'LIM YORDAMINI bering:
1. Rasmdagi TOPSHIRIQ/VAZIFANI aniqlang
2. Har bir PUNKT yoki BANDNI raqam bilan ALOHIDA tushuntiring
3. Har bir punkt uchun NAMUNA JAVOB va MISOL yozing
4. Vazifani bajarish uchun FOYDALI G'OYALAR va IBORALAR tavsiya qiling
5. Zarur GRAMMATIKA yoki LEKSIKANI tushuntiring
6. Oxirida foydalanuvchini rag'batlantiring

MUHIM: 
• Javobni O'ZBEK TILIDA yozing
• ** asterisk ishlatmang — faqat KATTA HARF, • nuqtalar va emojilar
• Amaliy, chuqur, o'quvchi uchun foydali javob bering"""

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
                    {"type": "text", "text": f"{VISION_SYSTEM}\n\nFoydalanuvchi so'rovi: {prompt}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }
        ],
        "max_tokens": 3000
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=90)
        print(f"Groq Vision → {r.status_code}")
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return f"⚠️ Rasm tahlil xatolik: {r.text[:200]}"
    except Exception as e:
        return f"⚠️ Texnik xatolik: {str(e)}"


# ======================================================
# QUIZ GENERATOR
# ======================================================
def generate_quiz(subject: str, used_questions: list = None) -> list:
    used_str = ""
    if used_questions:
        used_str = "\n\nQUYIDAGI SAVOLLARNI TAKRORLAMANG:\n" + "\n".join(f"- {q}" for q in used_questions[-20:])

    is_math = any(x in subject for x in ["Matematika", "Fizika", "Kimyo"])

    if is_math:
        extra = """MATEMATIKA/FIZIKA/KIMYO uchun MUHIM QOIDALAR:
- Har bir savol ANIQ HISOB-KITOB talab qilsin
- To'g'ri javob ALBATTA to'g'ri bo'lsin
- A, B, C, D variantlardan faqat BITTASI to'g'ri bo'lsin"""
    else:
        extra = """- Savollar xilma-xil bo'lsin (so'z ma'nosi, grammatika, tarjima)
- To'g'ri javob aniq va shubhasiz bo'lsin"""

    prompt = f"""'{subject}' mavzusida 10 ta test savoli tuzing.

{extra}
{used_str}

Qat'iy quyidagi formatda yozing (har savol orasida bo'sh qator bo'lsin):
1. Savol matni?
A) ...
B) ...
C) ...
D) ...
To'g'ri: A
Izoh: ...

Faqa't savollar, boshqa hech narsa yozmang."""

    result = ask_ai(prompt, subject, system_override=(
        "Siz professional test tuzuvchi mutaxasssissiz. Faqat berilgan formatda savollar tuzing."
    ))
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
                if line.lower().startswith(("to'g'ri:", "togri:", "to`g`ri:")):
                    ans = line.split(":")[-1].strip()
                    if ans:
                        q["answer"] = ans[0].upper()
                if line.lower().startswith("izoh:"):
                    q["explanation"] = line.split(":", 1)[-1].strip()
            if q["question"] and len(q["options"]) >= 2 and q["answer"] in ["A", "B", "C", "D"]:
                questions.append(q)
        except Exception:
            continue

    return questions[:10]


# ======================================================
# DAILY WORD
# ======================================================
async def send_daily_word(context):
    data = load_users()
    if not data["users"]:
        return

    langs = ["Ingliz", "Nemis", "Rus", "Turk"]
    lang = random.choice(langs)

    word_prompt = f"Bugungi kun uchun {lang} tilidan bitta foydali so'z tanlang. Format:\n🔤 So'z: ...\n📖 Ma'no: ...\n🗣 Talaffuz: ...\n💬 Misol: ...\n🔄 Tarjima: ..."
    word = ask_ai(word_prompt, lang, system_override="Siz til o'qituvchisisiz. Har kuni yangi foydali so'z o'rgatasiz.")

    for chat_id in data["users"]:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📅 Kundalik so'z — {lang} tili\n\n{word}"
            )
        except Exception as e:
            print(f"Daily word error for {chat_id}: {e}")


# ======================================================
# KEEP-ALIVE
# ======================================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"LangGo Academy Bot is alive!")
    def log_message(self, format, *args):
        pass

def run_health_server():
    port = int(os.getenv("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

def run_self_ping():
    port = int(os.getenv("PORT", 8000))
    url = f"http://localhost:{port}/"
    print(f"🔄 Self-ping ishga tushdi: {url}")
    standard_time.sleep(10)
    while True:
        standard_time.sleep(90)
        try:
            r = requests.get(url, timeout=10)
            print(f"🔄 Self-ping: {r.status_code}")
        except Exception as e:
            print(f"⚠️ Self-ping xatolik: {e}")

# ======================================================
# ADMIN ID
# ======================================================
ADMIN_ID = 6396413650

async def myid_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name or ""
    await update.message.reply_text(
        f"🪪 SIZNING TELEGRAM ID INGIZ:\n\n👤 {name}\n🔢 ID: {uid}"
    )

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_ID == 0 or update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bu buyruq faqat admin uchun.")
        return

    data = load_users()
    total_users = len(data["users"])

    admin_menu = [
        ["🏠 Bosh menyu", "🌐 Til tanlash"],
        ["📅 Bugungi so'z", "🏆 Yutuqlar"],
        ["📊 Statistika", "❓ Yordam"],
        ["📢 Broadcast", "🔄 Reboot"],
    ]

    text = (
        f"🛡 ADMIN PANEL\n━━━━━━━━━━━━━━━━\n\n"
        f"👥 Jami foydalanuvchilar: {total_users} ta\n\n"
        f"📌 ADMIN BUYRUQLAR:\n• /broadcast <xabar>\n• /reboot"
    )
    await update.message.reply_text(
        text, reply_markup=ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
    )

async def reboot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_ID == 0 or update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bu buyruq faqat admin uchun.")
        return
    await update.message.reply_text("🔄 Bot qayta ishga tushirilmoqda...")
    os._exit(0)

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_ID == 0 or update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bu buyruq faqat admin uchun.")
        return

    if not context.args:
        await update.message.reply_text("📢 Foydalanish: /broadcast <xabaringiz>")
        return

    message_text = " ".join(context.args)
    data = load_users()
    users = data["users"]

    sent = 0
    failed = 0
    status_msg = await update.message.reply_text(f"📤 Yuborilmoqda... 0/{len(users)}")

    for chat_id in users:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📢 ADMIN XABARI\n━━━━━━━━━━━━━━━━\n\n{message_text}"
            )
            sent += 1
        except Exception:
            failed += 1

    await status_msg.edit_text(f"✅ Yuborildi: {sent} ta\n❌ Xatolik: {failed} ta")

# ======================================================
# CORE COMMANDS
# ======================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_chat.id)
    name = update.effective_user.first_name or "O'quvchi"
    saved_stats = load_stats(update.effective_chat.id)
    context.user_data.clear()
    context.user_data["stats"] = saved_stats

    text = (
        f"Salom, {name}! 👋 LangGo Academy virtual botiga xush kelibsiz!\n\n"
        "👇 Kerakli bo'limni tanlang:"
    )
    await update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📚 LangGo Academy — Yordam\n\n"
        "/start — Botni qayta ishga tushirish\n"
        "/language — Til tanlash\n"
        "/vocabulary — Bugungi yangi so'z\n"
        "/stats — Statistikangiz\n\n"
        "Muammo yoki savol bo'lsa admin bilan bog'laning: @nurik_571m"
    )
    await update.message.reply_text(text)

async def language_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌐 Qaysi tilda o'rganmoqchisiz?",
        reply_markup=ReplyKeyboardMarkup(languages_menu, resize_keyboard=True)
    )

async def vocabulary_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import asyncio
    await update.message.reply_text("📅 Bugungi so'z tayyorlanmoqda... ⏳")
    langs = ["Ingliz", "Nemis", "Rus", "Turk"]
    lang = random.choice(langs)
    word_prompt = f"Bugungi kun uchun {lang} tilidan bitta foydali so'z tanlang. Format:\n🔤 So'z: ...\n📖 Ma'no: ..."
    word = await asyncio.get_running_loop().run_in_executor(
        None, lambda: ask_ai(word_prompt, lang, system_override="Siz til o'qituvchisisiz.")
    )
    await update.message.reply_text(f"📅 Kundalik so'z — {lang} tili\n\n{word}")

async def progress_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    saved = load_stats(update.effective_chat.id)
    total = saved.get("total", 0)
    level = get_level(total)
    await update.message.reply_text(f"🏆 YUTUQLARINGIZ:\n\n👤 Daraja: {level}\n⭐ Jami savollar: {total} ta")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    saved = load_stats(update.effective_chat.id)
    total = saved.get("total", 0)
    level = get_level(total)
    await update.message.reply_text(f"📊 STATISTIKA:\n\n👤 Darajangiz: {level}\n⭐ Berilgan savollar: {total} ta")

# ======================================================
# MULTIMEDIA HANDLERS
# ======================================================
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import asyncio
    mode = context.user_data.get("mode", "normal")
    writing_lang = context.user_data.get("writing_lang", "")
    speaking_lang = context.user_data.get("speaking_lang", "")

    await update.message.reply_text("📸 Rasm tahlil qilinmoqda... ⏳ (20-30 soniya)")

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytearray = await file.download_as_bytearray()
        image_bytes = bytes(image_bytearray)
        user_caption = update.message.caption

        if mode == "writing_topic":
            lang = writing_lang or "Ingliz"
            extract_prompt = f"Rasmdagi topshiriq/shartni o'qi va faqat shartni qisqacha o'zbek tilida yoz."
            extracted_topic = await asyncio.get_running_loop().run_in_executor(
                None, lambda: ask_ai_vision(image_bytes, extract_prompt)
            )
            context.user_data["writing_topic"] = extracted_topic
            context.user_data["mode"] = "writing"
            await update.message.reply_text(f"✅ Shart aniqlandi:\n\n📋 {extracted_topic}\n\nEndi yozma ishingizni rasmda yuboring!")
            return

        if mode == "writing":
            lang = writing_lang or "Ingliz"
            prompt = f"Rasmdagi {lang} matnni TELC tizimida bahola.\n\n{WRITING_SYSTEM}"
        elif mode == "speaking":
            lang = speaking_lang or "Ingliz"
            prompt = f"Rasmdagi matnni {lang} speaking deb bahola.\n\n{SPEAKING_SYSTEM}"
        elif user_caption:
            prompt = user_caption
        else:
            prompt = "Ushbu darslik rasmini aniqlab, to'liq o'quv yordami bering."

        answer = await asyncio.get_running_loop().run_in_executor(
            None, lambda: ask_ai_vision(image_bytes, prompt)
        )

        if len(answer) > 4096:
            for i in range(0, len(answer), 4096):
                await update.message.reply_text(answer[i:i + 4096])
        else:
            await update.message.reply_text(answer)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Rasm tahlilida xatolik: {e}")

async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import asyncio
    doc = update.message.document
    if not doc.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("⚠️ Faqat PDF qabul qilinadi.")
        return

    await update.message.reply_text("📄 PDF o'qilmoqda... ⏳")
    try:
        file = await context.bot.get_file(doc.file_id)
        pdf_bytearray = await file.download_as_bytearray()
        text = ""
        with pdfplumber.open(BytesIO(bytes(pdf_bytearray))) as pdf:
            for page in pdf.pages[:10]:
                t = page.extract_text()
                if t: text += t + "\n"

        if not text.strip():
            await update.message.reply_text("⚠️ PDF bo'sh.")
            return

        prompt = f"Matn:\n{text[:3000]}\n\nTahlil qiling."
        answer = await asyncio.get_running_loop().run_in_executor(
            None, lambda: ask_ai(prompt, "PDF tahlil")
        )
        await update.message.reply_text(answer)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Xato: {e}")

# ======================================================
# MESSAGE PROCESSING
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
    if text == "🏠 Bosh menyu" or text == "⬅️ Orqaga":
        context.user_data.pop("mode", None)
        await start(update, context)
        return

    if text == "📝 Writing tekshiruv":
        context.user_data.update({"mode": "writing_select"})
        await update.message.reply_text("📝 Qaysi tildagi matnni tekshiramiz?", reply_markup=ReplyKeyboardMarkup(
            [["✍️ Ingliz writing", "✍️ Nemis writing"], ["⬅️ Orqaga"]], resize_keyboard=True
        ))
        return

    if text in ["✍️ Ingliz writing", "✍️ Nemis writing"]:
        lang = text.replace("✍️ ", "").replace(" writing", "")
        context.user_data.update({"mode": "writing_topic", "writing_lang": lang})
        await update.message.reply_text(f"✍️ {lang} Writing mavzusi yoki shartini yozing (yoki rasm yuboring). Shart bo'lmasa 'Mavzu yo'q' deb yozing.", reply_markup=ReplyKeyboardMarkup([["Mavzu yo'q"], ["⬅️ Orqaga"]], resize_keyboard=True))
        return

    if context.user_data.get("mode") == "writing_topic":
        topic = "" if text == "Mavzu yo'q" else text
        context.user_data.update({"writing_topic": topic, "mode": "writing"})
        await update.message.reply_text("✅ Shart saqlandi. Endi to'liq matningizni yozib yuboring!")
        return

    if text == "🎯 Quiz / Test":
        context.user_data["mode"] = "quiz_select"
        await update.message.reply_text("🎯 Qaysi bo'limdan test ishlaysiz?", reply_markup=ReplyKeyboardMarkup(quiz_subject_menu, resize_keyboard=True))
        return

    subjects = ["Ingliz", "Nemis", "Rus", "Turk", "Matematika", "Fizika", "Kimyo", "Biologiya", "Adabiyot", "Ona tili"]
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
        await update.message.reply_text(f"✅ {text} tanlandi. Savolingizni yozib yuboring!")
        return

    subject = context.user_data.get("subject")
    mode = context.user_data.get("mode", "normal")
    if not subject and mode not in ["writing", "speaking"]:
        await update.message.reply_text("⚠️ Iltimos, avval menyudan birorta bo'limni tanlang.")
        return

    import asyncio
    await update.message.reply_text("⏳ O'ylayapman...")
    history = context.user_data.get("history", [])

    if mode == "writing":
        topic = context.user_data.get("writing_topic", "")
        system = f"{WRITING_SYSTEM}\nMavzu: {topic}"
        answer = await asyncio.get_running_loop().run_in_executor(None, lambda: ask_ai(text, "Writing", history, system_override=system))
    else:
        answer = await asyncio.get_running_loop().run_in_executor(None, lambda: ask_ai(text, subject, history))

    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": answer})
    context.user_data["history"] = history[-20:]

    # Statistikani yangilash
    stats = load_stats(update.effective_chat.id)
    stats["total"] += 1
    if subject: stats["subjects"][subject] = stats["subjects"].get(subject, 0) + 1
    save_stats(update.effective_chat.id, stats)

    await update.message.reply_text(answer)

# ======================================================
# QUIZ HANDLERS
# ======================================================
async def send_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    questions = context.user_data["quiz_questions"]
    index = context.user_data["quiz_index"]
    q = questions[index]
    options_text = "\n".join([f"{k}) {v}" for k, v in q["options"].items()])
    await update.message.reply_text(
        f"📝 Savol {index + 1}/{len(questions)}\n\n{q['question']}\n\n{options_text}",
        reply_markup=ReplyKeyboardMarkup([["A", "B", "C", "D"], ["🚪 Testdan chiqish"]], resize_keyboard=True)
    )

async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if text == "🚪 Testdan chiqish":
        context.user_data["quiz_active"] = False
        await update.message.reply_text("🏁 Test to'xtatildi.", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
        return

    ans = text.strip().upper()
    if ans not in ["A", "B", "C", "D"]:
        await update.message.reply_text("⚠️ Faqat A, B, C yoki D variantini bosing.")
        return

    questions = context.user_data["quiz_questions"]
    index = context.user_data["quiz_index"]
    q = questions[index]

    if ans == q["answer"]:
        context.user_data["quiz_score"] += 1
        await update.message.reply_text(f"✅ To'g'ri! 🎉\n\n💡 Izoh: {q['explanation']}")
    else:
        await update.message.reply_text(f"❌ Noto'g'ri. To'g'ri javob: {q['answer']}\n\n💡 Izoh: {q['explanation']}")

    context.user_data["quiz_index"] += 1
    if context.user_data["quiz_index"] >= len(questions):
        score = context.user_data["quiz_score"]
        context.user_data["quiz_active"] = False
        await update.message.reply_text(f"🏁 Test yakunlandi! Natijangiz: {score}/{len(questions)}", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
    else:
        await send_quiz_question(update, context)

async def error_handler(update, context: ContextTypes.DEFAULT_TYPE):
    print(f"❌ Xatolik yuz berdi: {context.error}")

# ======================================================
# MAIN FUNCTION
# ======================================================
def main():
    if not BOT_TOKEN or not GROQ_API_KEY:
        print("❌ Tokenlar topilmadi. Atrof-muhit o'zgaruvchilarini tekshiring.")
        return

    threading.Thread(target=run_health_server, daemon=True).start()
    threading.Thread(target=run_self_ping, daemon=True).start()
    print("✅ Keep-alive server yoqildi.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # TUZATISH: JobQueue mavjudligi xavfsiz tekshiriladi
    if app.job_queue:
        app.job_queue.run_daily(send_daily_word, time=datetime.time(hour=3, minute=0))
        print("✅ Kunlik vazifa (JobQueue) yuklandi.")
    else:
        print("⚠️ Ogohlantirish: JobQueue o'rnatilmagan (bepul hosting cheklovi bo'lishi mumkin).")

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

    print("🚀 Bot muvaffaqiyatli ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
