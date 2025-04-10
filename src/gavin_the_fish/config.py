from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_KEY: str = "your-secret-api-key-here"  # Change this to a secure random string
    API_KEY_HEADER: str = "X-API-Key"
    LOG_FILE: str = "logs/requests.log"  # Default log file path

    class Config:
        env_file = ".env"

settings = Settings() 