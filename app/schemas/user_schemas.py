# app/schemas/user_schemas.py
from pydantic import BaseModel, EmailStr
from typing import List
from app.schemas.post_schemas import PostResponse

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

class UserProfile(BaseModel):
    id: int
    name: str
    post_count: int
    followers_count: int
    following_count: int

    class Config:
        from_attributes = True

class UserWithPosts(UserProfile):
    posts: List[PostResponse]