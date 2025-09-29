import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_TYPE: str = "postgres"
    POSTGRES_URL: Optional[str] = None
    MONGODB_URL: Optional[str] = None
    GEMINI_API_KEY: str
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    class Config:
        env_file = ".env"
        extra = "ignore" 

settings = Settings()