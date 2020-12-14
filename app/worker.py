import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

from app.core.celery_app import celery_app  # noqa
from app.core.init_app import configure_logging
from app.settings.config import settings

configure_logging()

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[CeleryIntegration()],
    )
