FROM python:3.12.12-slim-bookworm

WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install netcat for waiting services
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/app/logs && chmod 755 /opt/app/logs

COPY ./pyproject.toml /opt/app

RUN python -m pip install --no-cache-dir poetry==2.2.1 \
    && poetry config virtualenvs.create false \
    && poetry install --without dev,tests --no-interaction --no-ansi \
    && rm -rf $(poetry config cache-dir)/{cache,artifacts}

COPY ./src /opt/app

COPY ./entrypoint.sh /opt/app
# Make entrypoint executable
RUN chmod +x /opt/app/entrypoint.sh

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

ENTRYPOINT ["/opt/app/entrypoint.sh"]
