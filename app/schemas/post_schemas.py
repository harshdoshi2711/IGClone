# app/schemas/post_schemas.py
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class PostBase(BaseModel):
    content: str
    # image_url: str = None # Optional[HttpUrl] = None

class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    id: int
    user_id: int
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    likes_count: Optional[int] = 0

    class Config:
        from_attributes = True
