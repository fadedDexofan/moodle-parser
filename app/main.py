import sentry_sdk
import uvicorn
from fastapi import FastAPI

from app.core.exceptions import SettingNotFound
from app.core.init_app import (
    configure_logging, init_middlewares, register_db, register_exceptions,
    register_routers,
)

try:
    from app.settings.config import settings
except ImportError:
    raise SettingNotFound('Can not import settings. Create settings file from template.config.py')

configure_logging()

if settings.SENTRY_DSN:
    sentry_sdk.init(settings.SENTRY_DSN)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_TITLE,
        version=settings.VERSION,
        debug=settings.DEBUG,
    )

    configure_logging()
    init_middlewares(app)
    register_db(app)
    register_exceptions(app)
    register_routers(app)

    return app


if __name__ == '__main__':
    uvicorn.run(
        app='main:create_app',
        loop='uvloop',
        http='httptools',
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        reload=True,
        factory=True,
    )
