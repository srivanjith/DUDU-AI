import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class LocalAgentSettings(BaseSettings):
    HOST: str = "127.0.0.1"
    PORT: int = 8001
    SECRET_TOKEN: str = "dodo_local_agent_shared_secure_token_v1"
    AUTHORIZED_WORKSPACE: str = str(Path("D:/DODO/workspace").resolve())
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


local_settings = LocalAgentSettings()

