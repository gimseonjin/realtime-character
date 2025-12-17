from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    TTS_URL: str | None = None
    DATABASE_URL: str | None = None
    CACHE_URL: str | None = None


settings = Settings()
