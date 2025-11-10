from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "EduMentorAI Backend"
    ENV: str = "dev"

    # CORS
    CORS_ORIGINS: str = "http://localhost:8501,http://127.0.0.1:8501"

    # OpenAI
    OPENAI_API_KEY: str

    # Database (psycopg is the modern driver)
    DATABASE_URL: str = "postgresql+psycopg://edumentor:edumentorpw@localhost:5432/edumentor"

    # JWT
    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Azure (optional, for later)
    AZURE_POSTGRES_SSLMODE: Optional[str] = "require"

    @field_validator("CORS_ORIGINS")
    @classmethod
    def parse_cors(cls, v: str):
        # keep as comma-separated for easy split in main
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    return Settings()
