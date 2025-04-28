# app/schemas/auth_schemas.py
from pydantic import BaseModel

# Request schema
class LoginRequest(BaseModel):
    email: str
    password: str

# Token response schema
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"