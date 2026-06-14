from sqlalchemy.orm import Session

from app.models.user import User


def find_or_create_github_user(db: Session, github_id: str, email: str | None) -> User:
    user = db.query(User).filter(User.github_id == github_id).first()
    if user:
        return user

    if email:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.github_id = github_id
            db.commit()
            db.refresh(user)
            return user

    if not email:
        raise ValueError("github_no_email")

    user = User(email=email, github_id=github_id, hashed_password=None)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
