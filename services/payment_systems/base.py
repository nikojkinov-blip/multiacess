from abc import ABC, abstractmethod
from typing import Optional, Dict

class BasePaymentSystem(ABC):
    @abstractmethod
    async def create_invoice(self, amount: float, order_id: str) -> Optional[Dict]:
        pass
    
    @abstractmethod
    async def check_invoice(self, invoice_id: str) -> Optional[str]:
        pass
    
    @abstractmethod
    async def cancel_invoice(self, invoice_id: str) -> bool:
        pass