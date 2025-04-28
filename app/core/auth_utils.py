# app/core/auth_utils.py
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

print("JWT_SECRET_KEY", repr(JWT_SECRET_KEY))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- PASSWORD UTILS ---

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    print("VERIFYING PASSWORD")
    return pwd_context.verify(plain_password, hashed_password)

# --- JWT UTILS ---

def create_access_token(data: dict) -> str:
    print("CREATING TOKEN WITH DATA:", data)
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    print("TOKEN CREATED:", token)
    return token

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        print("✅ Token decoded successfully:", payload)
        return payload
    except JWTError as e:
        print("❌ JWTError occurred while decoding token:", str(e))
        return None
