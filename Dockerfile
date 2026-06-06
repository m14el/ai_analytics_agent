# ============================================================
# AI Analytics Agent — Dockerfile
# Multi-stage production build
# ============================================================

# ── Stage 1: Dependencies ──────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system deps for pyodbc (optional MSSQL support)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ unixodbc-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ───────────────────────────────────────
FROM python:3.12-slim

# Labels
LABEL maintainer="AI Analytics Agent"
LABEL version="1.0.0"
LABEL description="AI-агент аналитики прибыльности проектов"

# Install runtime deps only (ODBC driver for MSSQL if needed)
RUN apt-get update && \
    apt-get install -y --no-install-recommends unixodbc curl && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Copy application code
COPY . .

# Create data directory with correct permissions
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with production settings
ENV APP_ENV=production
ENV APP_DEBUG=false

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--access-log"]
