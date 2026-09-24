from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    typesafe_api_key: str = ""
    claude_model: str = "claude-sonnet-5"
    whisper_model: str = "whisper-1"
    max_slide_mb: int = 20
    max_media_mb: int = 300
    cors_origin: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
