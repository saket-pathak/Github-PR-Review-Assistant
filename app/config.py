from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    github_token: str = ""
    github_webhook_secret: str = ""
    
    # GitLab configurations
    gitlab_token: str = ""
    gitlab_webhook_secret: str = ""
    gitlab_api_url: str = "https://gitlab.com/api/v4"

    
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
