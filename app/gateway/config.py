from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    TTS_URL: str = "http://localhost:8001"
    DATABASE_URL: str | None = None


settings = Settings()
