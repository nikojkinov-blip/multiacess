import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_PATH = os.getenv('DB_PATH', 'database/bot.db')

# Цены
AI_PAYMENT_AMOUNT = 49
SIM_PAYMENT_AMOUNT = 299

# Подписки (дни: цена)
AI_SUBSCRIPTIONS = {
    30: 49,
    90: 99,
    365: 299
}

SIM_SUBSCRIPTIONS = {
    30: 299,
    90: 599,
    365: 1499
}

CARD_NUMBER = '+79931173324 или 2200 7017 3078 1769'
BANK_NAME = 'T-bank'

ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '6593438966').split(',')]

CRYPTO_BOT_TOKEN = os.getenv('CRYPTO_BOT_TOKEN', '')

AI_TRIAL_DAYS = 3
REFERRAL_BONUS = 7
MAX_REQUESTS_PER_DAY_FREE = 5
MAX_REQUESTS_PER_DAY_PAID = 50

CHANNEL_USERNAME = "@MultiAcess"
CHANNEL_ID = -1003715251901

PROMO_CODES = {
    "WELCOME": {"discount": 20, "uses": 100},
    "VIP50": {"discount": 50, "uses": 50},
    "PREMIUM": {"discount": 30, "uses": 0},
}

ACHIEVEMENTS = {
    "first_payment": {"name": "Первый платёж", "emoji": "💎"},
    "five_friends": {"name": "5 друзей", "emoji": "🌟"},
    "ten_friends": {"name": "10 друзей", "emoji": "👑"},
    "hundred_requests": {"name": "100 запросов", "emoji": "🚀"},
    "week_active": {"name": "Неделя активности", "emoji": "⚡"},
}

LEVELS = {
    1: {"name": "Новичок", "emoji": "🟢", "xp": 0},
    2: {"name": "Пользователь", "emoji": "🔵", "xp": 100},
    3: {"name": "Продвинутый", "emoji": "🟣", "xp": 500},
    4: {"name": "Эксперт", "emoji": "🟡", "xp": 1000},
    5: {"name": "Легенда", "emoji": "🔴", "xp": 5000},
}

SIM_OPERATORS = ["Билайн", "Мегафон", "МТС", "Tele2"]
SIM_REGIONS = ["Москва", "СПб", "Казань", "Екатеринбург", "Новосибирск"]
SIM_TARIFFS = ["Доверенное лицо", "Корпоративный", "Самозанятый"]

WEB_ADMIN_HOST = os.getenv('WEB_ADMIN_HOST', '0.0.0.0')
WEB_ADMIN_PORT = int(os.getenv('WEB_ADMIN_PORT', 8000))
