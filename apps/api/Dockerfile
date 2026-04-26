FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY adapters ./adapters
COPY agent ./agent
COPY apps ./apps
COPY core ./core
COPY domain ./domain
COPY mcp ./mcp
COPY pipelines ./pipelines
COPY services ./services
COPY storage ./storage

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
