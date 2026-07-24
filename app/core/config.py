from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Knowledge Base API"
    debug: bool = False

    database_url: str
    redis_url: str

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    groq_api_key: str
    llm_model: str = "llama-3.3-70b-versatile"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
