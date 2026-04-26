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
    "obnal_samozanyat": {"name": "💳 Обнал через самозанятого", "price": 499, "desc": "Вывод до 500к/мес через СБП. Комиссия 3-4%", "category": "obnal"},
    "obnal_card": {"name": "💳 Обнал на карты физлиц", "price": 599, "desc": "Схема дробления платежей до 150к/день без блокировки", "category": "obnal"},
    "crypto_split": {"name": "₿ Крипто-сплит через P2P", "price": 599, "desc": "Разделение крипты на 10+ кошельков без KYC", "category": "crypto"},
    "crypto_nft": {"name": "₿ Отмыв через NFT", "price": 999, "desc": "Грязная крипта → NFT → чистая крипта. Полный цикл", "category": "crypto"},
    "drop_card": {"name": "🏢 Карта дропа удалённо", "price": 799, "desc": "Оформление дебетовки на дропа. Сим-карта + доступ в банк", "category": "drop"},
    "drop_ip": {"name": "🏢 ИП на дропа под ключ", "price": 1499, "desc": "ИП + счёт + ЭЦП. Полный пакет за 3 дня", "category": "drop"},
    "return_wb": {"name": "📊 Возврат на Wildberries", "price": 399, "desc": "Схема возврата товара без отправки обратно", "category": "return"},
    "return_ozon": {"name": "📊 Возврат на Ozon", "price": 399, "desc": "100% возврат средств за любой товар", "category": "return"},
}

CASH_CATEGORIES = {"obnal": "💳 Обнал", "crypto": "₿ Крипта", "drop": "🏢 Дропы", "return": "📊 Возвраты"}

# ==================== FRAGMENT COLLECTION ====================
FRAGMENT_BRAND = "📛 FRAGMENT COLLECTION"
FRAGMENT_SLOGAN = "Коллекционные Telegram-юзернеймы"

FRAGMENT_ITEMS = {
    "idrub": {"name": "@idrub", "price": 599, "available": True},
    "automatedconstruction": {"name": "@automatedconstruction", "price": 499, "available": True},
    "endyma": {"name": "@endyma", "price": 549, "available": True},
    "youngviperr": {"name": "@youngviperr", "price": 699, "available": True},
    "sunderwise": {"name": "@sunderwise", "price": 599, "available": True},
    "strainedly": {"name": "@strainedly", "price": 499, "available": True},
    "laceondrugs": {"name": "@laceondrugs", "price": 899, "available": True},
    "zobivnoi": {"name": "@zobivnoi", "price": 649, "available": True},
    "fsbsuck": {"name": "@fsbsuck", "price": 899, "available": True},
    "obckamil": {"name": "@obckamil", "price": 549, "available": True},
}

# ==================== ПЛАТЕЖИ ====================
CARD_NUMBER = '2200 7017 3078 1769'
BANK_NAME = 'Т-БАНК'
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
