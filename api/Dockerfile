# PigOS API — production image (non-root, no reload).
# Dev hot-reload is provided by docker-compose.yml's command override.
FROM python:3.12-slim

WORKDIR /app

# uv + non-root user
RUN pip install --no-cache-dir uv \
    && useradd -m -u 1000 appuser

# Dependencies (layer cache)
COPY pyproject.toml .
# ★ pyproject 의 dependencies 를 **그대로** 설치한다.
#   예전에는 여기에 패키지를 손으로 나열했다. pyproject 에 의존성을 추가해도 이미지에
#   들어가지 않아 배포 후에야 ModuleNotFoundError 로 죽는다(2026-08-26 실측: markdown).
#   같은 이유로 boto3·tzdata 도 빠져 있었다 — 목록 이중관리는 반드시 어긋난다.
RUN uv pip install --system --no-cache-dir -r pyproject.toml

# App source
COPY . .
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').getcode()==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
