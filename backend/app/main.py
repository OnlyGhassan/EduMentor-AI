import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .settings import get_settings
from .database import engine
from .models import Base
from .routers import auth, sessions

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

# Create tables if not using Alembic yet (safe for dev)
Base.metadata.create_all(bind=engine)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sessions.router)

@app.get("/")
def root():
    return {"status": "ok", "app": settings.APP_NAME}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
