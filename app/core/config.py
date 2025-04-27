import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configuration settings for the application."""
    
    # Application
    APP_NAME: str = Field("Sequential Questioning MCP Server", env="APP_NAME")
    APP_VERSION: str = Field("0.1.0", env="APP_VERSION")
    DEBUG: bool = Field(False, env="DEBUG")
    ENVIRONMENT: str = Field("production", env="ENVIRONMENT")
    
    # Server
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")
    
    # Database
    DATABASE_URL: str = Field("sqlite:///./app.db", env="DATABASE_URL")
    
    # Qdrant Vector Database
    QDRANT_HOST: str = Field("localhost", env="QDRANT_HOST")
    QDRANT_PORT: int = Field(6333, env="QDRANT_PORT")
    QDRANT_COLLECTION_NAME: str = Field("sequential_questioning", env="QDRANT_COLLECTION_NAME")
    
    # Language Model
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    OPENAI_MODEL_NAME: str = Field("gpt-3.5-turbo", env="OPENAI_MODEL_NAME")
    LLM_TEMPERATURE: float = Field(0.7, env="LLM_TEMPERATURE")
    
    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    """Get application settings from environment variables."""
    return Settings() 