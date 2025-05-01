from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Comment, Post
from app.schemas.comment_schemas import CommentCreate, CommentRead
from app.core.dependencies import get_current_user
from app.db.models import User
from typing import List

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.post("/", response_model=CommentRead, status_code=201)
def create_comment(comment: CommentCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == comment.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    new_comment = Comment(
        post_id=comment.post_id,
        user_id=current_user.id,
        content=comment.content
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


@router.get("/post/{post_id}", response_model=List[CommentRead])
def get_comments_for_post(post_id: int, db: Session = Depends(get_db)):
    return db.query(Comment).filter(Comment.post_id == post_id).order_by(Comment.created_at.desc()).all()


