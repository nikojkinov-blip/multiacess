from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from pathlib import Path

from web_admin.auth import verify_telegram_auth
from database.utils import get_stats, get_daily_stats
from database.models import PaymentModel

router = APIRouter(prefix="/stats", tags=["stats"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/")
async def statistics(
    request: Request,
    days: int = 30,
    user=Depends(verify_telegram_auth)
):
    """Страница статистики"""
    stats = get_stats()
    daily = get_daily_stats(days)
    payments = PaymentModel.get_all(limit=100)
    
    return templates.TemplateResponse("stats.html", {
        "request": request,
        "user": user,
        "stats": stats,
        "daily": daily,
        "payments": payments,
        "days": days
    })