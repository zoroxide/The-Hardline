from fastapi import APIRouter, Request, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment

from app.controllers.auth_controller import AuthController

router = APIRouter(tags=["Authentication"])

def get_jinja_env(request: Request) -> Environment:
    return request.app.state.jinja_env

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = AuthController.get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)

    env = get_jinja_env(request)
    template = env.get_template("login.html")
    return HTMLResponse(template.render(error=None))

@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    if not AuthController.authenticate_credentials(username, password):
        env = get_jinja_env(request)
        template = env.get_template("login.html")
        return HTMLResponse(
            template.render(error="Invalid credentials or account access is restricted."),
            status_code=401
        )

    response = RedirectResponse(url="/", status_code=303)
    AuthController.set_auth_cookie(response, username.strip())
    return response

@router.post("/logout")
async def logout_post():
    response = RedirectResponse(url="/login", status_code=303)
    AuthController.clear_auth_cookie(response)
    return response

@router.get("/logout")
async def logout_get():
    response = RedirectResponse(url="/login", status_code=303)
    AuthController.clear_auth_cookie(response)
    return response
