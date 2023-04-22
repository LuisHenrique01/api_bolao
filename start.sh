python manage.py migrate;
gunicorn api_bolao.wsgi:application --bind 0.0.0.0:8000;
celery -A api_bolao worker --loglevel=INFO;