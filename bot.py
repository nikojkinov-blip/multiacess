#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import sys
import threading
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from fastapi import FastAPI
import uvicorn

from config import BOT_TOKEN, ADMIN_IDS
from database.models import init_database, UserModel
from middlewares.throttling import ThrottlingMiddleware
from middlewares.ban_middleware import BanCheckMiddleware
from middlewares.logging_mw import LoggingMiddleware

from handlers.common import router as common_router
from handlers.payment import router as payment_router
from handlers.support import router as support_router
from handlers.ai_chat import router as ai_router
from handlers.admin import router as admin_router
from handlers.webapp import router as webapp_router

from services.auto_broadcast import AutoBroadcast
from services.achievements import AchievementSystem

sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============== ВЕБ-СЕРВЕР ==============
app = FastAPI(title="AI Access Bot")


@app.get("/")
async def root():
    return {"status": "ok", "bot": "running", "service": "ai-access-bot"}


@app.get("/health")
async def health():
    return {"status": "alive", "timestamp": __import__('datetime').datetime.now().isoformat()}


def run_web_server():
    """Запуск веб-сервера в отдельном потоке"""
    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="error")


# ============== ФОНОВЫЕ ЗАДАЧИ ==============
async def background_tasks(bot: Bot):
    """Фоновые задачи"""
    while True:
        try:
            # Авторассылки по расписанию
            pending = AutoBroadcast.get_pending()
            for broadcast in pending:
                sent, failed = await AutoBroadcast.send_broadcast(bot, broadcast)
                logger.info(f"Broadcast {broadcast['id']}: sent={sent}, failed={failed}")

        except Exception as e:
            logger.error(f"Background error: {e}")

        await asyncio.sleep(3600)


# ============== ЗАПУСК БОТА ==============
async def main():
    # Инициализация БД
    init_database()

    # Создание бота
    session = AiohttpSession()
    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Middlewares
    dp.message.middleware(ThrottlingMiddleware(rate_limit=5))
    dp.message.middleware(BanCheckMiddleware())
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware(rate_limit=10))
    dp.callback_query.middleware(BanCheckMiddleware())

    # Роутеры
    dp.include_router(admin_router)
    dp.include_router(common_router)
    dp.include_router(payment_router)
    dp.include_router(support_router)
    dp.include_router(ai_router)
    dp.include_router(webapp_router)

    logger.info("Бот запущен! Порт 10000 слушает.")

    # Уведомление админам
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "🟢 Бот запущен на Render!")
        except:
            pass

    # Фоновые задачи
    asyncio.create_task(background_tasks(bot))

    # Запуск бота
    await dp.start_polling(bot)


if __name__ == '__main__':
    # Запуск веб-сервера в отдельном потоке
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Запуск бота
    asyncio.run(main())
