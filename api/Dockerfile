# PigOS API — production image (non-root, no reload).
# Dev hot-reload is provided by docker-compose.yml's command override.
FROM python:3.12-slim

WORKDIR /app

# uv + non-root user
RUN pip install --no-cache-dir uv \
    && useradd -m -u 1000 appuser

# Dependencies (layer cache)
COPY pyproject.toml .
RUN uv pip install --system --no-cache-dir \
    "fastapi[standard]" "sqlalchemy[asyncio]" asyncpg alembic psycopg2-binary \
    "pydantic-settings" "python-jose[cryptography]" "passlib[bcrypt]" \
    redis arq python-multipart httpx email-validator

# App source
COPY . .
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').getcode()==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
