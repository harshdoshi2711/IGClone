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
