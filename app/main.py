print("🚀 Starting IGClone FastAPI...")

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