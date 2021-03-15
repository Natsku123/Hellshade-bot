FROM tiangolo/uvicorn-gunicorn:python3.8-alpine3.10

LABEL maintainer="Max Mecklin <max@meckl.in>"

RUN apk update && \
    apk add --virtual build-deps gcc python-dev musl-dev && \
    apk add --no-cache openssl-dev libffi-dev g++ && \
    apk add postgresql-dev && \
    apk add netcat-openbsd && \
    apk add postgresql-client


COPY . /app

WORKDIR /app

ENV PYTHONPATH "${PYTHONPATH}:/app"

RUN pip install -r requirements.txt
