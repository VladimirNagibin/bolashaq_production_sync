FROM python:3.12.12-slim-bookworm

# Install netcat for waiting services
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appgroup && useradd -r -g appgroup appuser

RUN mkdir -p /opt/app/logs && chown appuser:appgroup /opt/app/logs
# RUN mkdir -p /opt/app/logs && chmod 755 /opt/app/logs

WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY ./pyproject.toml /opt/app

RUN python -m pip install --no-cache-dir poetry==2.2.1 \
    && poetry config virtualenvs.create false \
    && poetry install --without dev,tests --no-interaction --no-ansi \
    && rm -rf $(poetry config cache-dir)/{cache,artifacts}

COPY ./src /opt/app

COPY ./entrypoint.sh /opt/app
# Make entrypoint executable
USER appuser

RUN chmod +x /opt/app/entrypoint.sh

# Create non-root user
# RUN useradd --create-home --shell /bin/bash app
# USER app

ENTRYPOINT ["/opt/app/entrypoint.sh"]
