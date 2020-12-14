from logging.config import dictConfig
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from app.applications.tests.routes import router as tests_router
from app.core.exceptions import APIException, on_api_exception
from app.settings.config import settings
from app.settings.log_config import LOGGING_CONFIG


def configure_logging() -> None:
    dictConfig(LOGGING_CONFIG)


def init_middlewares(app: FastAPI):
    if settings.SENTRY_DSN:
        app.add_middleware(SentryAsgiMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )


def get_apps_list() -> List[str]:
    return [
        f'{settings.APPLICATIONS_MODULE}.{app}'
        for app in settings.APPLICATIONS
    ]


def get_models_list() -> List[str]:
    models = [f'{app}.models' for app in get_apps_list()]
    models.append('aerich.models')
    return models


def get_tortoise_config() -> Dict[str, Any]:
    return {
        'connections': {'default': settings.get_db_url()},
        'apps': {
            'models': {
                'models': get_models_list(),
                'default_connection': 'default',
            }
        }
    }


TORTOISE_ORM = get_tortoise_config()


def register_db(app: FastAPI) -> None:
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        modules={'models': get_models_list()},
        generate_schemas=False,
        add_exception_handlers=True,
    )


async def init_db() -> None:
    await Tortoise.init(
        config=TORTOISE_ORM,
        modules={'models': get_models_list()},
    )


def register_exceptions(app: FastAPI):
    app.add_exception_handler(APIException, on_api_exception)


def register_routers(app: FastAPI):
    app.include_router(tests_router, prefix='/api/tests')
