# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from .settings import get_settings

# settings = get_settings()

# engine = create_engine(
#     settings.DATABASE_URL,
#     pool_pre_ping=True,
# )

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .settings import get_settings
import os

settings = get_settings()

# --- Build DATABASE_URL dynamically ---
# Prefer DATABASE_URL if explicitly set (for local dev)
# Otherwise, construct it from APP_DB_* env vars (for Docker)
if settings.DATABASE_URL and "localhost" not in settings.DATABASE_URL:
    DATABASE_URL = settings.DATABASE_URL
else:
    DB_USER = os.getenv("APP_DB_USER", "edumentor")
    DB_PASSWORD = os.getenv("APP_DB_PASSWORD", "edumentorpw")
    DB_HOST = os.getenv("APP_DB_HOST", "db")
    DB_PORT = os.getenv("APP_DB_PORT", "5432")
    DB_NAME = os.getenv("APP_DB_NAME", "edumentor")
    DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- Create engine and session ---
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
