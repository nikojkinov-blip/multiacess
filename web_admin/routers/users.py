from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pathlib import Path

from web_admin.auth import verify_telegram_auth
from database.models import UserModel, PaymentModel, BanModel
from config import ADMIN_IDS

router = APIRouter(prefix="/users", tags=["users"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/")
async def users_list(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    user=Depends(verify_telegram_auth)
):
    """Список пользователей"""
    offset = (page - 1) * limit
    
    if search:
        users = UserModel.search(search)
    else:
        users = UserModel.get_all(limit=limit, offset=offset)
    
    total = UserModel.count_all()
    pages = (total + limit - 1) // limit
    
    return templates.TemplateResponse("users.html", {
        "request": request,
        "user": user,
        "users": users,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
        "search": search
    })


@router.get("/{user_id}")
async def user_detail(
    request: Request,
    user_id: int,
    user=Depends(verify_telegram_auth)
):
    """Детальная информация о пользователе"""
    target = UserModel.get(user_id)
    if not target:
        return JSONResponse({"error": "User not found"}, status_code=404)
    
    payments = PaymentModel.get_by_user(user_id)
    is_banned = BanModel.is_banned(user_id)
    
    return templates.TemplateResponse("user_detail.html", {
        "request": request,
        "user": user,
        "target": target,
        "payments": payments,
        "is_banned": is_banned
    })


@router.post("/{user_id}/ban")
async def ban_user(
    request: Request,
    user_id: int,
    user=Depends(verify_telegram_auth)
):
    """Забанить пользователя"""
    data = await request.json()
    reason = data.get("reason", "Нарушение правил")
    
    BanModel.add(user_id, reason, int(user["id"]))
    return {"status": "ok", "message": f"User {user_id} banned"}


@router.post("/{user_id}/unban")
async def unban_user(user_id: int, user=Depends(verify_telegram_auth)):
    """Разбанить пользователя"""
    BanModel.remove(user_id)
    return {"status": "ok", "message": f"User {user_id} unbanned"}


@router.post("/{user_id}/set-premium")
async def set_premium(user_id: int, user=Depends(verify_telegram_auth)):
    """Выдать Premium"""
    UserModel.set_paid(user_id)
    return {"status": "ok", "message": f"Premium activated for {user_id}"}