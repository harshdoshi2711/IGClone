# app/core/config.py
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# app/core/dependencies.py

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi import Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.auth_utils import decode_access_token
from app.db.database import get_db
from app.db.models import User

# This allows token pasting manually in Swagger (via "Authorize" popup)
api_key_scheme = APIKeyHeader(name="Authorization", auto_error=False)

# This allows automatic flow if you're using OAuth2 password flow in Swagger (less reliable for testing)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: Optional[str] = Security(api_key_scheme), db: Session = Depends(get_db)) -> User:
    if token.startswith("Bearer "):
        token = token[len("Bearer "):]

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"})

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None:
        raise credentials_exception

    return user

# app/core/auth_utils.py
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

#print("JWT_SECRET_KEY", repr(JWT_SECRET_KEY))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- PASSWORD UTILS ---

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    print("VERIFYING PASSWORD")
    return pwd_context.verify(plain_password, hashed_password)

# --- JWT UTILS ---

def create_access_token(data: dict) -> str:
    print("CREATING TOKEN WITH DATA:", data)
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    print("TOKEN CREATED:", token)
    return token

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        print("✅ Token decoded successfully:", payload)
        return payload
    except JWTError as e:
        print("❌ JWTError occurred while decoding token:", str(e))
        return None

# app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import DATABASE_URL

# Replace with your actual PostgreSQL details
# DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/igclone"

# SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Create a configured Session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

# Dependency for getting DB session in routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# app/db/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)

    # One-to-many relationship with posts
    posts = relationship("Post", back_populates="user", cascade="all, delete")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, index=True, nullable=False)
    image_url = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Many-to-one relationship to user
    user = relationship("User", back_populates="posts")

class Follow(Base):
    __tablename__ = "follows"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    following_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint("follower_id", "following_id", name="unique_follow"),)

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "post_id", name="unique_like"),)

# app/schemas/auth_schemas.py
from pydantic import BaseModel

# Request schema
class LoginRequest(BaseModel):
    email: str
    password: str

# Token response schema
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

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

# app/routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.schemas.user_schemas import UserCreate, UserResponse
from app.schemas.auth_schemas import LoginRequest, TokenResponse
from app.core.auth_utils import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user


router = APIRouter()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password
    hashed_password = hash_password(user.password)

    # Create a new user object
    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password
    )

    # Save to DB
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    print("LOGIN ROUTE HIT")
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if not user or not verify_password(request.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        access_token = create_access_token({"sub": str(user.id)})
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        print("LOGIN ERROR:", e)  # <-- Add this to debug
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error - check logs"
        )


# @router.get("/test", tags=["Auth"])
# def test_auth_route():
#     print("LOGIN ROUTE HIT")
#     return {"message": "Auth route works!"}

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

# app/routes/comment_routes.py
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

# app/create_db.py
from app.db.database import engine
from app.db.models import Base

# Create all tables
Base.metadata.create_all(bind=engine)

print("✅ Tables created successfully!")

# app/main.py
from fastapi import FastAPI
from app.routes.auth_routes import router as auth_router
from app.routes.user_routes import router as user_router
from app.routes.post_routes import router as post_router
from app.routes.comment_routes import router as comment_router
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Include the routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(post_router, prefix="/posts", tags=["Posts"])
app.include_router(comment_router)

# Health check route
@app.get("/")
def read_root():
    return {"message": "Welcome to IGClone API"}

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Dockerfile
# Use official Python base image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code into the container
COPY . .

# Expose port (FastAPI default is 8000)
EXPOSE 8000

# Start FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

#docker-compose.yml
version: "3.9"

services:
  db:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: igclone
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  web:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/code
    ports:
      - "8000:8000"
    depends_on:
      - db
    env_file:
      - .env

volumes:
  postgres_data:
