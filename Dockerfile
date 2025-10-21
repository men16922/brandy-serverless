# Streamlit on AWS App Runner (hardened)
FROM python:3.11-slim

WORKDIR /app

# 1) System deps
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 2) Python deps
COPY requirements-streamlit.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# 3) App code (src/streamlit 안에 app.py가 있다고 가정)
COPY src/streamlit/ /app/

# 4) ECS Fargate with ALB - fixed port 8501
ENV PORT=8501
EXPOSE 8501

# 5) Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8501/_stcore/health || exit 1

# 6) Run with WebSocket support for ALB
CMD ["streamlit", "run", "/app/app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--server.enableCORS=false", \
    "--server.enableXsrfProtection=false", \
    "--server.enableWebsocketCompression=true", \
    "--server.fileWatcherType=none"]
