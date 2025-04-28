# app/create_db.py
from app.db.database import engine
from app.db.models import Base

# Create all tables
Base.metadata.create_all(bind=engine)

print("✅ Tables created successfully!")
