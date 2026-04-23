from typing import Any, Awaitable, Callable, Dict
from cachetools import TTLCache
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: int = 5):
        self.cache = TTLCache(maxsize=10000, ttl=60)
        self.rate_limit = rate_limit
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        
        current_count = self.cache.get(user_id, 0)
        if current_count >= self.rate_limit:
            if isinstance(event, Message):
                await event.answer("⚠️ Слишком много запросов. Подождите минуту.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⚠️ Слишком много действий. Подождите.", show_alert=True)
            return
        
        self.cache[user_id] = current_count + 1
        
        return await handler(event, data)