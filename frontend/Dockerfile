################ 1. Base image - Alpine (rất nhẹ) ################
FROM python:3.12-alpine AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

################# 2. Builder stage ################
FROM base AS builder

# Alpine dùng apk, không phải apt-get
RUN apk add --no-cache \
        build-base \
        git

WORKDIR /build

# Copy dependency files
COPY pyproject.toml ./

# Tạo venv và cài dependencies dùng pip
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip setuptools wheel && \
    /opt/venv/bin/pip install --no-cache-dir -e .

# Xóa cache và __pycache__
RUN find /opt/venv -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete && \
    find /opt/venv -type f -name "*.pyo" -delete

##################### 3. Runtime stage #####################
FROM base AS runtime

# Cài runtime libs tối thiểu
RUN apk add --no-cache \
        ca-certificates \
        curl

# Tạo non-root user
RUN adduser -D -h /home/appuser appuser

WORKDIR /app

# Copy venv từ builder
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv

# Copy source code
COPY --chown=appuser:appuser . .

USER appuser

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

LABEL maintainer="duc78240@email.com" \
    version="1.0" \
    description="Frontend Streamlit for AI Chatbot"

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--logger.level=info"]

# cd frontend && docker build -f Dockerfile -t ai-chatbot-ui:1.0 .
