# app/routes/post_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, Post, Follow
from app.schemas.post_schemas import PostCreate, PostResponse
from app.core.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=PostResponse)
def create_post(
        post: PostCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    db_post = Post(
        content=post.content,
        image_url=post.image_url,
        user_id=current_user.id
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@router.get("/{post_id}", response_model=PostResponse)
def read_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.get("/", response_model=list[PostResponse])
def get_followed_posts(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        skip: int = 0,
        limit: int = 10
):
    followed_user_ids = (
        db.query(Follow.following_id)
        .filter(Follow.follower_id == current_user.id)
        .all())
    posts = (db.query(Post)
             .filter(Post.user_id.in_(followed_user_ids))
             .order_by(Post.created_at.desc())
             .offset(skip)
             .limit(limit)
             .all()
             )
    return posts

# PUT Route to update post content
@router.put("/{post_id}")
def update_post(
    post_id: int,
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    if db_post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this post")

    db_post.content = post.content
    db_post.image_url = post.image_url
    db.commit()
    db.refresh(db_post)
    return db_post


@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    if db_post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this post")

    db.delete(db_post)
    db.commit()
    return {"message": "Post deleted successfully"}

