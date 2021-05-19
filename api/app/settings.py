from functools import lru_cache
from pydantic import BaseSettings, DirectoryPath


class Settings(BaseSettings):
    upload_directory: DirectoryPath = "uploads"
    mongo_db_uri: str = "mongodb://localhost:27017"

@lru_cache()
def get_settings():
    return Settings()