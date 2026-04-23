from fastapi import Request, Depends
from database.core import db
from .auth import verify_telegram_auth


def get_db():
    """Получить соединение с БД"""
    return db


async def get_current_user(request: Request):
    """Получить текущего пользователя из сессии"""
    return getattr(request.state, "user", None)


# Декоратор для проверки админа
def admin_required():
    return Depends(verify_telegram_auth)