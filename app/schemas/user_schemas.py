# app/schemas/user_schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

class FollowBase(BaseModel):
    follower_id: int
    following_id: int

class FollowRead(FollowBase):
    id: int

    class Config:
        from_attributes = True
