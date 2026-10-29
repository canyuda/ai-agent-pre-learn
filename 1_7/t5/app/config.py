from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置：环境变量优先，其次 .env 文件（.env 已被 gitignore，密钥不入库）。"""

    app_name: str = "t5-health-api"
    version: str = "0.1.0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
