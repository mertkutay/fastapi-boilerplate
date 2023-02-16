FROM python:3.10-slim-bullseye

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update && apt-get install --no-install-recommends -y \
  build-essential \
  libpq-dev \
  gettext \
  curl \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry && \
    poetry config virtualenvs.create false

ARG INSTALL_DEV=false

COPY pyproject.toml poetry.lock /app/
RUN --mount=type=cache,target=/root/.cache \
    poetry install --no-root $(if [ $INSTALL_DEV != 'true' ]; then echo '--no-dev'; fi)

COPY ./scripts/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//g' /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY ./scripts/start.sh /start.sh
RUN sed -i 's/\r$//g' /start.sh
RUN chmod +x /start.sh

COPY ./scripts/start-local.sh /start-local.sh
RUN sed -i 's/\r$//g' /start-local.sh
RUN chmod +x /start-local.sh

COPY . /app

ENV PYTHONPATH=/app
ENV PORT=8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/start.sh"]
