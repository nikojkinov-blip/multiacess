import hashlib
import hmac
from datetime import datetime
from fastapi import Request, HTTPException, Depends
from fastapi.security import APIKeyHeader
from config import BOT_TOKEN, ADMIN_IDS

# Для API авторизации
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_telegram_auth(request: Request):
    """Проверка данных от Telegram Login Widget"""
    auth_data = dict(request.query_params)
    
    if not auth_data:
        # Пробуем получить из куки
        user_id = request.cookies.get("user_id")
        if user_id and int(user_id) in ADMIN_IDS:
            return {"id": user_id, "is_admin": True}
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Проверяем hash
    received_hash = auth_data.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Missing hash")
    
    # Сортируем и создаём строку для проверки
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(auth_data.items()))
    
    # Вычисляем секретный ключ
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    if calculated_hash != received_hash:
        raise HTTPException(status_code=401, detail="Invalid hash")
    
    # Проверяем время (не старше 24 часов)
    auth_date = int(auth_data.get("auth_date", 0))
    if datetime.now().timestamp() - auth_date > 86400:
        raise HTTPException(status_code=401, detail="Auth data expired")
    
    user_id = int(auth_data["id"])
    if user_id not in ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": user_id,
        "first_name": auth_data.get("first_name", ""),
        "username": auth_data.get("username", ""),
        "photo_url": auth_data.get("photo_url", ""),
        "is_admin": True
    }


async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Проверка API ключа"""
    if api_key != "your_secret_api_key":  # Замени на свой ключ
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True