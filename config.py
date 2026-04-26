import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_PATH = os.getenv('DB_PATH', 'database/bot.db')

# ==================== AI ACCESS ====================
AI_PAYMENT_AMOUNT = 49
AI_TRIAL_DAYS = 3
MAX_REQUESTS_PER_DAY_FREE = 5
MAX_REQUESTS_PER_DAY_PAID = 50

# ==================== SIM.DL ====================
SIM_PAYMENT_AMOUNT = 299
SIM_OPERATORS = ["Билайн", "Мегафон", "МТС", "Tele2"]
SIM_REGIONS = ["Москва", "СПб", "Казань", "Екатеринбург", "Новосибирск"]
SIM_TARIFFS = ["Доверенное лицо", "Корпоративный", "Самозанятый"]

# ==================== CASH.DL ====================
CASH_ITEMS = {
    "obnal_samozanyat": {
        "name": "💳 Обнал через самозанятого",
        "price": 499,
        "desc": "Вывод до 500к/мес через СБП. Комиссия 3-4%",
        "category": "obnal"
    },
    "obnal_card": {
        "name": "💳 Обнал на карты физлиц",
        "price": 599,
        "desc": "Схема дробления платежей до 150к/день без блокировки",
        "category": "obnal"
    },
    "crypto_split": {
        "name": "₿ Крипто-сплит через P2P",
        "price": 599,
        "desc": "Разделение крипты на 10+ кошельков без KYC",
        "category": "crypto"
    },
    "crypto_nft": {
        "name": "₿ Отмыв через NFT",
        "price": 999,
        "desc": "Грязная крипта → NFT → чистая крипта. Полный цикл",
        "category": "crypto"
    },
    "drop_card": {
        "name": "🏢 Карта дропа удалённо",
        "price": 799,
        "desc": "Оформление дебетовки на дропа. Сим-карта + доступ в банк",
        "category": "drop"
    },
    "drop_ip": {
        "name": "🏢 ИП на дропа под ключ",
        "price": 1499,
        "desc": "ИП + счёт + ЭЦП. Полный пакет за 3 дня",
        "category": "drop"
    },
    "return_wb": {
        "name": "📊 Возврат на Wildberries",
        "price": 399,
        "desc": "Схема возврата товара без отправки обратно",
        "category": "return"
    },
    "return_ozon": {
        "name": "📊 Возврат на Ozon",
        "price": 399,
        "desc": "100% возврат средств за любой товар",
        "category": "return"
    },
}

CASH_CATEGORIES = {
    "obnal": "💳 Обнал",
    "crypto": "₿ Крипта",
    "drop": "🏢 Дропы",
    "return": "📊 Возвраты",
}

# ==================== WHITE MYSTIC LAB ====================
SHOP_BRAND = "🧪 WHITE MYSTIC LAB"
SHOP_SLOGAN = "Лаборатория чистой энергии"

SHOP_CITIES = ["Астрахань", "Камызяк"]

SHOP_DISTRICTS = {
    "Астрахань": [
        "🔬 Кировский кластер",
        "⚗️ Ленинский кластер", 
        "🧬 Советский кластер",
        "💊 Трусовский кластер",
        "🧫 Центр-лаб"
    ],
    "Камызяк": [
        "🔬 Центр-лаб",
        "⚗️ Табола-сектор",
        "🧬 Юбилейный-сектор",
        "💊 Мелиоративный-сектор"
    ],
}

SHOP_ITEMS = {
    "crystal_05_ast": {
        "name": "❄️ CRYSTAL WHITE 0.5", "price": 2500,
        "desc": "Лабораторные кристаллы. Чистота 99.1%. Пробник 0.5g",
        "city": "Астрахань", "category": "crystal", "emoji": "❄️"
    },
    "crystal_1_ast": {
        "name": "❄️ CRYSTAL WHITE 1.0", "price": 4500,
        "desc": "Лабораторные кристаллы. Чистота 99.1%. Стандарт 1g",
        "city": "Астрахань", "category": "crystal", "emoji": "❄️"
    },
    "crystal_3_ast": {
        "name": "❄️ CRYSTAL WHITE 3.0", "price": 12000,
        "desc": "Лабораторные кристаллы. Чистота 99.1%. Опт 3g",
        "city": "Астрахань", "category": "crystal", "emoji": "❄️"
    },
    "hydro_1_ast": {
        "name": "🥦 HYDRO GREEN 1.0", "price": 1500,
        "desc": "Гидропоника MYSTIC KUSH. 1g",
        "city": "Астрахань", "category": "hydro", "emoji": "🥦"
    },
    "hydro_3_ast": {
        "name": "🥦 HYDRO GREEN 3.0", "price": 4000,
        "desc": "Гидропоника MYSTIC KUSH. 3g",
        "city": "Астрахань", "category": "hydro", "emoji": "🥦"
    },
    "meow_05_ast": {
        "name": "🐱 MEOW ENERGY 0.5", "price": 2000,
        "desc": "Стимулятор. Формула M-21. Пробник 0.5g",
        "city": "Астрахань", "category": "meow", "emoji": "🐱"
    },
    "meow_1_ast": {
        "name": "🐱 MEOW ENERGY 1.0", "price": 3500,
        "desc": "Стимулятор. Формула M-21. Стандарт 1g",
        "city": "Астрахань", "category": "meow", "emoji": "🐱"
    },
    "mystic_mix": {
        "name": "🧬 MYSTIC MIX PACK", "price": 5000,
        "desc": "CRYSTAL 0.5 + MEOW 0.5 + HYDRO 1.0",
        "city": "Астрахань", "category": "hit", "emoji": "🧬"
    },
    "lab_pack": {
        "name": "🔬 LAB PACK PREMIUM", "price": 8000,
        "desc": "CRYSTAL 1.0 + MEOW 1.0 + PILLS x5",
        "city": "Астрахань", "category": "hit", "emoji": "🔬"
    },
    "crystal_05_kam": {
        "name": "❄️ CRYSTAL WHITE 0.5 (КМЗ)", "price": 2500,
        "desc": "Кристаллы 0.5g", "city": "Камызяк", "category": "crystal", "emoji": "❄️"
    },
    "hydro_1_kam": {
        "name": "🥦 HYDRO GREEN 1.0 (КМЗ)", "price": 1500,
        "desc": "Гидропоника 1g", "city": "Камызяк", "category": "hydro", "emoji": "🥦"
    },
    "meow_05_kam": {
        "name": "🐱 MEOW ENERGY 0.5 (КМЗ)", "price": 2000,
        "desc": "Стимулятор 0.5g", "city": "Камызяк", "category": "meow", "emoji": "🐱"
    },
}

