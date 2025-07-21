# backend/config/settings.py
import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    env: str = "dev"
    debug: bool = False
    host_url: str
    google_translation_api_key: str

    class Config:
        env_file = f".env.{os.getenv('ENV', 'dev')}"  # .env.dev 로드

@lru_cache()
def get_settings():
    return Settings()
