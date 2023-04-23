FROM python:3.10

ENV PYTHONUNBUFFERED 1

WORKDIR /code
RUN mkdir static
COPY . /code/

ARG CELERY_BROKER=${CELERY_BROKER}

ENV CELERY_BROKER=${CELERY_BROKER}

RUN pip install --no-cache-dir -r requirements.txt

CMD ["sh", "-c", "celery flower --app tasks --loglevel info"]