from pydantic import BaseSettings

class Settings(BaseSettings):
    DB_CONFIG:str
    OAUTH2_URL:str
    OAUTH2_TOKEN:str
    GOOGLE_APPLICATION_CREDENTIALS: str = 'creds/sa.json'
    GS_BUCKET_NAME: str
    GS_PROJECT_ID: str
    QUEUE_LOCATION: str
    PROJECT_NAME:str
    PDF_URL:str

    WF_BASE_URL:str
    WF_PUBLIC_KEY: str
    WF_SIGN_PRIVATE_KEY:str
    WF_SIGN_PUBLIC_KEY:str
    WF_CLIENT_ID:str
    RFP_BASE_URL:str
    RFP_CLIENT_ID:str
    ADOBE_TOKEN:str
    ADOBE_CLIENT_ID:str
    ADOBE_CLIENT_SECRET:str
    KEY_ENCRYPT_DOC:str

    INSTANCE:str

    class Config:
        env_file = ".env"

settings = Settings()