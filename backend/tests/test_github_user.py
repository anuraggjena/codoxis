import uuid

from app.auth.github_user import find_or_create_github_user
from app.models.user import User
from app.auth.utils import hash_password


def test_find_or_create_github_user_creates_new(db):
    user = find_or_create_github_user(db, "12345", "github@example.com")
    assert user.github_id == "12345"
    assert user.email == "github@example.com"
    assert user.hashed_password is None


def test_find_or_create_github_user_links_existing_email(db):
    existing = User(
        email="dev@example.com",
        hashed_password=hash_password("password"),
    )
    db.add(existing)
    db.commit()

    user = find_or_create_github_user(db, "99999", "dev@example.com")
    assert user.id == existing.id
    assert user.github_id == "99999"


def test_find_or_create_github_user_returns_existing_github_id(db):
    existing = User(
        email=f"gh-{uuid.uuid4().hex[:6]}@example.com",
        github_id="555",
        hashed_password=None,
    )
    db.add(existing)
    db.commit()

    user = find_or_create_github_user(db, "555", existing.email)
    assert user.id == existing.id
