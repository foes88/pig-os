FROM python:3.12-slim

WORKDIR /app

# Install uv (fast Python package manager)
RUN pip install uv --no-cache-dir

# Copy dependency files first (layer cache)
COPY pyproject.toml .

# Install all dependencies into the system Python
RUN uv pip install --system -e ".[dev]" 2>/dev/null || uv pip install --system \
    fastapi[standard] sqlalchemy[asyncio] asyncpg alembic psycopg2-binary \
    pydantic-settings python-jose[cryptography] passlib[bcrypt] \
    redis arq python-multipart httpx

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
