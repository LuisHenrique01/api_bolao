FROM python:3.10

ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /code/

RUN --mount=type=secret,id=_env,dst=/etc/secrets/.env cat .env

RUN ls 

CMD ["sh", "-c", "python manage.py migrate && \
    gunicorn myproject.wsgi:application --bind 0.0.0.0:8000 && \
    celery -A myproject worker --loglevel=INFO"]