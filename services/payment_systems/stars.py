from typing import Optional, Dict


class TelegramStarsPayment:
    """Оплата через Telegram Stars"""
    
    @classmethod
    async def create_invoice(cls, amount: float, order_id: str, title: str = "AI Access Bot") -> Optional[Dict]:
        """Создать счёт для оплаты звёздами"""
        return {
            "title": f"{title} - Premium доступ",
            "description": "Доступ к ChatGPT, Claude, Midjourney на 30 дней",
            "payload": f"premium_{order_id}",
            "currency": "XTR",
            "prices": [{"label": "Premium доступ", "amount": int(amount)}]
        }
    
    @classmethod
    async def check_invoice(cls, invoice_id: str) -> Optional[str]:
        """Проверить статус оплаты"""
        return "paid"
    
    @classmethod
    async def cancel_invoice(cls, invoice_id: str) -> bool:
        """Отменить счёт"""
        return True