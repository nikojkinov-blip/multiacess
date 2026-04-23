import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from datetime import datetime

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if isinstance(event, Message):
            content = event.text or "[media]"
            logger.info(f"[{timestamp}] User {user.id} (@{user.username}): {content[:100]}")
        elif isinstance(event, CallbackQuery):
            logger.info(f"[{timestamp}] User {user.id} (@{user.username}) callback: {event.data}")
        
        return await handler(event, data)