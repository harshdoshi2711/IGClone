# app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Replace with your actual PostgreSQL details
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/igclone"

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
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)

    # One-to-many relationship with posts
    posts = relationship("Post", back_populates="owner", cascade="all, delete")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, index=True)
    image_url = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    # Many-to-one relationship to user
    owner = relationship("User", back_populates="posts")


# app/create_db.py
from app.db.database import engine
from app.db.models import Base

# Create all tables
Base.metadata.create_all(bind=engine)

print("✅ Tables created successfully!")



# app/core/config.py
from dotenv import load_dotenv
import os

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# app/core/auth_utils.py
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

print("JWT_SECRET_KEY", repr(JWT_SECRET_KEY))

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
from pydantic import BaseModel

class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True


# app/schemas/post_schemas.py
from pydantic import BaseModel
from typing import Optional

class PostCreate(BaseModel):
    content: str
    image_url: Optional[str] = None

class PostRead(PostCreate):
    id: int
    user_id: int

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


@router.get("/test", tags=["Auth"])
def test_auth_route():
    print("LOGIN ROUTE HIT")
    return {"message": "Auth route works!"}


# app/routes/user_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.schemas.user_schemas import UserCreate, UserResponse
from app.core.dependencies import get_current_user


router = APIRouter()

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

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

@router.get("/", response_model=list[UserResponse])
def get_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(User).offset(skip).limit(limit).all()

@router.put("/{user_id}")
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.name = user.name
    db_user.email = user.email
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


# app/routes/post_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, Post
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
def get_posts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(Post).offset(skip).limit(limit).all()

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


# app/main.py
print("🚀 Starting IGClone FastAPI...")
from fastapi import FastAPI
from app.routes.user_routes import router as user_router
from app.routes.post_routes import router as post_router
from app.routes.auth_routes import router as auth_router

app = FastAPI()

# Include the routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(post_router, prefix="/posts", tags=["Posts"])

# Health check route
@app.get("/")
def read_root():
    return {"message": "Welcome to IGClone API"}
