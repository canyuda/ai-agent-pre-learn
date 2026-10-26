"""集中管理应用配置（后续可升级为 pydantic-settings）。"""

import os

APP_NAME = os.getenv("APP_NAME", "my-project")
DEBUG = os.getenv("APP_ENV", "development") == "development"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
