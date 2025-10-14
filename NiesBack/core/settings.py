# core/settings.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # raiz do projeto (NiesBack/)

class Settings(BaseSettings):
    AZURE_TENANT_ID: str
    AZURE_CLIENT_ID: str
    AZURE_CLIENT_SECRET: str

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
    

settings = Settings()
AUTH_URL = settings.AUTH_URL or (
    f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/token"
)
