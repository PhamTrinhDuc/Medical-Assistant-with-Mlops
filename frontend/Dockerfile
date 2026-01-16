################ 1. Base image - Alpine (Tối ưu nhẹ) ################
FROM python:3.12-alpine AS base

# Cài đặt các biến môi trường chuẩn cho Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

################# 2. Builder stage - Cài đặt dependencies ################
FROM base AS builder

# Chép công cụ uv từ image chính thức vào builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Alpine dùng apk. Cài đặt các thư viện cần để build (nếu có package C)
RUN apk add --no-cache build-base git

WORKDIR /build

# Chép pyproject.toml và uv.lock (Đây là chìa khóa để vá lỗi CVE)
# uv sẽ dùng uv.lock để cài đúng bản jaraco.context >= 6.1.0 của bạn
COPY pyproject.toml uv.lock ./

# Cài đặt dependencies vào /app/.venv thay vì hệ thống
# --frozen: ép buộc dùng uv.lock, không được tự ý update bản cũ dính lỗi
# --no-install-project: cài thư viện trước để tận dụng cache của Docker
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Chép toàn bộ source code của bạn vào
COPY . .

# Cài đặt chính project của bạn (frontend/app.py...)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

##################### 3. Runtime stage - Chạy ứng dụng #####################
FROM base AS runtime

# Cài đặt các thư viện cần thiết khi chạy (ca-certificates cho API/HTTPS)
RUN apk add --no-cache ca-certificates curl

# Tạo user để bảo mật (không chạy bằng root)
RUN adduser -D -h /home/appuser appuser

WORKDIR /app

# Chỉ chép môi trường ảo (.venv) từ builder sang để giữ image nhẹ
COPY --from=builder --chown=appuser:appuser /build/.venv /app/.venv
# Chép source code
COPY --chown=appuser:appuser . .

USER appuser

# Đưa môi trường ảo của uv vào PATH để các lệnh 'streamlit' hoạt động
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

LABEL maintainer="duc78240@email.com" \
    version="1.1" \
    description="Frontend Streamlit with UV and Security Patches"

EXPOSE 8501

# Healthcheck để Kubernetes biết container vẫn sống
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:8501/_stcore/health || exit 1

# Lệnh chạy ứng dụng
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--logger.level=info"]

     
# cd frontend && docker build -f Dockerfile -t ai-chatbot-ui:1.0 .
