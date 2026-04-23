from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime

from web_admin.auth import verify_telegram_auth
from database.utils import get_stats, get_daily_stats
from database.models import UserModel, PaymentModel, TicketModel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/")
async def dashboard(request: Request, user=Depends(verify_telegram_auth)):
    """Главная страница админки"""
    stats = get_stats()
    daily = get_daily_stats(7)
    
    # Последние пользователи
    recent_users = UserModel.get_all(limit=10)
    
    # Последние платежи
    recent_payments = PaymentModel.get_all(limit=10)
    
    # Открытые тикеты
    open_tickets = TicketModel.get_all_open()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "stats": stats,
        "daily": daily,
        "recent_users": recent_users,
        "recent_payments": recent_payments,
        "open_tickets": open_tickets,
        "current_time": datetime.now()
    })