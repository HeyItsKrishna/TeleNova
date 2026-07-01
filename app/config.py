from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    google_cloud_project: str = Field(..., env="GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = Field(default="us-central1", env="GOOGLE_CLOUD_LOCATION")

    gemini_model: str = Field(default="gemini-2.5-flash", env="GEMINI_MODEL")
    gemini_temperature: float = Field(default=0.2, env="GEMINI_TEMPERATURE")
    gemini_max_output_tokens: int = Field(default=1024, env="GEMINI_MAX_OUTPUT_TOKENS")

    dialogflow_agent_id: str = Field(default="", env="DIALOGFLOW_AGENT_ID")
    dialogflow_location: str = Field(default="global", env="DIALOGFLOW_LOCATION")

    gcs_bucket_name: str = Field(default="telecom-support-knowledge-base", env="GCS_BUCKET_NAME")
    chroma_persist_dir: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIR")

    database_url: str = Field(
        default="postgresql://telenova:telenova_dev@localhost:5432/telenova",
        env="DATABASE_URL",
    )
    db_pool_min_size: int = Field(default=2, env="DB_POOL_MIN_SIZE")
    db_pool_max_size: int = Field(default=10, env="DB_POOL_MAX_SIZE")
    db_command_timeout_seconds: int = Field(default=10, env="DB_COMMAND_TIMEOUT_SECONDS")

    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    app_env: str = Field(default="production", env="APP_ENV")
    app_port: int = Field(default=8080, env="APP_PORT")

    session_ttl_seconds: int = Field(default=1800, env="SESSION_TTL_SECONDS")
    max_history_turns: int = Field(default=10, env="MAX_HISTORY_TURNS")

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
