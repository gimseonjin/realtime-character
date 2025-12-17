from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    TTS_SAMPLE_RATE: int = 24000
    TTS_DEFAULT_FORMAT: str = "wav"
    TTS_MAX_TEXT_LEN: int = 500


settings = Settings()
