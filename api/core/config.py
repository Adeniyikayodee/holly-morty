from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Settings
    app_name: str = "Holly and Morty API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # ElevenLabs Settings
    elevenlabs_webhook_secret: Optional[str] = None
    
    # Azure Cosmos DB Settings
    cosmos_connection_string: Optional[str] = None
    cosmos_database_name: str = "holly-morty-db"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
