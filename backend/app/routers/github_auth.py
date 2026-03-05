from fastapi import APIRouter, Request
from app.auth.github_oauth import oauth

router = APIRouter(prefix="/auth", tags=["github"])


@router.get("/github/login")
async def login_via_github(request: Request):
    redirect_uri = request.url_for("github_callback")
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/github/callback")
async def github_callback(request: Request):
    token = await oauth.github.authorize_access_token(request)
    user = await oauth.github.get("user", token=token)
    return user.json()