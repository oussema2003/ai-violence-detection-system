"""
Session SQLAlchemy + initialisation de la base
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SQLITE = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'surveillance.db')}"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE)

if DATABASE_URL.startswith("sqlite"):
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
