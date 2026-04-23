from .common import router as common_router
from .payment import router as payment_router
from .support import router as support_router
from .ai_chat import router as ai_router
from .admin import router as admin_router

__all__ = [
    'common_router',
    'payment_router', 
    'support_router',
    'ai_router',
    'admin_router'
]