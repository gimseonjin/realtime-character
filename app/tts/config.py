from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    TTS_SAMPLE_RATE: int = 24000
    TTS_DEFAULT_FORMAT: str = "wav"
    TTS_MAX_TEXT_LEN: int = 500

    # Provider selection: "dummy" | "openai"
    TTS_PROVIDER: str = "dummy"

    # OpenAI TTS settings
    OPENAI_API_KEY: str | None = None
    OPENAI_TTS_MODEL: str = "tts-1"  # "tts-1" | "tts-1-hd"
    OPENAI_TTS_VOICE: str = "alloy"  # alloy, echo, fable, onyx, nova, shimmer

    # Logging
    LOG_JSON: bool = True


settings = Settings()
