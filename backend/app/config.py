from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "anthropic"          # change here to swap providers
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = ""                   # only for OpenAI-compatible providers
    llm_reasoning_effort: str = ""           # "none" / "low" for Gemini speed-up; empty = default
    database_url: str = "sqlite:///./app.db"  # swap to Postgres later
    frontend_origin: str = "http://localhost:5173"


settings = Settings()
