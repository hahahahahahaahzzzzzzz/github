import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "RepoLeak Watcher X"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = Field(default="cyberpunk-neon-glow-secret-key-321", validation_alias="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week
    
    # Databases
    DATABASE_URL: str = Field(default="sqlite:///./repoleak.db", validation_alias="DATABASE_URL")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    
    # Intelligence & Integrations
    GITHUB_TOKENS: str = Field(default="", description="Comma-separated GitHub Personal Access Tokens")
    TELEGRAM_BOT_TOKEN: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str = Field(default="", validation_alias="TELEGRAM_CHAT_ID")
    AI_API_KEY: str = Field(default="", validation_alias="AI_API_KEY")
    
    # System Controls
    SIMULATION_MODE: bool = Field(default=True, description="Enable simulated real-time leak generator")
    SIMULATION_INTERVAL_SECONDS: int = Field(default=5, description="Frequency of simulated leak generation")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def github_token_list(self) -> List[str]:
        if not self.GITHUB_TOKENS:
            return []
        return [t.strip() for t in self.GITHUB_TOKENS.split(",") if t.strip()]

settings = Settings()
