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
from middlewares.ban_middleware import BanCheckMiddleware
from middlewares.logging_mw import LoggingMiddleware
from handlers.common import router as common_router
from handlers.payment import router as payment_router
from handlers.support import router as support_router
from handlers.ai_chat import router as ai_router
from handlers.admin import router as admin_router
from handlers.webapp import router as webapp_router
from handlers.cash import router as cash_router
from handlers.fragment import router as fragment_router
from services.auto_broadcast import AutoBroadcast
from services.level_system import LevelSystem

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# ==================== API ====================
app = FastAPI(title="MultiAcces API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root(): return {"status": "ok"}

@app.get("/health")
async def health(): return {"status": "alive", "timestamp": datetime.now().isoformat()}

@app.get("/api/profile")
async def api_profile(user_id: int = Query(...)):
    user = UserModel.get(user_id)
    if not user: return {"error": "Not found"}
    progress = LevelSystem.get_progress(user_id)
    achievements = json.loads(user.get('achievements','[]'))
    ach_list = []
    for k in achievements:
        a = ACHIEVEMENTS.get(k, {})
        if a: ach_list.append({"key": k, "name": a["name"], "emoji": a["emoji"]})
    lvl = LEVELS.get(user.get('level',1), LEVELS[1])
    return {
        "user_id": user_id, "username": user.get('username',''),
        "first_name": user.get('first_name',''), "total_requests": user.get('total_requests',0),
        "level": user.get('level',1), "level_name": lvl["name"], "level_emoji": lvl["emoji"],
        "experience": user.get('experience',0), "xp_percent": progress.get('percent',0),
        "next_xp": progress.get('next_xp',100), "ai_premium": UserModel.is_ai_premium(user_id),
        "sim_premium": UserModel.is_sim_premium(user_id),
        "trial_active": bool(user.get('trial_until')),
        "achievements": ach_list, "referral_bonus": user.get('referral_bonus',0)
    }

@app.get("/api/keys")
async def api_keys(user_id: int = Query(...)):
    user = UserModel.get(user_id)
    if not user: return {"error": "Not found"}
    return {"keys": json.loads(user.get('api_keys','[]'))}

@app.get("/api/sim-orders")
async def api_sim_orders(user_id: int = Query(...)):
    return {"orders": SimModel.get_user_orders(user_id)}

@app.get("/api/new-key")
async def api_new_key(user_id: int = Query(...)):
    user = UserModel.get(user_id)
    if not user: return {"error": "Not found"}
    if not UserModel.is_ai_premium(user_id): return {"error": "No premium"}
    keys = json.loads(user.get('api_keys','[]'))
    new_key = f"sk-pro-{uuid.uuid4().hex[:24]}"
    keys.append(new_key)
    UserModel.update(user_id, {'api_keys': json.dumps(keys)})
    return {"key": new_key, "all_keys": keys}

def run_web(): uvicorn.run(app, host="0.0.0.0", port=10000, log_level="error")

# ==================== MAIN ====================
async def main():
    init_database()
    bot = Bot(token=BOT_TOKEN, session=AiohttpSession(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(BanCheckMiddleware())
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(BanCheckMiddleware())
    dp.include_router(admin_router)
    dp.include_router(common_router)
    dp.include_router(payment_router)
    dp.include_router(support_router)
    dp.include_router(ai_router)
    dp.include_router(webapp_router)
    dp.include_router(cash_router)
    dp.include_router(fragment_router)
    logger.info("🚀 MultiAcces запущен!")
    for aid in ADMIN_IDS:
        try: await bot.send_message(aid, "🟢 Бот запущен!")
        except: pass
    await dp.start_polling(bot)

if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    asyncio.run(main())
