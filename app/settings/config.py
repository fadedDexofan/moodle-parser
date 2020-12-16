import secrets
from pathlib import Path
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, HttpUrl, validator

PROJECT_ROOT = Path(__file__).parent.parent
BASE_DIR = PROJECT_ROOT.parent
LOGS_ROOT = BASE_DIR.joinpath('logs')

ENV_PATH = BASE_DIR.joinpath('.env')


class Settings(BaseSettings):
    VERSION: str = '0.1.0'
    APP_TITLE: str = 'Moodle Parser'
    PROJECT_NAME: str = 'Moodle Parser'
    SECRET_KEY: str = secrets.token_urlsafe(32)

    HOST: str = 'localhost'
    PORT: int = 8000
    WORKERS: int = 16
    LOG_LEVEL: str = 'INFO'

    DEBUG: bool = True

    APPLICATIONS_MODULE: str = 'app.applications'
    APPLICATIONS: List[str] = [
        'tests'
    ]

    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: int = 15432
    POSTGRES_DB: str = 'bonch'
    POSTGRES_USER: str = 'bonch'
    POSTGRES_PASSWORD: str = 'bonch'

    REDIS_HOST: str = 'localhost'
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str

    CHROMIUM_PATH: str

    CORS_ORIGINS: List[AnyHttpUrl] = [
        'http://localhost',
        'http://localhost:8080',
        'http://localhost:5000',
        'http://localhost:3000',
    ]

    @validator('CORS_ORIGINS', pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ['*']
    CORS_ALLOW_HEADERS: List[str] = ['*']

    SENTRY_DSN: Optional[HttpUrl] = None

    @validator('SENTRY_DSN', pre=True)
    def sentry_dsn_can_be_blank(cls, v: str) -> Optional[str]:
        if len(v) == 0:
            return None
        return v

    def get_db_url(self) -> str:
        host = self.POSTGRES_HOST
        port = self.POSTGRES_PORT
        user = self.POSTGRES_USER
        password = self.POSTGRES_PASSWORD
        name = self.POSTGRES_DB

        return f'postgres://{user}:{password}@{host}:{port}/{name}'

    class Config:
        env_file = ENV_PATH
        env_file_encoding = 'utf-8'
        use_enum_values = True


settings = Settings()
