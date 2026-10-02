from collections.abc import Callable

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .store import Token, User


def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = db.get(Token, authorization.removeprefix("Bearer "))
    user = db.get(User, token.user_id) if token else None
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def require_role(*roles: str) -> Callable:
    def check(user=Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Requires role: {', '.join(roles)}")
        return user

    return check
