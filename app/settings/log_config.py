from typing import Dict, Union

from app.settings.config import settings

LOG_LEVEL = settings.LOG_LEVEL

LOGGING_CONFIG: Dict[str, Union[Dict, bool, int, str]] = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'class': 'logging.Formatter',
            'format': '%(levelname)-10s %(message)s',
        },
        'verbose': {
            'class': 'logging.Formatter',
            'format': '%(asctime)s | %(levelname)s | %(process)d | %(name)-15s | %(message)s',
        },
        'gunicorn': {
            'class': 'logging.Formatter',
            'format': '%(asctime)s | %(levelname)s | %(process)d | %(name)-15s | %(message)s',
        },
        'uvicorn': {
            '()': 'uvicorn.logging.DefaultFormatter',
            'format': '%(levelprefix)s %(message)s',
            'use_colors': False,
        },
    },
    'handlers': {
        'default': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': LOG_LEVEL,
            'stream': 'ext://sys.stdout',
        }
    },
    'root': {'handlers': ['default'], 'level': LOG_LEVEL},
    'loggers': {
        'fastapi': {'propagate': True},
        'gunicorn.access': {'handlers': ['default'], 'propagate': True},
        'gunicorn.error': {'propagate': True},
        'uvicorn': {'propagate': True},
        'uvicorn.access': {'propagate': True},
        'uvicorn.asgi': {'propagate': True},
        'uvicorn.error': {'propagate': True},
    },
}
