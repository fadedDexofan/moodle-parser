import multiprocessing
import os

from app.settings.config import settings
from app.settings.log_config import LOGGING_CONFIG

workers_per_core_str = os.getenv('WORKERS_PER_CORE', '1')
max_workers_str = os.getenv('MAX_WORKERS')
use_max_workers = None
if max_workers_str:
    use_max_workers = int(max_workers_str)
web_concurrency_str = os.getenv('WEB_CONCURRENCY', None)

host = settings.HOST
port = settings.PORT
bind_env = os.getenv('BIND', None)
use_loglevel = settings.LOG_LEVEL
use_bind = bind_env or f'{host}:{port}'
cores = multiprocessing.cpu_count()
workers_per_core = float(workers_per_core_str)
default_web_concurrency = workers_per_core * cores

if web_concurrency_str:
    web_concurrency = int(web_concurrency_str)
    assert web_concurrency > 0
else:
    web_concurrency = max(int(default_web_concurrency), 2)
    if use_max_workers:
        web_concurrency = min(web_concurrency, use_max_workers)

accesslog_var = os.getenv('ACCESS_LOG', '-')
use_accesslog = accesslog_var or None
errorlog_var = os.getenv('ERROR_LOG', '-')
use_errorlog = errorlog_var or None
graceful_timeout_str = os.getenv('GRACEFUL_TIMEOUT', '120')
timeout_str = os.getenv('TIMEOUT', '120')
keepalive_str = os.getenv('KEEP_ALIVE', '5')

# Gunicorn config variables
loglevel = use_loglevel
workers = web_concurrency
bind = use_bind
logconfig_dict = LOGGING_CONFIG
errorlog = use_errorlog
worker_tmp_dir = '/dev/shm'
accesslog = use_accesslog
graceful_timeout = int(graceful_timeout_str)
timeout = int(timeout_str)
keepalive = int(keepalive_str)
