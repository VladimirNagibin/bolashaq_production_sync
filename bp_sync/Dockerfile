FROM python:3.12.12-slim-bookworm

WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


COPY ./pyproject.toml /opt/app

RUN python -m pip install --no-cache-dir poetry==2.2.1 \
    && poetry config virtualenvs.create false \
    && poetry install --without dev,tests --no-interaction --no-ansi \
    && rm -rf $(poetry config cache-dir)/{cache,artifacts}

COPY ./src /opt/app

CMD ["python3", "/opt/app/main.py"]
