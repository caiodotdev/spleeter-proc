import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spleeter_back.settings')

app = Celery('app')
# app = Celery('api', backend='redis://127.0.0.1:6379', broker='redis://127.0.0.1:6379')

# app.conf.update(BROKER_URL=os.environ['REDIS_URL'],
#                 CELERY_RESULT_BACKEND=os.environ['REDIS_URL'])

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
