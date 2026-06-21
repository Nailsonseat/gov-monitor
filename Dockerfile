# syntax=docker/dockerfile:1

FROM python:3.11-slim-bookworm
WORKDIR /app

# Copy only site-packages (portable). Do NOT copy .venv/bin — symlinks point at the host.
COPY .venv/lib/python3.11/site-packages /app/deps
ENV PYTHONPATH="/app:/app/deps"

COPY src/ /app/src/
COPY pyproject.toml README.md /app/

CMD ["python", "-m", "src.main"]
