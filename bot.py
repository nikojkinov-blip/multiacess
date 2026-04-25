#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import sys
import threading
import json
import uuid
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import BOT_TOKEN, ADMIN_IDS, ACHIEVEMENTS, LEVELS
from database.models import init_database, UserModel, SimModel
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
from services.level_system import LevelSystem

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# ==================== API СЕРВЕР ====================
app = FastAPI(title="AI Access Bot API", version="4.0",
              description="API для WebApp и админки")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    return {"status": "ok", "bot": "running", "version": "4.0"}

@app.get("/health")
async def health():
    return {"status": "alive", "timestamp": datetime.now().isoformat()}

@app.get("/api/profile")
async def api_profile(user_id: int = Query(...)):
    user = UserModel.get(user_id)
    if not user:
        return {"error": "User not found"}
    progress = LevelSystem.get_progress(user_id)
    achievements = json.loads(user.get('achievements', '[]'))
    ach_list = []
    for ach_key in achievements:
        ach = ACHIEVEMENTS.get(ach_key, {})
        if ach: ach_list.append({"key": ach_key, "name": ach["name"], "emoji": ach["emoji"]})
    level_data = LEVELS.get(user.get('level', 1), LEVELS[1])
    return {
        "user_id": user_id, "username": user.get('username', ''),
        "first_name": user.get('first_name', ''),
        "total_requests": user.get('total_requests', 0),
        "level": user.get('level', 1), "level_name": level_data["name"],
        "level_emoji": level_data["emoji"], "experience": user.get('experience', 0),
        "xp_percent": progress.get('percent', 0), "next_xp": progress.get('next_xp', 100),
        "ai_premium": UserModel.is_ai_premium(user_id),
        "sim_premium": UserModel.is_sim_premium(user_id),
        "trial_active": bool(user.get('trial_until')),
        "achievements": ach_list, "referral_bonus": user.get('referral_bonus', 0)
    }

@app.get("/api/keys")
async def api_keys(user_id: int = Query(...)):
    user = UserModel.get(user_id)
    if not user: return {"error": "User not found"}
    return {"keys": json.loads(user.get('api_keys', '[]'))}

@app.get("/api/sim-orders")
async def api_sim_orders(user_id: int = Query(...)):
    return {"orders": SimModel.get_user_orders(user_id)}

@app.get("/api/new-key")
async def api_new_key(user_id: int = Query(...)):
    user = UserModel.get(user_id)
    if not user: return {"error": "User not found"}
    if not UserModel.is_ai_premium(user_id): return {"error": "No AI Premium"}
    keys = json.loads(user.get('api_keys', '[]'))
    new_key = f"sk-pro-{uuid.uuid4().hex[:24]}"
    keys.append(new_key)
    UserModel.update(user_id, {'api_keys': json.dumps(keys)})
    return {"key": new_key, "all_keys": keys}

def run_web_server():
    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="error")

# ==================== ФОНОВЫЕ ЗАДАЧИ ====================
async def background_tasks(bot: Bot):
    while True:
        try:
            pending = AutoBroadcast.get_pending()
            for broadcast in pending:
                await AutoBroadcast.send_broadcast(bot, broadcast)
        except Exception as e:
            logger.error(f"Background error: {e}")
        await asyncio.sleep(3600)

# ==================== ЗАПУСК БОТА ====================
async def main():
    init_database()
    session = AiohttpSession()
    bot = Bot(token=BOT_TOKEN, session=session,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.message.middleware(ThrottlingMiddleware(rate_limit=5))
    dp.message.middleware(BanCheckMiddleware())
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware(rate_limit=10))
    dp.callback_query.middleware(BanCheckMiddleware())
    dp.include_router(admin_router)
    dp.include_router(common_router)
    dp.include_router(payment_router)
    dp.include_router(support_router)
    dp.include_router(ai_router)
    dp.include_router(webapp_router)
    logger.info("🚀 Бот запущен! API на порту 10000")
    for admin_id in ADMIN_IDS:
        try: await bot.send_message(admin_id, "🟢 Бот запущен на Render!")
        except: pass
    asyncio.create_task(background_tasks(bot))
    await dp.start_polling(bot)

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    asyncio.run(main())
