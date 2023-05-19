from pydantic import BaseSettings

class Settings(BaseSettings):
    DB_CONFIG:str
    OAUTH2_URL:str
    OAUTH2_TOKEN:str

    class Config:
        env_file = ".env"

settings = Settings()