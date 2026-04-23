from functools import wraps
from typing import Callable
from aiogram.types import Message, CallbackQuery
from config import ADMIN_IDS
from database.models import UserModel

def admin_only(func: Callable):
    @wraps(func)
    async def wrapper(event: Message | CallbackQuery, *args, **kwargs):
        user_id = event.from_user.id
        if user_id not in ADMIN_IDS:
            if isinstance(event, Message):
                await event.answer("❌ У вас нет доступа к этой команде.")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ Нет доступа", show_alert=True)
            return
        return await func(event, *args, **kwargs)
    return wrapper

def premium_only(func: Callable):
    @wraps(func)
    async def wrapper(event: Message | CallbackQuery, *args, **kwargs):
        user_id = event.from_user.id
        if not UserModel.is_premium(user_id) and user_id not in ADMIN_IDS:
            if isinstance(event, Message):
                await event.answer(
                    "❌ Эта функция доступна только Premium пользователям.\n"
                    "Используйте /start для получения доступа."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ Только для Premium", show_alert=True)
            return
        return await func(event, *args, **kwargs)
    return wrapper