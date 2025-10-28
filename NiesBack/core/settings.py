# core/settings.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent  # raiz do projeto (NiesBack/)

class Settings(BaseSettings):
    AZURE_TENANT_ID: str
    AZURE_CLIENT_ID: str
    AZURE_CLIENT_SECRET: str


    #Email
    MAIL_FROM_NAME: str = "NIES"
    MAIL_FROM: str
    MAIL_HOST: str
    MAIL_PORT: int 
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None
    MAIL_USE_TLS: bool = True
    MAIL_USE_SSL: bool = False
    MAIL_DISABLED: bool = True  # desabilita envio real de emails (apenas loga) – para DEV

    # Power BI
    PBI_SCOPE: str = "https://analysis.windows.net/powerbi/api/.default"
    AUTH_URL: str | None = None
    PBI_API: str = "https://api.powerbi.com/v1.0/myorg"

    # pydantic v2
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    DB_URL: str

    SECRET_KEY: str




    # AZURE_REDIRECT_URI: str

    

settings = Settings()
AUTH_URL = settings.AUTH_URL or (
    f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/token"
)
