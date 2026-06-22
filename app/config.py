from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    github_token: str = ""
    github_webhook_secret: str = ""
    
    # LLM configurations
    llm_provider: str = "anthropic"  # 'anthropic', 'openai', or 'mock'
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    
    # Server configurations
    port: int = 8000
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
