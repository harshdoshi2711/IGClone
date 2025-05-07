# app/schemas/comment_schemas.py
from pydantic import BaseModel
from datetime import datetime

class CommentCreate(BaseModel):
    post_id: int
    content: str

class CommentRead(BaseModel):
    id: int
    post_id: int
    user_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

