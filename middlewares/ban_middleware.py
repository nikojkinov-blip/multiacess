from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from database.models import BanModel

class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        
        if BanModel.is_banned(user_id):
            if isinstance(event, Message) and event.text:
                if event.text.startswith('/'):
                    await event.answer("🚫 Вы заблокированы в этом боте.")
            elif isinstance(event, CallbackQuery):
                await event.answer("🚫 Вы заблокированы.", show_alert=True)
            return
        
        return await handler(event, data)