SHOP_CATEGORIES = {
    "crystal": "❄️ CRYSTAL WHITE",
    "hydro": "🥦 HYDRO GREEN",
    "meow": "🐱 MEOW ENERGY",
    "hit": "🔥 MYSTIC HITS",
}

# ==================== ВАКАНСИИ ====================
JOB_POSITIONS = [
    {
        "title": "🧪 Лаборант (Химик)",
        "desc": "Производство продуктов в лаборатории. Опыт работы с хим. веществами обязателен.",
        "salary": "от 300 000 ₽/мес",
        "city": "Астрахань",
        "requirements": "Опыт работы в лаборатории от 1 года"
    },
    {
        "title": "📦 Кладмен",
        "desc": "Раскладка продуктов по кластерам. Работа с координатами.",
        "salary": "от 200 000 ₽/мес",
        "city": "Астрахань",
        "requirements": "Знание города, внимательность"
    },
    {
        "title": "📦 Кладмен",
        "desc": "Раскладка по городу. Гибкий график.",
        "salary": "от 150 000 ₽/мес",
        "city": "Камызяк",
        "requirements": "Знание города, без вредных привычек"
    },
    {
        "title": "💪 Спортивный (Охрана)",
        "desc": "Физическая охрана объектов и сотрудников. Спортивная подготовка.",
        "salary": "от 250 000 ₽/мес",
        "city": "Астрахань",
        "requirements": "Спортивный разряд, опыт в единоборствах"
    },
    {
        "title": "🏭 Складмен",
        "desc": "Приём, хранение и учёт продукции на складе.",
        "salary": "от 180 000 ₽/мес",
        "city": "Астрахань",
        "requirements": "Ответственность, пунктуальность"
    },
    {
        "title": "👑 Куратор",
        "desc": "Управление командой лаборантов и кладменов. Контроль качества.",
        "salary": "от 400 000 ₽/мес",
        "city": "Астрахань",
        "requirements": "Опыт управления от 2 лет"
    },
    {
        "title": "👑 Куратор (Камызяк)",
        "desc": "Развитие кластера в Камызяке. Набор и обучение персонала.",
        "salary": "от 350 000 ₽/мес",
        "city": "Камызяк",
        "requirements": "Опыт в подборе персонала"
    },
]

# ==================== ПЛАТЕЖИ ====================
CARD_NUMBER = '2200 7017 3078 1769'
BANK_NAME = 'Т-банк'
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '6593438966').split(',')]
CRYPTO_BOT_TOKEN = os.getenv('CRYPTO_BOT_TOKEN', '')

# ==================== ПРОМО И РЕФЕРАЛЫ ====================
REFERRAL_BONUS = 7
PROMO_CODES = {
    "WELCOME": {"discount": 20, "uses": 100},
    "VIP50": {"discount": 50, "uses": 50},
    "PREMIUM": {"discount": 30, "uses": 0},
}

# ==================== ДОСТИЖЕНИЯ И УРОВНИ ====================
ACHIEVEMENTS = {
    "first_payment": {"name": "Первый платёж", "emoji": "💎"},
    "five_friends": {"name": "5 друзей", "emoji": "🌟"},
    "ten_friends": {"name": "10 друзей", "emoji": "👑"},
    "hundred_requests": {"name": "100 запросов", "emoji": "🚀"},
}

LEVELS = {
    1: {"name": "Новичок", "emoji": "🟢", "xp": 0},
    2: {"name": "Пользователь", "emoji": "🔵", "xp": 100},
    3: {"name": "Продвинутый", "emoji": "🟣", "xp": 500},
    4: {"name": "Эксперт", "emoji": "🟡", "xp": 1000},
    5: {"name": "Легенда", "emoji": "🔴", "xp": 5000},
}

# ==================== ПРОЧЕЕ ====================
CHANNEL_USERNAME = "@your_channel"
CHANNEL_ID = -1001234567890
WEB_ADMIN_HOST = os.getenv('WEB_ADMIN_HOST', '0.0.0.0')
WEB_ADMIN_PORT = int(os.getenv('WEB_ADMIN_PORT', 8000))
