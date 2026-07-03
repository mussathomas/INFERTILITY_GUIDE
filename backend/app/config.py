from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    gemini_api_key: str = ""
    secret_key: str = "dev-secret-change-in-production"
    database_url: str = "sqlite:///./data/app.db"
    knowledge_base_dir: str = "./knowledge_base"
    chroma_persist_dir: str = "./data/chroma"
    gemini_model: str = "gemini-2.0-flash"
    access_token_expire_minutes: int = 60 * 24
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k: int = 5

    @property
    def knowledge_base_path(self) -> Path:
        return Path(self.knowledge_base_dir)

    @property
    def chroma_path(self) -> Path:
        return Path(self.chroma_persist_dir)


settings = Settings()
