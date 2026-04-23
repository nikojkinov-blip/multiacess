#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp_socks import ProxyConnector
from datetime import datetime

from config import BOT_TOKEN, ADMIN_IDS
from database.core import Database
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
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def background_tasks(bot: Bot):
    """Фоновые задачи"""
    while True:
        try:
            # Проверка подписок
            users = UserModel.check_subscription_ending()
            for user in users:
                try:
                    await bot.send_message(
                        user['user_id'],
                        "⚠️ <b>Подписка истекает завтра!</b>\n"
                        "Продлите: /start",
                        parse_mode="HTML"
                    )
                except:
                    pass
            
            # Авторассылки по расписанию
            pending = AutoBroadcast.get_pending()
            for broadcast in pending:
                sent, failed = await AutoBroadcast.send_broadcast(bot, broadcast)
                logger.info(f"Broadcast {broadcast['id']}: sent={sent}, failed={failed}")
            
            # Проверка достижений
            active_users = db.fetchall(
                "SELECT user_id FROM users WHERE last_activity >= datetime('now', '-1 day')"
            )
            for user in active_users:
                new_ach = AchievementSystem.check_and_award(user['user_id'])
                if new_ach:
                    for ach_key in new_ach:
                        ach = AchievementSystem.get_achievement_info(ach_key)
                        try:
                            await bot.send_message(
                                user['user_id'],
                                f"{ach['emoji']} <b>Новое достижение!</b>\n{ach['name']}",
                                parse_mode="HTML"
                            )
                        except:
                            pass
            
        except Exception as e:
            logger.error(f"Background error: {e}")
        
        await asyncio.sleep(3600)  # Раз в час


async def main():
    init_database()
    
    # Прокси
    try:
        connector = ProxyConnector.from_url('socks5://127.0.0.1:9150')
        session = AiohttpSession(connector=connector)
    except:
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
    
    logger.info("Бот запущен!")
    
    # Фоновые задачи
    asyncio.create_task(background_tasks(bot))
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "🟢 Бот запущен!")
        except:
            pass
    
    await dp.start_polling(bot)


if __name__ == '__main__':
    # Импорт db здесь чтобы избежать циклического импорта
    from database.models import db
    asyncio.run(main())