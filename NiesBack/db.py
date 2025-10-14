# db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.settings import settings


engine = create_engine(settings.DB_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
