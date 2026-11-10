import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from app.config import TEMPLATES_DIR, STATIC_DIR
from app.database import init_db_pool, close_db_pool
from app.middlewares import SessionAuthMiddleware, TimingMiddleware
from app.routes import auth_router, search_router, health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan: setup and teardown resources."""
    await init_db_pool()
    yield
    await close_db_pool()

def create_application() -> FastAPI:
    """Application factory configuring routes, middlewares, and templates."""
    app = FastAPI(
        title="The Hardline",
        description="High-performance Egyptian user intelligence directory (45M+ records)",
        version="2.0.0",
        lifespan=lifespan
    )

    # 1. Initialize Jinja2 Templates Environment
    if not os.path.exists(TEMPLATES_DIR):
        raise RuntimeError(f"Templates directory not found: {TEMPLATES_DIR}")
    app.state.jinja_env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True
    )

    # 2. Register Global Middlewares
    app.add_middleware(TimingMiddleware)
    app.add_middleware(SessionAuthMiddleware)

    # 3. Mount Static Files
    if os.path.exists(STATIC_DIR):
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # 4. Include Modular Routers
    app.include_router(auth_router)
    app.include_router(search_router)
    app.include_router(health_router)

    return app

app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=6969, reload=True)
