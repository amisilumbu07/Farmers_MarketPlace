import hashlib
import hmac
import secrets
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..shared.database import get_db
from ..shared.store import Token, User, new_id

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    email: str
    password: str = Field(min_length=8)


class Registration(Credentials):
    role: Literal["farmer", "buyer"] = "buyer"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"{salt.hex()}${digest.hex()}"


def check_password(password: str, stored: str) -> bool:
    salt, digest = stored.split("$", 1)
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 120_000)
    return hmac.compare_digest(actual.hex(), digest)


def issue_token(db: Session, user: User) -> dict:
    db.flush()
    token = uuid4().hex
    db.add(Token(token=token, user_id=user.id))
    return {"token": token, "user_id": user.id, "role": user.role}


@router.post("/register")
def register(credentials: Registration, db: Session = Depends(get_db)):
    email = credentials.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(id=new_id("usr"), email=email, password=hash_password(credentials.password), role=credentials.role, active=True)
    db.add(user)
    return issue_token(db, user)


@router.post("/login")
def login(credentials: Credentials, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == credentials.email.lower()))
    if not user or not check_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return issue_token(db, user)
