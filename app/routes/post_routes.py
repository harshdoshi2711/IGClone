# app/routes/post_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, Post, Follow, Like
from app.schemas.post_schemas import PostCreate, PostResponse
from app.core.dependencies import get_current_user
from typing import List

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

# @router.get("/{post_id}", response_model=PostResponse)
# def read_post(post_id: int, db: Session = Depends(get_db)):
#     post = db.query(Post).filter(Post.id == post_id).first()
#     if not post:
#         raise HTTPException(status_code=404, detail="Post not found")
#     return post

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



# @router.get("/", response_model=list[PostResponse])
# def get_followed_posts(
#         db: Session = Depends(get_db),
#         current_user: User = Depends(get_current_user),
#         skip: int = 0,
#         limit: int = 20
# ):
#     followed_user_ids = (
#         db.query(Follow.following_id).filter(Follow.follower_id == current_user.id).all())
#     followed_user_ids = [row[0] for row in followed_user_ids]
#     posts = (db.query(Post)
#              .filter(Post.user_id.in_(followed_user_ids))
#              .order_by(Post.created_at.desc())
#              .offset(skip)
#              .limit(limit)
#              .all()
#              )
#     return posts


@router.get("/", response_model=List[PostResponse])
def get_posts(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        skip: int = 0,
        limit: int = 20
):
    # Get IDs of users that current user follows
    followed_ids = db.query(Follow.following_id).filter(Follow.follower_id == current_user.id)

    # Get posts and their like counts
    posts = (
        db.query(
            Post, func.count(Like.id).label("likes_count")
        )
        .outerjoin(Like, Post.id == Like.post_id)
        .filter(Post.user_id.in_(followed_ids))
        .group_by(Post.id)
        .order_by(Post.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

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

