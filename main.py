import os
import json
import base64
import random
import threading
import requests
from datetime import time as dtime, datetime, date
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
    return 0, "💎 Siz eng yuqori darajasizи!"

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
    import time
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
                time.sleep(wait)
                continue
            if r.status_code in (502, 503, 504):
                print(f"Groq server xatosi {r.status_code} — qayta urinish")
                time.sleep(2)
                continue
            return f"⚠️ Xatolik: {r.text[:200]}"
        except requests.exceptions.Timeout:
            print(f"Groq timeout 25s (urinish {attempt+1})")
            if attempt < 2:
                time.sleep(2)
                continue
            return "⏱ Server sekin javob berdi. Iltimos, qayta yuboring!"
        except requests.exceptions.ConnectionError:
            print(f"Groq ulanish xatosi (urinish {attempt+1})")
            if attempt < 2:
                time.sleep(3)
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
        "Расскажите о человеке, который повлиял на вашу жизнь.",
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
1. MAZMUN VA G'OYA — 0-20 ball (topshiriqqa mos, rivojlangan g'oyalar)
2. RAVONLIK VA MANTIQ — 0-15 ball (mantiqiy tartib, bog'lovchilar)
3. LEKSIKA — 0-20 ball (so'z boyligi, iboralar, takrorlanmaslik)
4. GRAMMATIKA — 0-20 ball (xatosizlik, gap tuzilishi)

JAVOB FORMATI (qat'iy shu tartibda):

🎤 SPEAKING BAHOSI: XX/75

📋 MAZMUN VA G'OYA: XX/20
🔗 RAVONLIK VA MANTIQ: XX/15
📚 LEKSIKA: XX/20
✏️ GRAMMATIKA: XX/20

✅ YAXSHI TOMONLAR:
• ...

❌ XATOLAR VA ZAIF JOYLAR:
• (har bir xato + to'g'ri varianti)

🌟 NAMUNA JAVOB (Band 7-8 darajasida):
(Shu mavzu bo'yicha professional, to'liq namuna javob)

💡 FOYDALI IBORALAR:
• (5 ta shu mavzu uchun foydali ibora + tarjimasi)

MUHIM: ** yoki * ishlatmang. Rag'batlantiruvchi, adolatli va chuqur baho bering."""

WRITING_SYSTEM = """Siz rasmiy TELC imtihoni tekshiruvchisisiz. Foydalanuvchi yozgan matnni TELC mezonlari asosida qat'iy 0-75 ball tizimida baholaysiz.

Agar foydalanuvchi mavzu/shart ko'rsatgan bo'lsa — o'sha shartga qanchalik javob berganini ham baholang.
Agar mavzu ko'rsatilmagan bo'lsa — umumiy yozuv sifatini baholang.

TELC BAHOLASH MEZONLARI (jami 75 ball):

1. AUFGABENERFÜLLUNG — Topshiriqni bajarish: 0 dan 25 ball
   • Mavzu/topshiriq to'liq yoritildimi?
   • Barcha talab qilingan nuqtalar yozildimi?
   • G'oyalar rivojlantirilgan va dalillar keltirilganmi?
   • Matnning uzunligi va formati mos keladi mi?

2. KOMMUNIKATIVE GESTALTUNG — Uslub va tuzilish: 0 dan 25 ball
   • Matn mantiqiy va izchil tuzilganmi?
   • Kirish, asosiy qism, xulosa aniq ko'rinadi mi?
   • Bog'lovchi so'zlar va o'tish iboralari to'g'ri ishlatilganmi?
   • So'z boyligi va uslub darajasi mos keladi mi?

3. FORMALE RICHTIGKEIT — Grammatik to'g'rilik: 0 dan 25 ball
   • Grammatik xatolar soni va og'irligi
   • Gap tuzilishi va so'z tartibi to'g'riligи
   • Tinish belgilari va imlo to'g'riligи
   • Zamon va kelishik shakllarining to'g'riligi

JAVOB FORMATI (qat'iy shu tartibda):

📊 UMUMIY BALL: XX/75

📋 Aufgabenerfüllung (Topshiriq): XX/25
🔗 Kommunikative Gestaltung (Uslub): XX/25
✏️ Formale Richtigkeit (Grammatika): XX/25

✅ KUCHLI TOMONLAR:
• (2-3 ta aniq misol)

❌ XATOLAR:
• (har bir xato → to'g'ri varianti)

📝 YAXSHILANGAN VERSIYA:
(Xatolar to'g'rilangan to'liq matn)

💡 MASLAHAT:
(Keyingi safar nimaga e'tibor berish kerak — 1-2 ta aniq tavsiya)

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
• Amaliy, chuqur, o'quvchi uchun foydali javob bering
• Agar til mashqi bo'lsa — namuna gap/matn ham yozing"""

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
- Har bir savol ANIQ HISOB-KITOB talab qilsin (misol: 2x + 5 = 13, x = ?)
- To'g'ri javob ALBATTA to'g'ri bo'lsin — hisob-kitobni tekshiring!
- A, B, C, D variantlardan faqat BITTASI to'g'ri bo'lsin
- Variantlar bir-biridan aniq farq qilsin
- Savol oddiy bo'lsin, lekin hisob kerak bo'lsin"""
    else:
        extra = """- Savollar xilma-xil bo'lsin (so'z ma'nosi, grammatika, tarjima, gap to'ldirish)
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

2. Savol matni?
A) ...
B) ...
C) ...
D) ...
To'g'ri: B
Izoh: ...

