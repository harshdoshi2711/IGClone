# app/routes/user_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, Follow, Post
from app.schemas.user_schemas import UserCreate, UserResponse, UserProfile, UserWithPosts
from app.core.dependencies import get_current_user
from typing import List

router = APIRouter()

# @router.post("/", response_model=UserRead)
# def create_user(user: UserCreate, db: Session = Depends(get_db)):
#     db_user = User(name=user.name, email=user.email)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

@router.get("/", response_model=list[UserResponse])
def get_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(User).offset(skip).limit(limit).all()
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    print("📡 /users/me was hit")
    return current_user

@router.get("/{user_id}/profile", response_model=UserProfile)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    post_count = db.query(func.count(Post.id)).filter(Post.user_id == user_id).scalar()
    followers_count = db.query(func.count(Follow.id)).filter(Follow.following_id == user_id).scalar()
    following_count = db.query(func.count(Follow.id)).filter(Follow.follower_id == user_id).scalar()

    return UserProfile(
        id=user.id,
        name=user.name,
        post_count=post_count,
        followers_count=followers_count,
        following_count=following_count
    )

@router.get("/search", response_model=UserWithPosts)
def search_user_by_name(
    search: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.name.ilike(f"%{search}%")).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id != current_user.id:
        is_following = (db.query(Follow)
                        .filter(Follow.follower_id == current_user.id, Follow.following_id == user.id)
                        .first()
                        )
        if not is_following:
            raise HTTPException(status_code=403, detail="You are not allowed to view this user's profile")

    post_count = db.query(func.count(Post.id)).filter(Post.user_id == user.id).scalar()
    followers_count = db.query(func.count(Follow.id)).filter(Follow.following_id == user.id).scalar()
    following_count = db.query(func.count(Follow.id)).filter(Follow.follower_id == user.id).scalar()
    user_posts = db.query(Post).filter(Post.user_id == user.id).order_by(Post.created_at.desc()).all()

    return {
        "id": user.id,
        "name": user.name,
        "post_count": post_count,
        "followers_count": followers_count,
        "following_count": following_count,
        "posts": user_posts
    }

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
        user_id: int,
        updated_user: UserCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")

    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.name = updated_user.name
    db_user.email = updated_user.email
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}")
def delete_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/follow", status_code=201)
def follow_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself.")

    follow_exists = (db.query(Follow)
                     .filter_by(follower_id=current_user.id, following_id=user_id)
                     .first()
                     )

    if follow_exists:
        raise HTTPException(status_code=400, detail="You are already following this user.")

    follow = Follow(follower_id=current_user.id, following_id=user_id)
    db.add(follow)
    db.commit()
    return {"detail": "Followed user successfully."}


@router.delete("/{user_id}/unfollow", status_code=200)
def unfollow_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):

    follow = (db.query(Follow)
              .filter_by(follower_id=current_user.id, following_id=user_id)
              .first()
              )

    if not follow:
        raise HTTPException(status_code=404, detail="Follow relationship not found.")

    db.delete(follow)
    db.commit()
    return {"detail": "Unfollowed user successfully."}


@router.get("/{user_id}/following", response_model = List[UserResponse])
def get_following(
        user_id: int,
        db: Session = Depends(get_db)
):
    following = (db.query(User)
                 .join(Follow, Follow.following_id == User.id)
                 .filter(Follow.follower_id == user_id)
                 .all()
                 )
    return following


@router.get("/{user_id}/followers", response_model = List[UserResponse])
def get_followers(
        user_id: int,
        db: Session = Depends(get_db)
):
    followers = (db.query(User)
                 .join(Follow, Follow.follower_id == User.id)
                 .filter(Follow.following_id == user_id)
                 .all()
                 )
    return followers
