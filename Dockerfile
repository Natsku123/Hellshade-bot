FROM python:3.12-slim

LABEL maintainer="Max Mecklin <max@meckl.in>"

WORKDIR /bot

COPY ./requirements.txt /bot/requirements.txt

RUN pip3.12 install -r requirements.txt

COPY . /bot

ENV PYTHONPATH "${PYTHONPATH}:/bot"

RUN ["chmod", "+x", "/bot/docker-entrypoint.sh"]

ENTRYPOINT ["/bot/docker-entrypoint.sh"]
CMD ["python3.12", "main.py"]
