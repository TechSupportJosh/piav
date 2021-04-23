from functools import lru_cache
from pydantic import BaseSettings, DirectoryPath


class Settings(BaseSettings):
    upload_directory: DirectoryPath = "uploads"


@lru_cache()
def get_settings():
    return Settings()