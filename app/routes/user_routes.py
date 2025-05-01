# app/routes/user_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, Follow
from app.schemas.user_schemas import UserCreate, UserResponse
from app.core.dependencies import get_current_user


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

@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    print("users/USER_ID was hit")
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


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

    follow_exists = db.query(Follow).filter_by(
        follower_id=current_user.id, following_id=user_id
    ).first()

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

    follow = db.query(Follow).filter_by(
        follower_id=current_user.id, following_id=user_id
    ).first()

    if not follow:
        raise HTTPException(status_code=404, detail="Follow relationship not found.")

    db.delete(follow)
    db.commit()
    return {"detail": "Unfollowed user successfully."}

