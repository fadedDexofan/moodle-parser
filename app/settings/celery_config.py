from app.settings.config import settings

REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT
REDIS_PASSWORD = settings.REDIS_PASSWORD or ''

broker_url = f'redis://{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0'
accept_content = ['pickle']
enable_utc = True
task_acks_late = True
task_serializer = 'pickle'
timezone = 'UTC'
task_track_started = False
worker_hijack_root_logger = False
# worker_redirect_stdouts_level = 'ERROR'
result_expires = 60 * 60 * 24
