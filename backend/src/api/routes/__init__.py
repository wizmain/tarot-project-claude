"""
API Routes package
"""
from src.api.routes.cards import router as cards_router
from src.api.routes.readings import router as readings_router
from src.api.routes.auth import router as auth_router
from src.api.routes.feedback import router as feedback_router
from src.api.routes.admin import router as admin_router

__all__ = ["cards_router", "readings_router", "auth_router", "feedback_router", "admin_router"]
