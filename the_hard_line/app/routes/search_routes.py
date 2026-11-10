from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from jinja2 import Environment

from app.controllers.auth_controller import AuthController
from app.controllers.search_controller import SearchController
from app.models.user import SearchResponse

router = APIRouter(tags=["Search & Dashboard"])

def get_jinja_env(request: Request) -> Environment:
    return request.app.state.jinja_env

@router.get("/", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    user = getattr(request.state, "user", None) or AuthController.get_current_user(request)
    if not user:
        return HTMLResponse(status_code=302, headers={"Location": "/login"})

    env = get_jinja_env(request)
    template = env.get_template("dashboard.html")
    return HTMLResponse(template.render(username=user.username))

@router.get("/api/search", response_model=SearchResponse)
async def search_api(
    request: Request,
    q: str = Query(..., min_length=1, max_length=500, description="Search query string or Facebook profile URL"),
    mode: str = Query("url", regex="^(url|auto|fbid|phone|name)$", description="Search mode")
):
    try:
        return await SearchController.execute_search(q, mode)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search execution failed: {str(exc)}")
