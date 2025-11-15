import time
import psycopg2
from psycopg2 import OperationalError
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .settings import get_settings
from .database import engine
from .models import Base
from .routers import auth, sessions


# -------------------------------------------------------------------
# 💡 Load settings
# -------------------------------------------------------------------
settings = get_settings()

# -------------------------------------------------------------------
# 💡 Wait for the database to be ready (important in Docker)
# -------------------------------------------------------------------
def wait_for_db():
    db_ready = False
    for attempt in range(10):
        try:
            conn = psycopg2.connect(
                dbname=os.getenv("APP_DB_NAME"),
                user=os.getenv("APP_DB_USER"),
                password=os.getenv("APP_DB_PASSWORD"),
                host=os.getenv("APP_DB_HOST"),
                port=os.getenv("APP_DB_PORT"),
            )
            conn.close()
            db_ready = True
            print("✅ Database is ready!")
            break
        except OperationalError:
            print(f"⏳ Waiting for database... (attempt {attempt+1}/10)")
            time.sleep(3)
    if not db_ready:
        raise RuntimeError("Database not ready after waiting 30 seconds")

wait_for_db()  # 💡 Call before creating tables

# -------------------------------------------------------------------
# 💡 Initialize FastAPI
# -------------------------------------------------------------------
app = FastAPI(title=settings.APP_NAME)

# Create tables after DB is confirmed up
Base.metadata.create_all(bind=engine)

# -------------------------------------------------------------------
# 💡 CORS setup
# -------------------------------------------------------------------
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# 💡 Routers
# -------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(sessions.router)


@app.get("/")
def root():
    return {"status": "ok", "app": settings.APP_NAME}


# -------------------------------------------------------------------
# 💡 Entry point
# -------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)








# import uvicorn
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from .settings import get_settings
# from .database import engine
# from .models import Base
# from .routers import auth, sessions

# settings = get_settings()

# app = FastAPI(title=settings.APP_NAME)

# # Create tables if not using Alembic yet (safe for dev)
# Base.metadata.create_all(bind=engine)

# origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(auth.router)
# app.include_router(sessions.router)

# @app.get("/")
# def root():
#     return {"status": "ok", "app": settings.APP_NAME}

# if __name__ == "__main__":
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
