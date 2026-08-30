FROM python:3.13-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

LABEL maintainer="Max Mecklin <max@meckl.in>"

WORKDIR /bot

ADD . /bot

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --compile-bytecode

ENV PYTHONPATH="${PYTHONPATH}:/bot"

RUN ["chmod", "+x", "/bot/docker-entrypoint.sh"]

ENTRYPOINT ["/bot/docker-entrypoint.sh"]
CMD ["uv", "run", "main.py"]
