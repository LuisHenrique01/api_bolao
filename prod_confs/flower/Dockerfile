FROM python:3.10

ENV PYTHONUNBUFFERED 1

WORKDIR /code
RUN mkdir static
COPY . /code/

ARG CELERY_BROKER=${CELERY_BROKER}
ARG USER=${USER}
ARG PASSWORD=${PASSWORD}

ENV USER=${USER}
ENV PASSWORD=${PASSWORD}
ENV CELERY_BROKER=${CELERY_BROKER}


RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["sh", "-c"]

CMD ["celery flower --app tasks --loglevel info --basic_auth=$USER:$PASSWORD"]