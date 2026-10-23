from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./ai_ecosystem.db"
    secret_key: str = ""
    access_token_minutes: int = 60
    cors_origins: str = "http://localhost:8080"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
