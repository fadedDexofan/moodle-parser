from __future__ import absolute_import, unicode_literals

from kombu import Exchange, Queue

from app.settings.config import settings

RABBITMQ_LOGIN = settings.RABBITMQ_LOGIN
RABBITMQ_PASSWORD = settings.RABBITMQ_PASSWORD
RABBITMQ_HOST = settings.RABBITMQ_HOST
RABBITMQ_PORT = settings.RABBITMQ_PORT

broker_url = f'amqp://{RABBITMQ_LOGIN}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}//'
accept_content = ['json']
enable_utc = True
task_serializer = 'json'
timezone = 'UTC'
task_track_started = True
worker_hijack_root_logger = False
worker_redirect_stdouts_level = 'ERROR'
result_expires = 60 * 60 * 24

task_queues = (
    Queue('default', exchange=Exchange('default'), routing_key='default')
)
task_default_queue = 'default'
task_default_exchange = 'default'
task_default_routing_key = 'default'
