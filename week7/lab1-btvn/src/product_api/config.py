import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DB_URL", "sqlite:///lab1.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    API_TITLE = "Lab 1 - Product & Order API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
