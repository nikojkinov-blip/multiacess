import aiohttp
from config import BOT_TOKEN, ADMIN_IDS


async def notify_admins(bot, message: str):
    """Уведомить всех админов"""
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, message, parse_mode="HTML")
        except:
            pass


async def notify_user(bot, user_id: int, message: str):
    """Уведомить пользователя"""
    try:
        await bot.send_message(user_id, message, parse_mode="HTML")
        return True
    except:
        return False


async def send_log_to_channel(bot, channel_id: int, message: str):
    """Отправить лог в канал"""
    try:
        await bot.send_message(channel_id, message, parse_mode="HTML")
    except:
        pass