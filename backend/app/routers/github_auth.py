import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.github_oauth import oauth
from app.auth.github_user import find_or_create_github_user
from app.auth.token_vault import encrypt_token
from app.auth.utils import create_access_token
from app.database import get_db
from app.models.oauth_token import OAuthToken

router = APIRouter(prefix="/auth", tags=["github"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


async def _get_github_profile(token) -> dict:
    resp = await oauth.github.get("user", token=token)
    profile = resp.json()

    if not profile.get("email"):
        emails_resp = await oauth.github.get("user/emails", token=token)
        emails = emails_resp.json()
        for entry in emails:
            if entry.get("primary") and entry.get("verified"):
                profile["email"] = entry["email"]
                break
        if not profile.get("email") and emails:
            profile["email"] = emails[0].get("email")

    return profile


@router.get("/github/login")
async def login_via_github(request: Request):
    redirect_uri = request.url_for("github_callback")
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/github/callback", name="github_callback")
async def github_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.github.authorize_access_token(request)
        profile = await _get_github_profile(token)
    except Exception:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=github_auth_failed")

    github_id = str(profile["id"])
    email = profile.get("email")

    try:
        user = find_or_create_github_user(db, github_id, email)
    except ValueError:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=github_no_email")

    access_token = token.get("access_token")
    if access_token:
        existing = db.query(OAuthToken).filter(
            OAuthToken.user_id == user.id,
            OAuthToken.provider == "github",
        ).first()
        encrypted = encrypt_token(access_token)
        if existing:
            existing.encrypted_access_token = encrypted
        else:
            db.add(OAuthToken(user_id=user.id, provider="github", encrypted_access_token=encrypted))
        db.commit()

    jwt = create_access_token({"sub": str(user.id)})
    return RedirectResponse(f"{FRONTEND_URL}/auth/callback?token={jwt}")
