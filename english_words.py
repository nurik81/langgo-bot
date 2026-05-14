en_data = [
    # --- VAQT VA DAVRIY (Time) ---
    ["bugun", "today"], ["ertaga", "tomorrow"], ["kecha", "yesterday"],
    ["hozir", "now"], ["keyin", "later"], ["har doim", "always"],
    ["hech qachon", "never"], ["ba'zan", "sometimes"], ["hafta", "week"],
    ["oy", "month"], ["yil", "year"], ["soat", "hour"],

    # --- SIFATLAR (Kengaytirilgan) ---
    ["issiq", "hot"], ["sovuq", "cold"], ["iliq", "warm"], ["shirin", "sweet"],
    ["achchiq", "bitter"], ["sho'r", "salty"], ["og'ir", "heavy"],
    ["yengil", "light"], ["boy", "rich"], ["kambag'al", "poor"],
    ["yosh", "young"], ["qari", "old"], ["toza", "clean"],
    ["iflos", "dirty"], ["baland", "high"], ["past", "low"],

    # --- MUHIM FE'LLAR (Action Verbs) ---
    ["yashamoq", "live"], ["ishlamoq", "work"], ["o'ynamoq", "play"],
    ["yordam bermoq", "help"], ["tushunmoq", "understand"], ["eslamoq", "remember"],
    ["unutmoq", "forget"], ["sotib olmoq", "buy"], ["sotmoq", "sell"],
    ["to'lamoq", "pay"], ["kutmoq", "wait"], ["shoshilmoq", "hurry"],
    ["pishirmoq", "cook"], ["tozalamoq", "clean"], ["yuvmoq", "wash"],

    # --- TABIAT VA OB-HAVO (Nature) ---
    ["osmon", "sky"], ["quyosh", "sun"], ["oy", "moon"], ["yulduz", "star"],
    ["daraxt", "tree"], ["gul", "flower"], ["o't", "grass"], ["tog'", "mountain"],
    ["daryo", "river"], ["dengiz", "sea"], ["shamol", "wind"], ["yomg'ir", "rain"],
    ["qor", "snow"], ["tuman", "fog"], ["olov", "fire"], ["yer", "earth"],

    # --- TAOM VA ICHIMLIK (Food & Drink) ---
    ["non", "bread"], ["suv", "water"], ["sut", "milk"], ["choy", "tea"],
    ["qahva", "coffee"], ["sharbat", "juice"], ["tuz", "salt"], ["shakar", "sugar"],
    ["tuxum", "egg"], ["pishloq", "cheese"], ["go'sht", "meat"], ["guruch", "rice"],
    ["meva", "fruit"], ["sabzavot", "vegetable"], ["shirinlik", "sweet/candy"],

    # --- JAMOAT JOYI VA TRANSPORT ---
    ["ko'cha", "street"], ["yo'l", "road"], ["park", "park"], ["do'kon", "shop"],
    ["maktab", "school"], ["ish", "work"], ["shahar", "city"], ["qishloq", "village"],
    ["mamlakat", "country"], ["aeroport", "airport"], ["avtobus", "bus"],
    ["mashina", "car"], ["poyezd", "train"], ["samolyot", "plane"], ["kema", "ship"],

    # --- UY VA KUNDALIK BUYUMLAR ---
    ["xona", "room"], ["oshxona", "kitchen"], ["hammom", "bathroom"],
    ["deraza", "window"], ["eshik", "door"], ["devor", "wall"], ["tom", "roof"],
    ["karovat", "bed"], ["stul", "chair"], ["stol", "table"], ["oyna", "mirror"],
    ["sumka", "bag"], ["pul", "money"], ["soat", "watch/clock"], ["kalit", "key"]
]
    # --- OLMOSHLAR VA BIRIKMALAR ---
    ["men", "I"], ["sen", "you"], ["u (o'g'il)", "he"], ["u (qiz)", "she"],
    ["biz", "we"], ["ular", "they"], ["meniki", "mine"], ["seniki", "yours"],
    ["uniki (o'g'il)", "his"], ["uniki (qiz)", "hers"],
    ["menda bor", "I have"], ["senda bor", "you have"],

    # --- SHAHAR VA JOY NOMLARI (Places) ---
    ["dorixona", "pharmacy"], ["shifoxona", "hospital"], ["politsiya", "police"],
    ["do'kon", "shop"], ["supermarket", "supermarket"], ["restoran", "restaurant"],
    ["mehmonxona", "hotel"], ["bank", "bank"], ["teatr", "theater"],
    ["muzey", "museum"], ["kutubxona", "library"], ["maydon", "square"],

    # --- KASBLAR (Jobs) ---
    ["shifokor", "doctor"], ["hamshira", "nurse"], ["haydovchi", "driver"],
    ["oshpaz", "cook"], ["muhandis", "engineer"], ["sotuvchi", "seller"],
    ["politsiyachi", "policeman"], ["talaba", "student"], ["uchuvchi", "pilot"],

    # --- SPORT VA O'YINLAR ---
    ["to'p", "ball"], ["futbol", "football"], ["suzish", "swimming"],
    ["yugurish", "running"], ["g'alaba", "victory"], ["jamoa", "team"],

    # --- HIS-TUYG'ULAR (Feelings) ---
    ["sevgi", "love"], ["nafrat", "hate"], ["qo'rquv", "fear"],
    ["quvonch", "joy"], ["g'azab", "anger"], ["tinchlik", "peace"],
    ["ishonch", "trust"], ["umid", "hope"],

    # --- RANGLAR (Colors) ---
    ["pushti", "pink"], ["jigarrang", "brown"], ["kulrang", "grey"],
    ["siyohrang", "purple"], ["to'q sariq", "orange"], ["oltinrang", "golden"],

    # --- MAVSUM VA OB-HAVO ---
    ["bahor", "spring"], ["yoz", "summer"], ["kuz", "autumn"], ["qish", "winter"],
    ["quyoshli", "sunny"], ["bulutli", "cloudy"], ["issiq", "warm"],
    ["sovuq", "cold"], ["yomg'irli", "rainy"], ["qorli", "snowy"],

    # --- MAKTAB VA ISH ---
    ["qalam", "pencil"], ["ruchka", "pen"], ["daftar", "notebook"],
    ["lug'at", "dictionary"], ["imtihon", "exam"], ["savol", "question"],
    ["javob", "answer"], ["xato", "error"],

    # --- TAOMLAR VA ICHIMLIKLAR ---
    ["guruch", "rice"], ["sho'rva", "soup"], ["shakar", "sugar"],
    ["tuz", "salt"], ["qahva", "coffee"], ["sharbat", "juice"],
    ["pishloq", "cheese"], ["yog'", "oil"], ["asal", "honey"]
]
    # --- ELDERS ---
    ["bobo", "grandfather"],
    ["buvi", "grandmother"],
    ["katta bobo", "great-grandfather"],
    ["katta buvi", "great-grandmother"],

    # --- UNCLE, AUNT AND COUSINS ---
    ["amaki / tog‘a", "uncle"],
    ["amma / xola", "aunt"],
    ["amakivachcha / ammavachcha (umumiy)", "cousin"],
    
    # --- IN-LAWS AND OTHERS ---
    ["kelinoyi / yanga", "sister-in-law"],
    ["pochcha", "brother-in-law"],
    ["oila a'zosi", "family member"],
    ["qarindoshlik", "kinship"],
    ["egizak", "twin"],
    ["asrab olingan bola", "adopted child"]
]
    # --- BASIC FAMILY ---
    ["ota-ona", "parents"],
    ["farzandlar", "children"],
    ["egizaklar", "twins"],
    ["er-xotin", "married couple"],
    
    # --- RELATIVES (In-laws & others) ---
    ["qaynona", "mother-in-law"],
    ["qaynota", "father-in-law"],
    ["kelin", "daughter-in-law"],
    ["kuyov", "son-in-law"],
    ["qayinaga / qayini", "brother-in-law"],
    ["qayinsingil / qayniopa", "sister-in-law"],
    ["o'gay ota", "stepfather"],
    ["o'gay ona", "stepmother"],
    ["o'gay aka/uka", "stepbrother"],
    ["o'gay opa/singil", "stepsister"],
    ["ajdodlar", "ancestors"],
    ["avlodlar", "descendants"],
    ["qarindosh", "relative"]
]
