IGClone - Backend API

A backend clone of Instagram built with FastAPI, SQLAlchemy, and PostgreSQL.

Features

User registration and authentication (JWT-based)

Secure password hashing

CRUD operations for Users and Posts

Authentication & Authorization

JWT-protected routes

Pagination for posts

Proper project structure and modularization


Tech Stack

Backend Framework: FastAPI

Database: PostgreSQL

ORM: SQLAlchemy

Authentication: JWT (JSON Web Tokens)

Password Hashing: Passlib (bcrypt)

Environment Variables: python-dotenv

Others: Pydantic, Uvicorn, Python 3.13

Project Structure

IGClone/
├── app/
│   ├──core/
│   │   ├── auth_utils.py
│   │   ├── config.py
│   │   └── dependencies.py
│   ├──db/
│   │   ├── database.py
│   │   └── models.py
│   ├──routes/
│   │   ├── auth_routes.py
│   │   ├── post_routes.py
│   │   └── user_routes.py
│   └── schemas/
│       ├── auth_schemas.py
│       ├── post_schemas.py
│       └── user_schemas.py
├── .env
├── .gitignore
├── requirements.txt
└── README.md

How to Run

1. Clone the repository:

git clone https://github.com/harshdoshi2711/igclone.git
cd IGClone


2. Create a virtual environment and activate it:

python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate


3. Install dependencies:

pip install -r requirements.txt


4. Set up your .env file with necessary environment variables (example):

DATABASE_URL=postgresql://username:password@localhost/dbname
JWT_SECRET_KEY=your_secret_key


5. Run the application:

uvicorn app.main:app --reload


6. Access the API documentation at:

http://localhost:8000/docs
