from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import Optional
import os

class Settings(BaseSettings):
    APP_NAME: str = "EduMentorAI Backend"
    ENV: str = "dev"

    # CORS
    CORS_ORIGINS: str = "http://localhost:8501,http://127.0.0.1:8501,http://172.24.124.9:8501,http://0.0.0.0:8501"

    # OpenAI
    OPENAI_API_KEY: str

    # ✅ Add type annotations for DB config
    DB_USER: str = os.getenv("APP_DB_USER", "edumentor")
    DB_PASSWORD: str = os.getenv("APP_DB_PASSWORD", "edumentorpw")
    DB_HOST: str = os.getenv("APP_DB_HOST", "db")
    DB_PORT: str = os.getenv("APP_DB_PORT", "5432")
    DB_NAME: str = os.getenv("APP_DB_NAME", "edumentor")

    # ✅ Annotate DATABASE_URL too
    DATABASE_URL: str = f"postgresql+psycopg://{os.getenv('APP_DB_USER', 'edumentor')}:{os.getenv('APP_DB_PASSWORD', 'edumentorpw')}@{os.getenv('APP_DB_HOST', 'db')}:{os.getenv('APP_DB_PORT', '5432')}/{os.getenv('APP_DB_NAME', 'edumentor')}"

    # JWT
    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Azure (optional)
    AZURE_POSTGRES_SSLMODE: Optional[str] = "require"

    @field_validator("CORS_ORIGINS")
    @classmethod
    def parse_cors(cls, v: str):
        return v  # keep as comma-separated for easy split

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    return Settings()









# from pydantic_settings import BaseSettings
# from pydantic import field_validator
# from functools import lru_cache
# from typing import Optional
# import os

# class Settings(BaseSettings):
#     APP_NAME: str = "EduMentorAI Backend"
#     ENV: str = "dev"

#     # CORS
#     CORS_ORIGINS: str = "http://localhost:8501,http://127.0.0.1:8501,http://172.24.124.9:8501,http://0.0.0.0:8501"

#     # OpenAI
#     OPENAI_API_KEY: str

#     DB_USER = os.getenv("APP_DB_USER", "edumentor")
#     DB_PASSWORD = os.getenv("APP_DB_PASSWORD", "edumentorpw")
#     DB_HOST = os.getenv("APP_DB_HOST", "db")
#     DB_PORT = os.getenv("APP_DB_PORT", "5432")
#     DB_NAME = os.getenv("APP_DB_NAME", "edumentor")
#     DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

#     # Database (psycopg is the modern driver)
#     #DATABASE_URL: str = "postgresql+psycopg://edumentor:edumentorpw@localhost:5432/edumentor"

#     # JWT
#     JWT_SECRET: str
#     JWT_ALG: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

#     # Azure (optional, for later)
#     AZURE_POSTGRES_SSLMODE: Optional[str] = "require"

#     @field_validator("CORS_ORIGINS")
#     @classmethod
#     def parse_cors(cls, v: str):
#         # keep as comma-separated for easy split in main
#         return v

#     class Config:
#         env_file = ".env"
#         case_sensitive = True

# @lru_cache
# def get_settings() -> Settings:
#     return Settings()
