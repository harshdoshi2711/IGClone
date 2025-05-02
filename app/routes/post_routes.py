# app/routes/post_routes.py
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Query
from sqlalchemy import func, select, desc, asc
from sqlalchemy.orm import Session, aliased
from app.db.database import get_db
from app.db.models import User, Post, Follow, Like
from app.schemas.post_schemas import PostCreate, PostResponse
from app.core.dependencies import get_current_user
from typing import List, Optional
import os
from uuid import uuid4

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok = True)

router = APIRouter()

@router.post("/", response_model=PostResponse, status_code=201)
def create_post(
        content: str = Form(...),
        image: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    image_url = None
    if image:
        ext = os.path.splitext(image.filename)[1]
        filename = f"{uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(image.file.read())
        image_url = f"/{UPLOAD_DIR}/{filename}"

    post = Post(
        content=content,
        image_url=image_url,
        user_id=current_user.id
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return PostResponse(
        id=post.id,
        content=post.content,
        image_url=post.image_url,
        user_id=post.user_id,
        created_at=post.created_at,
        updated_at=post.updated_at,
        likes_count=0
    )

@router.get("/{post_id}", response_model=PostResponse)
def read_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Step 1: Get the post and likes count
    result = (
        db.query(Post, func.count(Like.id).label("likes_count"))
        .outerjoin(Like, Post.id == Like.post_id)
        .filter(Post.id == post_id)
        .group_by(Post.id)
        .first()
    )

    if not result:
        raise HTTPException(status_code=404, detail="Post not found")

    post, likes_count = result

    # Step 2: Check if current user is allowed to view the post
    if post.user_id != current_user.id:
        follow_exists = db.query(Follow).filter_by(
            follower_id=current_user.id,
            following_id=post.user_id
        ).first()

        if not follow_exists:
            raise HTTPException(status_code=403, detail="You are not authorized to view this post")

    # Step 3: Return the post with likes_count
    return PostResponse(
        id=post.id,
        content=post.content,
        image_url=post.image_url,
        user_id=post.user_id,
        created_at=post.created_at,
        updated_at=post.updated_at,
        likes_count=likes_count
    )

@router.get("/", response_model=List[PostResponse])
def get_posts(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        skip: int = Query(0, ge=0),
        limit: int = Query(10, le=50),
        user_id: Optional[int] = None,
        #search: Optional[str] = None,
        sort_by: Optional[str] = Query("created_at", regex="^(created_at|likes)$"),
        sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$")
):
    # Get IDs of users that current user follows
    followed_user_ids = select(Follow.following_id).filter(Follow.follower_id == current_user.id)

    like_alias = aliased(Like)

    query = (db.query(Post, func.count(like_alias.id).label("likes_count"))
             .outerjoin(like_alias, Post.id == like_alias.post_id)
             .filter(Post.user_id.in_(followed_user_ids)).group_by(Post.id)
             )

    #query = (db.query(Post).filter(Post.user_id.in_(followed_user_ids)))

    if user_id:
        query = query.filter(Post.user_id == user_id)
    else:
        query = query.filter(Post.user_id.in_(followed_user_ids))

    # if search:
    #     query = query.filter(Post.content.ilike(f"%{search}%"))

    if sort_by == "likes":
        order = desc("likes_count") if sort_order == "desc" else asc("like_count")
    else:
        order = desc(Post.created_at) if sort_order == "desc" else asc(Post.created_at)

    posts = query.order_by(order).offset(skip).limit(limit).all()

    return [
        PostResponse(
            id=post.id,
            content=post.content,
            image_url=post.image_url,
            user_id=post.user_id,
            created_at=post.created_at,
            updated_at=post.updated_at,
            likes_count=likes_count
        )
        for post, likes_count in posts
    ]

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


@router.post("/{post_id}/like", status_code=201)
def like_post(
        post_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    existing_like = db.query(Like).filter_by(user_id=current_user.id, post_id=post_id).first()
    if existing_like:
        raise HTTPException(status_code=400, detail="You have already liked this post.")

    like = Like(user_id=current_user.id, post_id=post_id)
    db.add(like)
    db.commit()
    return {"detail": "Post liked successfully."}


@router.delete("/{post_id}/unlike", status_code=200)
def unlike_post(
        post_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    like = db.query(Like).filter_by(user_id=current_user.id, post_id=post_id).first()
    if not like:
        raise HTTPException(status_code=404, detail="You have not liked this post.")

    db.delete(like)
    db.commit()
    return {"detail": "Post unliked successfully."}

