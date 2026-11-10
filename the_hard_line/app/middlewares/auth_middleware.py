from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse, JSONResponse

from app.controllers.auth_controller import AuthController

PUBLIC_PATHS = {
    "/login",
    "/logout",
    "/healthz",
    "/favicon.ico"
}

class SessionAuthMiddleware(BaseHTTPMiddleware):
    """Middleware validating user session cookies on protected endpoints."""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Allow public and static assets without session check
        if path in PUBLIC_PATHS or path.startswith("/static"):
            return await call_next(request)

        user = AuthController.get_current_user(request)

        if not user:
            # For JSON API calls, return 401 Unauthorized
            if path.startswith("/api/"):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required. Please log in."}
                )
            # For browser HTML views, redirect to login page
            return RedirectResponse(url="/login", status_code=302)

        # Store authenticated user in request state for downstream handlers
        request.state.user = user
        return await call_next(request)
