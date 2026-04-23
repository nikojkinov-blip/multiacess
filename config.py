import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_PATH = 'database/bot.db'

# AI Access цены
AI_PAYMENT_AMOUNT = 49
AI_TRIAL_DAYS = 3

# SIM.DL цены
SIM_PAYMENT_AMOUNT = 299

CARD_NUMBER = '+79931173324'
BANK_NAME = 'Т-банк'

ADMIN_IDS = [6593438966]

CRYPTO_BOT_TOKEN = os.getenv('CRYPTO_BOT_TOKEN', '')

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
}

SIM_OPERATORS = ["Билайн", "Мегафон", "МТС", "Tele2"]
SIM_REGIONS = ["Москва", "СПб", "Казань", "Екатеринбург", "Новосибирск"]
SIM_TARIFFS = ["Доверенное лицо", "Корпоративный", "Самозанятый"]

WEB_ADMIN_HOST = os.getenv('WEB_ADMIN_HOST', '127.0.0.1')
WEB_ADMIN_PORT = int(os.getenv('WEB_ADMIN_PORT', 8000))