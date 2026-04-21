FROM python:3.13-slim

WORKDIR /app

# Prevent Python from writing .pyc files and enable stdout logging

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies needed by Python packages
# libffi-dev: required by passlib[argon2]
# libpq-dev: required by asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi-dev \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first — Docker layer caching means this slow step
# only reruns when requirements.txt changes, not on every code change.
# The spaCy model (en_core_web_sm) is pinned in requirements.txt as a
# direct wheel URL, so pip installs it here too.
  COPY requirements.txt .                                                                                                                                                                                         
  RUN pip install --no-cache-dir torch==2.11.0 \            
      --index-url https://download.pytorch.org/whl/cpu
  RUN pip install --no-cache-dir -r requirements.txt  

# Copy application code (includes vendored HTMX and PicoCSS under
# app/static/vendor/ — no CDN, no build-time downloads)
COPY . .

# Create the uploads directory
RUN mkdir -p /app/uploads

# Run as non-root user for security
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["./scripts/start.sh"]