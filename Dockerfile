# === Aurum Ghana Backend Dockerfile ===
# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Production
FROM python:3.12-slim AS production

LABEL maintainer="Aurum Ghana <dev@aurumghana.com>"
LABEL description="Aurum Ghana API - Flask Backend"

# Create non-root user
RUN groupadd --gid 1000 aurum \
    && useradd --uid 1000 --gid aurum --shell /bin/bash --create-home aurum

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application
COPY --chown=aurum:aurum backend/ ./backend/
COPY --chown=aurum:aurum migrations/ ./migrations/
COPY --chown=aurum:aurum alembic.ini ./
COPY --chown=aurum:aurum .env.example ./

# Set env vars
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" \
    || exit 1

# Run as non-root user
USER aurum

# Gunicorn with 4 workers
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 --access-logfile - --error-logfile - backend.wsgi:app"]
