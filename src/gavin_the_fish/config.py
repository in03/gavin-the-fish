from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_KEY: str = "your-secret-api-key-here"  # Change this to a secure random string
    API_KEY_HEADER: str = "X-API-Key"
    LOG_FILE: str = "logs/requests.log"  # Default log file path
    
    # ElevenLabs Configuration
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_AGENT_ID: str = ""
    ELEVENLABS_API_BASE_URL: str = "https://api.elevenlabs.io/v1"

    class Config:
        env_file = ".env"

settings = Settings() 