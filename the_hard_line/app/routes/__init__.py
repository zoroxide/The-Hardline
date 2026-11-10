from app.routes.auth_routes import router as auth_router
from app.routes.search_routes import router as search_router
from app.routes.health_routes import router as health_router

__all__ = ["auth_router", "search_router", "health_router"]
