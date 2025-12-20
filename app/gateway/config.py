from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    TTS_URL: str | None = None
    DATABASE_URL: str | None = None
    CACHE_URL: str | None = None

    # LLM Provider selection: "mock" | "openai"
    LLM_PROVIDER: str = "mock"

    # OpenAI LLM settings
    OPENAI_API_KEY: str | None = None
    OPENAI_LLM_MODEL: str = "gpt-4o-mini"
    OPENAI_LLM_TEMPERATURE: float = 0.7
    OPENAI_LLM_MAX_TOKENS: int = 1024
    OPENAI_LLM_SYSTEM_PROMPT: str | None = None

    # Logging
    LOG_JSON: bool = True  # False for colored console output (dev)


settings = Settings()