Va hokazo 10 tagacha. Faqat savollar, boshqa hech narsa yozmang."""

    result = ask_ai(prompt, subject, system_override=(
        "Siz professional test tuzuvchi mutaxasssissiz. "
        "Faqat berilgan formatda savollar tuzing. "
        "Matematika savollarida hisob-kitobni ALBATTA tekshiring — xato javob bo'lmasin!"
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
                if line.lower().startswith("to'g'ri:") or line.lower().startswith("togri:") or line.lower().startswith("to`g`ri:"):
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
    import random
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
# KEEP-ALIVE + WATCHDOG
# ======================================================
import time as _time
_last_activity = _time.time()

def update_activity():
    global _last_activity
    _last_activity = _time.time()

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
    _time.sleep(10)
    while True:
        _time.sleep(90)
        try:
            r = requests.get(url, timeout=10)
            print(f"🔄 Self-ping: {r.status_code}")
        except Exception as e:
            print(f"⚠️ Self-ping xatolik: {e}")

# ======================================================
# ADMIN ID (faqat shu foydalanuvchi /admin ko'ra oladi)
# ======================================================
ADMIN_ID = 6396413650

# ======================================================
# /myid
# ======================================================
async def myid_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name or ""
    await update.message.reply_text(
        f"🪪 SIZNING TELEGRAM ID INGIZ:\n\n"
        f"👤 {name}\n"
        f"🔢 ID: {uid}\n\n"
        f"Bu ID ni menga yuboring — admin sifatida qo'shaman!"
    )

# ======================================================
# /admin
# ======================================================
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
        f"🛡 ADMIN PANEL\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"👥 Jami foydalanuvchilar: {total_users} ta\n\n"
        f"✅ Bot holati: FAOL\n\n"
        f"📌 ADMIN BUYRUQLAR:\n"
        f"• /broadcast <xabar> — hammaga xabar yuborish\n"
        f"• /reboot — botni qayta ishga tushirish\n"
        f"• /myid — Telegram ID ko'rish\n\n"
        f"👇 Foydalanuvchi buyruqlarini sinab ko'ring:"
    )
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
    )

# ======================================================
# /reboot
# ======================================================
async def reboot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_ID == 0 or update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bu buyruq faqat admin uchun.")
        return
    await update.message.reply_text("🔄 Bot qayta ishga tushirilmoqda... 5-10 soniyadan so'ng ishlaydi!")
    import os
    os._exit(0)

# ======================================================
# /broadcast
# ======================================================
async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_ID == 0 or update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bu buyruq faqat admin uchun.")
        return

    if not context.args:
        await update.message.reply_text(
            "📢 BROADCAST YUBORISH\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "Foydalanish:\n"
            "/broadcast <xabaringiz>\n\n"
            "Misol:\n"
            "/broadcast Bugun yangi darslar qo'shildi! 🎉"
        )
        return

    message_text = " ".join(context.args)
    data = load_users()
    users = data["users"]

    if not users:
        await update.message.reply_text("⚠️ Hali hech qanday foydalanuvchi yo'q.")
        return

    sent = 0
    failed = 0
    status_msg = await update.message.reply_text(
        f"📤 Yuborilmoqda... 0/{len(users)}"
    )

    for chat_id in users:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📢 ADMIN XABARI\n━━━━━━━━━━━━━━━━\n\n{message_text}"
            )
            sent += 1
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"✅ BROADCAST YAKUNLANDI\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"📨 Yuborildi: {sent} ta\n"
        f"❌ Xatolik: {failed} ta\n"
        f"👥 Jami: {len(users)} ta foydalanuvchi"
    )

# ======================================================
# /start
# ======================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_activity()
    save_user(update.effective_chat.id)
    name = update.effective_user.first_name or "O'quvchi"
    saved_stats = load_stats(update.effective_chat.id)
    context.user_data.clear()
    context.user_data["stats"] = saved_stats

    greetings = [
        f"Salom, {name}! 👋 O'rganishga tayyor bo'lsangiz, men ham tayor! 🚀",
        f"Xush kelibsiz, {name}! 🎉 Bugun nima o'rganamiz?",
        f"Assalomu alaykum, {name}! 🌟 Bilim olishni boshlaylik!",
        f"Salom {name}! 😊 LangGo Academy sizni kutib turardi!",
    ]

    text = (
        f"{random.choice(greetings)}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌍 Til o'rganish — Ingliz, Nemis, Rus, Turk\n"
        "🔢 Aniq fanlar — Matematika, Fizika...\n"
        "📝 Speaking & Writing — IELTS feedback\n"
        "🎯 Quiz / Test — bilimingizni sinang\n"
        "🗣 Erkin suhbat — til amaliyoti\n"
        "📸 Rasm yuboring — AI tahlil qiladi\n"
        "📄 PDF yuboring — matnni tahlil qiladi\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 Kerakli bo'limni tanlang:"
    )
    await update.message.reply_text(text,
        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))

# ======================================================
# /help
# ======================================================
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or "Noma'lum"
    username = f"@{user.username}" if user.username else "username yo'q"
    uid = user.id

    text = (
        "📚 LangGo Academy — Yordam\n\n"
        "Buyruqlar:\n"
        "/start — Botni qayta ishga tushirish\n"
        "/language — Til tanlash\n"
        "/vocabulary — Bugungi yangi so'z\n"
        "/progress — Mening yutuqlarim\n"
        "/stats — Statistikangiz\n"
        "/help — Ushbu yordam\n\n"
        "Bo'limlar:\n"
        "🌍 Jahon tillari — tarjima, grammatika, idiomlar\n"
        "🔢 Aniq fanlar — bosqichma-bosqich tushuntirish\n"
        "📝 Speaking/Writing — IELTS feedback\n"
        "🎯 Quiz/Test — bilimingizni sinang\n"
        "🗣 Erkin suhbat — til amaliyoti\n\n"
        "Maxsus:\n"
        "📸 Rasm yuboring — AI tahlil qiladi\n"
        "📄 PDF yuboring — matnni tahlil qiladi\n"
        "📅 Kundalik so'z — har kuni yangi so'z\n\n"
        "Muammo yoki savol bo'lsa admin bilan bog'laning: @nurik_571m\n\n"
        "Bot javob bermasa: /reboot yuboring — o'zi qayta ishga tushadi!"
    )
    await update.message.reply_text(text)

    if ADMIN_ID != 0:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"🆘 YORDAM SO'ROVI\n"
                    f"━━━━━━━━━━━━━━━━\n\n"
                    f"👤 Ism: {name}\n"
                    f"🔗 Username: {username}\n"
                    f"🔢 ID: {uid}\n\n"
                    f"Foydalanuvchi /help buyrug'ini bosdi."
                )
            )
        except Exception:
            pass

# ======================================================
# /language
# ======================================================
async def language_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌐 TIL TANLASH\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "Qaysi tilda o'rganmoqchisiz?",
        reply_markup=ReplyKeyboardMarkup(languages_menu, resize_keyboard=True)
    )

# ======================================================
# /vocabulary
# ======================================================
async def vocabulary_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import asyncio
    await update.message.reply_text("📅 Bugungi so'z tayyorlanmoqda... ⏳")

    langs = ["Ingliz", "Nemis", "Rus", "Turk"]
    lang = random.choice(langs)
    word_prompt = (
        f"Bugungi kun uchun {lang} tilidan bitta foydali so'z tanlang. Format:\n"
        f"🔤 So'z: ...\n📖 Ma'no: ...\n🗣 Talaffuz: ...\n💬 Misol: ...\n🔄 Tarjima: ..."
    )
    word = await asyncio.get_running_loop().run_in_executor(
        None,
        lambda: ask_ai(word_prompt, lang, system_override="Siz til o'qituvchisisiz. Har kuni yangi foydali so'z o'rgatasiz.")
    )
    await update.message.reply_text(f"📅 Kundalik so'z — {lang} tili\n\n{word}")

# ======================================================
# /progress
# ======================================================
async def progress_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    saved = load_stats(update.effective_chat.id)
    mem = context.user_data.get("stats", {"total": 0, "subjects": {}})
    stats = saved if saved["total"] >= mem["total"] else mem
    total = stats["total"]

    if total == 0:
        await update.message.reply_text(
            "🏆 MENING YUTUQLARIM\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Hali hech qanday yutuq yo'q!\n\n"
            "Boshlang — har bir savol yangi yutuqqa olib keladi! 🚀"
        )
        return

    level = get_level(total)
    need, next_level = get_next_level(total)
    subjects = stats["subjects"]

    earned = [msg for milestone, msg in ACHIEVEMENTS.items() if total >= milestone]
    achievements_text = "\n".join(earned) if earned else "• Hali mukofot yo'q — davom eting!"

    progress_bar = "█" * min(10, total // 5) + "░" * max(0, 10 - total // 5)
    next_text = f"Keyingi daraja: {next_level} ({need} ta savol qoldi)" if need > 0 else "🎉 Eng yuqori daraja!"

    top = sorted(subjects.items(), key=lambda x: x[1], reverse=True)[:3]
    top_text = "\n".join([f"  {i+1}. {s} — {c} ta" for i, (s, c) in enumerate(top)]) if top else "  Hali yo'q"

    text = (
        f"🏆 MENING YUTUQLARIM\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Daraja: {level}\n"
        f"⭐ Jami savollar: {total} ta\n"
        f"📈 Progress: [{progress_bar}]\n"
        f"🎯 {next_text}\n\n"
        f"🏅 MUKOFOTLAR:\n{achievements_text}\n\n"
        f"📚 ENG KO'P ISHLATILADIGAN:\n{top_text}"
    )
    await update.message.reply_text(text)

# ======================================================
# /stats
# ======================================================
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    saved = load_stats(update.effective_chat.id)
    mem = context.user_data.get("stats", {"total": 0, "subjects": {}})
    stats = saved if saved["total"] >= mem["total"] else mem
    total = stats["total"]
    subjects = stats["subjects"]

    if total == 0:
        await update.message.reply_text(
            "📊 Hali savol bermagansiz!\n\n"
            "Boshlang — har bir savol sizi yangi darajaga olib chiqadi! 🚀"
        )
        return

    level = get_level(total)
    need, next_level = get_next_level(total)
    top = sorted(subjects.items(), key=lambda x: x[1], reverse=True)[:3]
    top_text = "\n".join([f"  {i+1}. {s} — {c} ta savol" for i, (s, c) in enumerate(top)])

    progress_bar = "█" * min(10, total // 5) + "░" * max(0, 10 - total // 5)

    next_text = f"Keyingi daraja: {next_level} ({need} ta savol qoldi)" if need > 0 else "🎉 Eng yuqori daraja!"

    text = (
        f"📊 SIZNING STATISTIKANGIZ\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Daraja: {level}\n"
        f"⭐ Jami savollar: {total} ta\n"
        f"📈 Progress: [{progress_bar}]\n"
        f"🎯 {next_text}\n\n"
        f"🏆 ENG KO'P ISHLATILADIGAN:\n{top_text}\n\n"
        f"Davom eting! {random.choice(MOTIVATIONS)}"
    )
    await update.message.reply_text(text)

# ======================================================
# PHOTO HANDLER
# ======================================================
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_activity()
    import asyncio
    mode = context.user_data.get("mode", "normal")
    writing_lang = context.user_data.get("writing_lang", "")
    speaking_lang = context.user_data.get("speaking_lang", "")

    if mode == "writing_topic":
        await update.message.reply_text("📸 Shartni rasmdan o'qimoqdaman... ⏳")
    elif mode == "writing":
        await update.message.reply_text("📸 Yozma ishingiz rasmi tahlil qilinmoqda va TELC mezonlari asosida tekshirilmoqda... ⏳")
    elif mode == "speaking":
        await update.message.reply_text("📸 Rasmdagi matn speaking sifatida baholanmoqda... ⏳")
    else:
        await update.message.reply_text("📸 Rasm tahlil qilinmoqda... ⏳ (20-30 soniya)")

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytearray = await file.download_as_bytearray()
        image_bytes = bytes(image_bytearray)

        user_caption = update.message.caption

        if mode == "writing_topic":
            lang = writing_lang or "Ingliz"
            extract_prompt = (
                f"Bu rasmda {lang} tilidagi TELC yoki boshqa rasmiy imtihonning yozma (writing) topshiriq sharti bor. "
                f"Rasmdagi barcha matn va punktlarni o'qi. Ularni o'zbek tilida qisqa, tushunarli va punktma-punkt formatda extract qilib ber. "
                f"Faqat topshiriq sharti mazmunini yoz, boshqa gap qo'shma."
            )
            extracted_topic = await asyncio.get_running_loop().run_in_executor(
                None, lambda: ask_ai_vision(image_bytes, extract_prompt)
            )
            context.user_data["writing_topic"] = extracted_topic
            context.user_data["mode"] = "writing"
            await update.message.reply_text(
                f"✅ Shart aniqlandi:\n\n📋 {extracted_topic}\n\n"
                f"✍️ Endi o'zingiz yozgan email/xatni matn ko'rinishida yuboring yoki rasmini joylang!",
                reply_markup=ReplyKeyboardMarkup(
                    [["⬅️ Orqaga"]], resize_keyboard=True
                )
            )
            return

        if mode == "writing":
            lang = writing_lang or "Ingliz"
            topic = context.user_data.get("writing_topic", "")
            caption_hint = f"\nFoydalanuvchi qo'shimcha izoh qoldirdi: {user_caption}" if user_caption else ""
            prompt = (
                f"Rasmdagi qo'lda yoki bosmada {lang} tilida yozilgan matnni (yozma ishni) diqqat bilan o'qi.\n"
                f"Berilgan topshiriq sharti: {topic}\n"
                f"Ushbu matnni TELC standartlari asosida, qat'iy 0-75 ball tizimida bahola.{caption_hint}\n\n"
                f"{WRITING_SYSTEM}"
            )
            subject = f"{lang} writing"
        elif mode == "speaking":
            lang = speaking_lang or "Ingliz"
            topic = context.user_data.get("speaking_topic", "")
            prompt = (
                f"Rasmdagi matnni o'qi va {lang} tilida yozilgan speaking javobi sifatida baho.\n"
                f"Mavzu: {topic}\n\n"
                f"{SPEAKING_SYSTEM}"
            )
            subject = f"{lang} speaking"
        elif user_caption:
            prompt = user_caption
            subject = "Rasm tahlil"
        else:
            prompt = (
                "Bu rasmni diqqat bilan ko'ring. Bu o'quv kitobi yoki darslik sahifasi bo'lishi mumkin.\n\n"
                "QUYIDAGILARNI BAJARING:\n"
                "1. Rasmdagi TOPSHIRIQ/VAZIFANI aniqlang va o'zbek tilida tushuntiring\n"
                "2. Har bir PUNKTNI/BANDNI RAQAM BILAN alohida tushuntiring\n"
                "3. Har bir punkt uchun NAMUNA JAVOB yoki MISOL yozing\n"
                "4. Vazifani bajarish uchun G'OYALAR va FOYDALI IBORALAR bering\n"
                "5. Zarur grammatika yoki leksikani ham tushuntiring\n\n"
                "Faqat rasm tavsifini bermasdan — TO'LIQ O'QUV YORDAMI bering!"
            )
            subject = "Rasm tahlil"

        answer = await asyncio.get_running_loop().run_in_executor(
            None, lambda: ask_ai_vision(image_bytes, prompt)
        )

        # Statistika yangilash (agar writing yoki speaking bo'lsa)
        if mode in ("writing", "speaking"):
            saved = load_stats(update.effective_chat.id)
            mem = context.user_data.get("stats", {"total": 0, "subjects": {}})
            stats = saved if saved["total"] >= mem["total"] else mem
            stats["total"] += 1
            stats["subjects"][subject] = stats["subjects"].get(subject, 0) + 1
            context.user_data["stats"] = stats
            save_stats(update.effective_chat.id, stats)

        if len(answer) > 4096:
            for i in range(0, len(answer), 4096):
                await update.message.reply_text(answer[i:i + 4096])
        else:
            await update.message.reply_text(answer)

    except Exception as e:
        print(f"Photo handler error: {e}")
        await update.message.reply_text(f"⚠️ Rasm tahlilida xatolik yuz berdi. Qayta urinib ko'ring.")

# ======================================================
# DOCUMENT HANDLER (PDF)
# ======================================================
async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_activity()
    import asyncio
    doc = update.message.document

    if not doc.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("⚠️ Faqat PDF formatdagi fayllar qabul qilinadi.")
        return

    await update.message.reply_text("📄 PDF o'qilmoqda... ⏳")

    try:
        file = await context.bot.get_file(doc.file_id)
        pdf_bytearray = await file.download_as_bytearray()

        text = ""
        try:
            with pdfplumber.open(BytesIO(bytes(pdf_bytearray))) as pdf:
                for page in pdf.pages[:10]:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
        except Exception as e:
            await update.message.reply_text(f"⚠️ PDF o'qib bo'lmadi: {str(e)}")
            return

        if not text.strip():
            await update.message.reply_text("⚠️ PDF dan matn topilmadi.")
            return

        truncated = text[:3000]
        caption = update.message.caption or "Bu matnni tahlil qiling, asosiy g'oyalarini tushuntiring va savollar tuzing."
        prompt = f"Matn:\n{truncated}\n\nSo'rov: {caption}"

        answer = await asyncio.get_running_loop().run_in_executor(
            None, lambda: ask_ai(prompt, "PDF tahlil")
        )

        if len(answer) > 4096:
            for i in range(0, len(answer), 4096):
                await update.message.reply_text(answer[i:i + 4096])
        else:
            await update.message.reply_text(answer)

    except Exception as e:
        print(f"Document handler error: {e}")
        await update.message.reply_text("⚠️ PDF tahlilida xatolik yuz berdi. Qayta urinib ko'ring.")

# ======================================================
# HANDLE TEXT MESSAGES
# ======================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_activity()
    save_user(update.effective_chat.id)
    text = update.message.text.strip()

    # ---- QUIZ MODE ----
    if context.user_data.get("quiz_active"):
        await handle_quiz_answer(update, context, text)
        return

    # ---- MAIN MENU ----
    if text == "🌍 Jahon tillari":
        await update.message.reply_text("🌍 Tilni tanlang:",
            reply_markup=ReplyKeyboardMarkup(languages_menu, resize_keyboard=True))
        return

    if text == "🔢 Aniq fanlar":
        await update.message.reply_text("📚 Fanni tanlang:",
            reply_markup=ReplyKeyboardMarkup(science_menu, resize_keyboard=True))
        return

    if text == "📝 Writing tekshiruv":
        context.user_data.update({"mode": "writing_select"})
        await update.message.reply_text(
            "📝 WRITING TEKSHIRUVI\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "Qaysi tilda yozgan matningizni tekshirasiz?\n\n"
            "Tilni tanlang:",
            reply_markup=ReplyKeyboardMarkup(
                [["✍️ Ingliz writing", "✍️ Nemis writing"],
                 ["✍️ Rus writing", "✍️ O'zbek writing"],
                 ["⬅️ Orqaga"]],
                resize_keyboard=True
            )
        )
        return

    if text == "🎤 Speaking simulyatsiya":
        await update.message.reply_text(
            "🎤 SPEAKING SIMULYATSIYA\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "Qaysi tilda speaking mashq qilasiz?\n\n"
            "Tilni tanlang:",
            reply_markup=ReplyKeyboardMarkup(
                [["🎤 Ingliz speaking", "🎤 Nemis speaking"],
                 ["🎤 Rus speaking"],
                 ["⬅️ Orqaga"]],
                resize_keyboard=True
            )
        )
        return

    if text in ["🎤 Ingliz speaking", "🎤 Nemis speaking", "🎤 Rus speaking"]:
        lang_map = {
            "🎤 Ingliz speaking": "🇬🇧 Ingliz",
            "🎤 Nemis speaking": "🇩🇪 Nemis",
            "🎤 Rus speaking": "🇷🇺 Rus",
        }
        lang_key = lang_map[text]
        topic = random.choice(SPEAKING_TOPICS.get(lang_key, SPEAKING_TOPICS["🇬🇧 Ingliz"]))
        context.user_data.update({
            "subject": f"{lang_key} speaking",
            "speaking_lang": lang_key,
            "speaking_topic": topic,
            "history": [],
            "mode": "speaking"
        })
        lang_display = lang_key.split(" ")[1]
        await update.message.reply_text(
            f"🎤 {lang_display.upper()} SPEAKING\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"📌 MAVZUINGIZ:\n\n"
            f"❝ {topic} ❞\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📊 Baholash: 0-75 ball (4 mezon)\n"
            f"⏱ Tavsiya: 2-3 paragraf yozing\n\n"
            f"👇 Javobingizni yuboring:",
            reply_markup=ReplyKeyboardMarkup(
                [["🔄 Boshqa mavzu", "⬅️ Orqaga"]], resize_keyboard=True
            )
        )
        return

    if text == "🔄 Boshqa mavzu":
        lang_key = context.user_data.get("speaking_lang", "🇬🇧 Ingliz")
        topic = random.choice(SPEAKING_TOPICS.get(lang_key, SPEAKING_TOPICS["🇬🇧 Ingliz"]))
        context.user_data["speaking_topic"] = topic
        lang_display = lang_key.split(" ")[1]
        await update.message.reply_text(
            f"🔄 YANGI MAVZU:\n\n"
            f"❝ {topic} ❞\n\n"
            f"👇 Javobingizni yuboring:",
            reply_markup=ReplyKeyboardMarkup(
                [["🔄 Boshqa mavzu", "⬅️ Orqaga"]], resize_keyboard=True
            )
        )
        return

    if text in ["✍️ Ingliz writing", "✍️ Nemis writing", "✍️ Rus writing", "✍️ O'zbek writing"]:
        lang = text.replace("✍️ ", "").replace(" writing", "")
        context.user_data.update({
            "subject": f"{lang} writing",
            "writing_lang": lang,
            "history": [],
            "mode": "writing_topic"
        })
        await update.message.reply_text(
            f"✍️ {lang} WRITING TEKSHIRUVI\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"📋 Qaysi shart/mavzu bo'yicha yozdingiz?\n\n"
            f"📝 Matn qilib yuborishingiz\n"
            f"YOKI\n"
            f"📸 TELC writing topshiriq sharti rasmini yuborishingiz mumkin (AI o'zi o'qiydi).\n\n"
            f"Agar aniq bir mavzu bo'lmasa — «Mavzu yo'q» deb yuboring.",
            reply_markup=ReplyKeyboardMarkup(
                [["Mavzu yo'q"], ["⬅️ Orqaga"]], resize_keyboard=True
            )
        )
        return

    if text == "🎯 Quiz / Test":
        context.user_data["mode"] = "quiz_select"
        await update.message.reply_text("🎯 Qaysi bo'limdan test olasiz?",
            reply_markup=ReplyKeyboardMarkup(quiz_subject_menu, resize_keyboard=True))
        return

    if text == "🗣 Erkin suhbat":
        context.user_data.update({
            "subject": "Erkin suhbat",
            "history": [],
            "mode": "conversation",
        })
        await update.message.reply_text(
            "🗣 Erkin suhbat rejimi!\n\n"
            "Istalgan tilda gapirishingiz mumkin — men xatolaringizni to'g'irlab, "
            "tabiiy javob beraman. Boshlang!"
        )
        return

    if text == "📊 Statistika":
        await stats_cmd(update, context)
        return

    if text == "🏠 Bosh menyu":
        await start(update, context)
        return

    if text == "🌐 Til tanlash":
        await language_cmd(update, context)
        return

    if text == "📅 Bugungi so'z":
        await vocabulary_cmd(update, context)
        return

    if text == "🏆 Yutuqlar":
        await progress_cmd(update, context)
        return

    if text == "❓ Yordam":
        await help_cmd(update, context)
        return

    if text == "📢 Broadcast":
        await update.message.reply_text(
            "📢 BROADCAST YUBORISH\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "Foydalanish:\n"
            "/broadcast <xabaringiz>\n\n"
            "Misol:\n"
            "/broadcast Bugun yangi darslar qo'shildi! 🎉"
        )
        return

    if text == "🔄 Reboot":
        if update.effective_user.id == ADMIN_ID:
            await reboot_cmd(update, context)
        return

    if text == "⚙️ Sozlamalar":
        await update.message.reply_text("⚙️ Sozlamalar:",
            reply_markup=ReplyKeyboardMarkup(settings_menu, resize_keyboard=True))
        return

    if text == "⬅️ Orqaga":
        context.user_data.pop("mode", None)
        await update.message.reply_text("🏠 Asosiy menyu:",
            reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
        return

    # ---- SETTINGS ----
    if text == "📅 Kundalik so'z: Yoqish":
        save_user(update.effective_chat.id)
        await update.message.reply_text("✅ Kundalik so'z yoqildi! Har kuni ertalab yangi so'z keladi.")
        return

    if text == "📅 Kundalik so'z: O'chirish":
        data = load_users()
        chat_id = update.effective_chat.id
        if chat_id in data["users"]:
            data["users"].remove(chat_id)
            USERS_FILE.write_text(json.dumps(data))
        await update.message.reply_text("❌ Kundalik so'z o'chirildi.")
        return

    if text.startswith("🌐 Bot tili:"):
        lang = "ingliz" if "Ingliz" in text else "o'zbek"
        context.user_data["ui_lang"] = lang
        await update.message.reply_text(f"✅ Bot tili {text.split(':')[1].strip()} ga o'zgartirildi.")
        return

    # ---- SUBJECT SELECT ----
    subjects = ["Ingliz", "Nemis", "Rus", "Turk", "Matematika", "Fizika", "Kimyo", "Biologiya", "Adabiyot", "Ona tili"]

    if any(x.lower() in text.lower() for x in subjects):
        mode = context.user_data.get("mode", "normal")

        if mode == "quiz_select":
            import asyncio
            await update.message.reply_text(
                f"⏳ {text} bo'yicha 10 ta savol tayyorlanmoqda...",
                reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
            )
            used = context.user_data.get("quiz_used_questions", {}).get(text, [])
            questions = await asyncio.get_running_loop().run_in_executor(
                None, lambda: generate_quiz(text, used)
            )

            if not questions:
                await update.message.reply_text("⚠️ Savollar yaratishda xatolik. Qayta urining.")
                return

            used_map = context.user_data.get("quiz_used_questions", {})
            used_map[text] = used + [q["question"] for q in questions]
            context.user_data["quiz_used_questions"] = used_map

            context.user_data.update({
                "quiz_active": True,
                "quiz_questions": questions,
                "quiz_index": 0,
                "quiz_score": 0,
                "quiz_subject": text
            })
            await send_quiz_question(update, context)
            return

        context.user_data.update({"subject": text, "history": [], "mode": "normal"})
        await update.message.reply_text(f"✅ {text} tanlandi. Savolingizni yuboring!")
        return

    # ---- WRITING TOPIC HANDLER ----
    if context.user_data.get("mode") == "writing_topic":
        topic = "" if text == "Mavzu yo'q" else text
        context.user_data["writing_topic"] = topic
        context.user_data["mode"] = "writing"
        topic_line = f"Mavzu: {topic}" if topic else "Shart ko'rsatilmagan — umumiy yozuv sifati baholanadi."
        await update.message.reply_text(
            f"✅ Mavzu qabul qilindi!\n"
            f"📋 {topic_line}\n\n"
            f"✍️ Endi o'zingiz yozgan email/xatni matn ko'rinishida yuboring yoki rasmini joylang (AI o'qiydi)!",
            reply_markup=ReplyKeyboardMarkup(
                [["⬅️ Orqaga"]], resize_keyboard=True
            )
        )
        return

    # ---- SUBJECT CHECK ----
    subject = context.user_data.get("subject")

    if not subject:
        await update.message.reply_text("⚠️ Avval bo'lim tanlang.",
            reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
        return

    # ---- AI ANSWER ----
    import asyncio
    await update.message.reply_text("⏳ O'ylayapman...")

    mode = context.user_data.get("mode", "normal")
    history = context.user_data.get("history", [])

    if mode == "speaking":
        lang = context.user_data.get("speaking_lang", "")
        topic = context.user_data.get("speaking_topic", "")
        system = (
            f"{SPEAKING_SYSTEM}\n\n"
            f"Til: {lang}\n"
            f"Mavzu: {topic}\n\n"
            f"Foydalanuvchi shu mavzu bo'yicha javob yozdi — uni baholaydi."
        )
        answer = await asyncio.get_running_loop().run_in_executor(
            None, lambda: ask_ai(text, subject, history, system_override=system)
        )
    elif mode == "writing":
        lang = context.user_data.get("writing_lang", "")
        preview = text[:300] + ("..." if len(text) > 300 else "")
        await update.message.reply_text(
            f"📝 Siz yozgansiz:\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"{preview}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"⏳ TELC mezonlari bo'yicha baholanmoqda..."
        )
        topic = context.user_data.get("writing_topic", "")
        topic_note = f"Foydalanuvchi quyidagi shart/mavzu bo'yicha yozgan: {topic}" if topic else "Shart ko'rsatilmagan — umumiy yozuv sifatini baholang."
        system = (
            f"{WRITING_SYSTEM}\n\n"
            f"Til: {lang}\n"
            f"{topic_note}"
        )
        answer = await asyncio.get_running_loop().run_in_executor(
            None, lambda: ask_ai(text, subject, history, system_override=system)
        )
    elif mode == "conversation":
        system = (
            f"{SYSTEM_PROMPT}\n\n"
            "Hozir ERKIN SUHBAT rejimi. Foydalanuvchi bilan tabiiy suhbatlashing. "
            "Uning grammatik xatolarini asta-sekin to'g'irlang. "
            "Qisqa, jonli javob bering. Har javob oxirida qiziqarli savol bering."
        )
        answer = await asyncio.get_running_loop().run_in_executor(
            None, lambda: ask_ai(text, subject, history, system_override=system)
        )
    else:
        answer = await asyncio.get_running_loop().run_in_executor(
            None, lambda: ask_ai(text, subject, history)
        )

    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": answer})
    if len(history) > 20:
        history = history[-20:]
    context.user_data["history"] = history

    saved = load_stats(update.effective_chat.id)
    mem = context.user_data.get("stats", {"total": 0, "subjects": {}})
    stats = saved if saved["total"] >= mem["total"] else mem
    prev_total = stats["total"]
    stats["total"] += 1
    stats["subjects"][subject] = stats["subjects"].get(subject, 0) + 1
    context.user_data["stats"] = stats
    save_stats(update.effective_chat.id, stats)
    new_total = stats["total"]

    if len(answer) > 4096:
        for i in range(0, len(answer), 4096):
            await update.message.reply_text(answer[i:i + 4096])
    else:
        await update.message.reply_text(answer)

    if new_total in ACHIEVEMENTS:
        await update.message.reply_text(
            f"🎊 TABRIKLAYMIZ!\n{ACHIEVEMENTS[new_total]}\n\n"
            f"Darajangiz: {get_level(new_total)}"
        )
    elif new_total % 5 == 0 and new_total > 0:
        await update.message.reply_text(random.choice(FUN_FACTS))
    elif random.random() < 0.3:
        await update.message.reply_text(f"💬 {random.choice(MOTIVATIONS)}")

# ======================================================
# QUIZ LOGIC
# ======================================================
async def send_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    questions = context.user_data["quiz_questions"]
    index = context.user_data["quiz_index"]
    q = questions[index]

    options_text = "\n".join([f"{k}) {v}" for k, v in q["options"].items()])
    text = (
        f"📝 Savol {index + 1}/{len(questions)}\n\n"
        f"{q['question']}\n\n"
        f"{options_text}\n\n"
        f"Javobingizni yuboring (A, B, C yoki D):"
    )
    await update.message.reply_text(text,
        reply_markup=ReplyKeyboardMarkup([["A", "B", "C", "D"], ["🚪 Testdan chiqish"]], resize_keyboard=True))


async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if text == "🚪 Testdan chiqish":
        score = context.user_data.get("quiz_score", 0)
        total = context.user_data.get("quiz_index", 0)
        context.user_data["quiz_active"] = False
        await update.message.reply_text(
            f"🏁 Test tugadi!\n\n✅ Natija: {score}/{total}\n\nAsosiy menyuga qaytdingiz.",
            reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
        )
        return

    answer = text.strip().upper()
    if answer not in ["A", "B", "C", "D"]:
        await update.message.reply_text("⚠️ Faqat A, B, C yoki D yuboring.")
        return

    questions = context.user_data["quiz_questions"]
    index = context.user_data["quiz_index"]
    q = questions[index]
    correct = q["answer"]

    if answer == correct:
        context.user_data["quiz_score"] += 1
        feedback = f"✅ To'g'ri! Barakalla! 🎉\n\n💡 {q.get('explanation', '')}"
    else:
        feedback = f"❌ Noto'g'ri.\n\n✔️ To'g'ri javob: {correct}\n\n💡 {q.get('explanation', '')}"

    context.user_data["quiz_index"] += 1
    await update.message.reply_text(feedback)

    if context.user_data["quiz_index"] >= len(questions):
        score = context.user_data["quiz_score"]
        total = len(questions)
        context.user_data["quiz_active"] = False

        if score == total:
            result_msg = "🏆 MUKAMMAL! Barcha savollar to'g'ri! Siz dahosiz! 🌟"
        elif score >= total * 0.8:
            result_msg = "🥇 A'LO natija! Zo'r ketayapsiz! 🔥"
        elif score >= total * 0.6:
            result_msg = "🥈 Yaxshi! Biroz mashq qilsangiz, mukammal bo'lasiz! 💪"
        elif score >= total * 0.4:
            result_msg = "🥉 Yaxshi urinish! Takrorlang va qayta sinang! 📚"
        else:
            result_msg = "📖 Bu mavzuni ko'proq o'rganing — keling, birga qilamiz! 🤝"

        percent = int(score / total * 100)
        stars = "⭐" * score + "☆" * (total - score)

        await update.message.reply_text(
            f"🏁 TEST YAKUNLANDI!\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"✅ Natija: {score}/{total}  ({percent}%)\n"
            f"{stars}\n\n"
            f"{result_msg}\n\n"
            f"Yana sinab ko'ring! Amaliyot — muvaffaqiyat kaliti! 🗝",
            reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
        )
    else:
        await send_quiz_question(update, context)

# ======================================================
# ERROR HANDLER
# ======================================================
async def error_handler(update, context: ContextTypes.DEFAULT_TYPE):
    import traceback
    err = context.error
    tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))
    print(f"❌ Xatolik:\n{tb}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ Texnik nosozlik yuz berdi. Biroz kuting va qayta urinib ko'ring.\n"
                "Agar muammo davom etsa /start bosing."
            )
    except Exception:
        pass

# ======================================================
# MAIN
# ======================================================
def main():
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN topilmadi")
        return
    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY topilmadi")
        return

    threading.Thread(target=run_health_server, daemon=True).start()
    threading.Thread(target=run_self_ping, daemon=True).start()
    print("✅ Keep-alive server ishga tushdi")

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )

    app.job_queue.run_daily(send_daily_word, time=dtime(hour=3, minute=0))

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

    print("🚀 LangGo Academy ishga tushdi — 24/7 faol!")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"],
    )

if __name__ == "__main__":
    main()
