FROM python:3.10

ENV PYTHONUNBUFFERED 1

WORKDIR /code
RUN --mount=type=secret,id=_env,dst=/etc/secrets/.env cat /code/.env
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /code/
