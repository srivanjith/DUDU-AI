import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "DODO"
    TAGLINE: str = "Your AI. Your Machine. Your Rules."
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = "dodo_dev_secret_key_change_in_production_min_32_chars"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "dodo_db"
    MONGODB_MAX_POOL_SIZE: int = 50
    MONGODB_MIN_POOL_SIZE: int = 10
    MONGODB_SERVER_SELECTION_TIMEOUT_MS: int = 2000

    # Ollama / Local AI Inference
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TIMEOUT_SECONDS: int = 120
    DEFAULT_GENERAL_MODEL: str = "qwen2.5:7b"
    DEFAULT_CODING_MODEL: str = "qwen2.5-coder:7b"
    DEFAULT_REASONING_MODEL: str = "deepseek-r1:8b"
    DEFAULT_LIGHTWEIGHT_MODEL: str = "llama3.2:1b"
    DEFAULT_EMBEDDING_MODEL: str = "nomic-embed-text"

    # Local Agent
    LOCAL_AGENT_HOST: str = "127.0.0.1"
    LOCAL_AGENT_PORT: int = 8001
    LOCAL_AGENT_SECRET_TOKEN: str = "dodo_local_agent_shared_secure_token_v1"
    AUTHORIZED_WORKSPACE_DIR: str = str(Path("D:/DODO/workspace").resolve())

    # Agent Limits & Safety
    MAX_EXECUTION_STEPS: int = 35
    STEP_TIMEOUT_SECONDS: int = 180
    MAX_RETRIES_PER_STEP: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

