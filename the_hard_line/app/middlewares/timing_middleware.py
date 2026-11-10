import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware that measures total HTTP request processing duration."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        t0 = time.time()
        response = await call_next(request)
        process_time = (time.time() - t0) * 1000
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        return response
