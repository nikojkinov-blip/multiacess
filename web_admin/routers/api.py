from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from web_admin.auth import verify_api_key
from database.utils import get_stats, get_daily_stats, backup_database, export_users_to_csv
from database.models import UserModel, PaymentModel, TicketModel, BanModel

router = APIRouter(prefix="/api", tags=["api"])


class BanRequest(BaseModel):
    user_id: int
    reason: str = "Нарушение правил"


class BroadcastRequest(BaseModel):
    message: str
    target: str = "all"


@router.get("/stats")
async def api_stats(api_key: bool = Depends(verify_api_key)):
    """Получить статистику"""
    return get_stats()


@router.get("/stats/daily")
async def api_daily_stats(days: int = 7, api_key: bool = Depends(verify_api_key)):
    """Статистика по дням"""
    return get_daily_stats(days)


@router.get("/users")
async def api_users(
    page: int = 1,
    limit: int = 50,
    api_key: bool = Depends(verify_api_key)
):
    """Список пользователей"""
    offset = (page - 1) * limit
    users = UserModel.get_all(limit=limit, offset=offset)
    total = UserModel.count_all()
    
    return {
        "users": users,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit
    }


@router.get("/users/{user_id}")
async def api_user_detail(user_id: int, api_key: bool = Depends(verify_api_key)):
    """Информация о пользователе"""
    user = UserModel.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    payments = PaymentModel.get_by_user(user_id)
    return {"user": user, "payments": payments}


@router.post("/ban")
async def api_ban(request: BanRequest, api_key: bool = Depends(verify_api_key)):
    """Забанить пользователя"""
    BanModel.add(request.user_id, request.reason, 0)
    return {"status": "ok", "user_id": request.user_id}


@router.post("/unban/{user_id}")
async def api_unban(user_id: int, api_key: bool = Depends(verify_api_key)):
    """Разбанить пользователя"""
    BanModel.remove(user_id)
    return {"status": "ok", "user_id": user_id}


@router.get("/payments")
async def api_payments(
    page: int = 1,
    limit: int = 50,
    api_key: bool = Depends(verify_api_key)
):
    """Список платежей"""
    payments = PaymentModel.get_all(limit=limit)
    return {"payments": payments, "page": page}


@router.get("/tickets")
async def api_tickets(api_key: bool = Depends(verify_api_key)):
    """Открытые тикеты"""
    tickets = TicketModel.get_all_open()
    return {"tickets": tickets, "count": len(tickets)}


@router.get("/backup")
async def api_backup(api_key: bool = Depends(verify_api_key)):
    """Создать бэкап"""
    path = backup_database()
    return {"status": "ok", "path": path}


@router.get("/export/users")
async def api_export_users(api_key: bool = Depends(verify_api_key)):
    """Экспорт пользователей"""
    path = export_users_to_csv()
    return {"status": "ok", "path": path}


@router.post("/broadcast")
async def api_broadcast(
    request: BroadcastRequest,
    api_key: bool = Depends(verify_api_key)
):
    """Массовая рассылка"""
    # Здесь логика рассылки
    return {"status": "ok", "message": "Broadcast started", "target": request.target}