FROM python:3.9-alpine

LABEL maintainer="Max Mecklin <max@meckl.in>"

RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/community" > /etc/apk/repositories
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories

RUN apk update && apk add python3-dev gcc libc-dev postgresql-dev build-base curl

COPY . /bot

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN ["chmod", "+x", "/docker-entrypoint.sh"]

WORKDIR /bot

RUN pip3.9 install -r requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/bot"

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python3.9", "main.py"]
