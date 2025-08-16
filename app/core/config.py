from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "financial_management"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Environment
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"


settings = Settings()