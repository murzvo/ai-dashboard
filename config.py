"""
Configuration management using Pydantic Settings (FastAPI best practice).
Automatically loads from environment variables with validation.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment
    environment: Literal["local", "production"] = "local"
    
    # MongoDB configuration
    mongodb_uri: str = "mongodb://localhost:27017/"
    mongodb_db_name: str = "ai_dashboard"
    
    # Security
    registration_token: str = "demo_registration_token_123"
    
    # AI Configuration
    anthropic_api_key: str = ""
    
    # Widget Configuration
    widget_refresh_interval: int = 30000
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra env vars
    )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        # Auto-detect: Heroku sets DYNO env var
        import os
        if self.environment == "production":
            return True
        return bool(os.getenv("DYNO"))
    
    @property
    def mongodb_uri_normalized(self) -> str:
        """Get normalized MongoDB URI."""
        return self.mongodb_uri.rstrip("/")


# Global settings instance
settings = Settings()

# Backward compatibility exports (for existing code)
ENVIRONMENT = settings.environment
IS_PRODUCTION = settings.is_production
MONGODB_URI = settings.mongodb_uri_normalized
MONGODB_DB_NAME = settings.mongodb_db_name
REGISTRATION_TOKEN = settings.registration_token
ANTHROPIC_API_KEY = settings.anthropic_api_key
WIDGET_REFRESH_INTERVAL = settings.widget_refresh_interval
