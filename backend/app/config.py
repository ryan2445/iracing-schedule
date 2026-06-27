from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Configurations
    iracing_username: str | None = None
    iracing_password: str | None = None
    iracing_client_id: str | None = None
    iracing_client_secret: str | None = None
    
    # Mode selection
    mock_mode: bool = True
    
    # CORS Origins
    allowed_origins: list[str] = ["*"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Auto-enable mock mode if no credentials are provided
if not (settings.iracing_username and settings.iracing_password) and not (settings.iracing_client_id and settings.iracing_client_secret):
    settings.mock_mode = True
