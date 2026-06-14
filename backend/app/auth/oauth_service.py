from sqlalchemy.orm import Session

from app.auth.token_vault import decrypt_token
from app.models.oauth_token import OAuthToken


def get_user_github_token(user_id, db: Session) -> str | None:
    row = (
        db.query(OAuthToken)
        .filter(OAuthToken.user_id == user_id, OAuthToken.provider == "github")
        .first()
    )
    if not row:
        return None
    return decrypt_token(row.encrypted_access_token)
