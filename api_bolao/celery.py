import os
from api_bolao.celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_bolao.settings')

app = Celery('api_bolao')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
