from pydantic import BaseSettings

class Settings(BaseSettings):
    DB_CONFIG:str

    class Config:
        env_file = ".env"

settings = Settings()