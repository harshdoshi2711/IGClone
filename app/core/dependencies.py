# app/core/dependencies.py

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi import Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.auth_utils import decode_access_token
from app.db.database import get_db
from app.db.models import User

# This allows token pasting manually in Swagger (via "Authorize" popup)
api_key_scheme = APIKeyHeader(name="Authorization", auto_error=False)

# This allows automatic flow if you're using OAuth2 password flow in Swagger (less reliable for testing)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: Optional[str] = Security(api_key_scheme), db: Session = Depends(get_db)) -> User:
    if token.startswith("Bearer "):
        token = token[len("Bearer "):]

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"})

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None:
        raise credentials_exception

    return user
