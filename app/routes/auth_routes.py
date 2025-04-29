# app/routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.schemas.user_schemas import UserCreate, UserRead
from app.schemas.auth_schemas import LoginRequest, TokenResponse
from app.core.auth_utils import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user


router = APIRouter()


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
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
