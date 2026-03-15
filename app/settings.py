from pathlib import Path
from tempfile import gettempdir

from pydantic_settings import BaseSettings, SettingsConfigDict

TEMP_DIR = Path(gettempdir())


class Settings(BaseSettings):
    """
    Application settings.

    These parameters can be configured
    with environment variables.
    """
    gutenberg_uri: str = "https://gutendex.com/books/"

    # qdrant settings
    qdrant_collection: str = "book_collection"
    qdrant_uri: str = "http://localhost:6333"

    # ollama model settings
    ollama_model: str = "tinyllama"
    ollama_uri: str = "http://localhost:11434"

    # retrieval
    top_k_retrieval: int = 5

    # Read .env variables
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()