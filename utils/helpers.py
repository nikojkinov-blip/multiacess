import html
from typing import Optional
from aiogram.types import User

def format_number(num: int) -> str:
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)

def get_user_mention(user: User) -> str:
    if user.username:
        return f"@{user.username}"
    return f"<a href='tg://user?id={user.id}'>{html.escape(user.first_name)}</a>"

def escape_html(text: str) -> str:
    return html.escape(str(text))

def truncate_text(text: str, max_length: int = 100) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def parse_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} сек"
    elif seconds < 3600:
        return f"{seconds//60} мин"
    elif seconds < 86400:
        return f"{seconds//3600} ч"
    return f"{seconds//86400} дн"

def get_progress_bar(current: int, total: int, length: int = 10) -> str:
    filled = int(length * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {current}/{total}"