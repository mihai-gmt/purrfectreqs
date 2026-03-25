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
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first — Docker layer caching means this slow step
# only reruns when requirements.txt changes, not on every code change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download the spaCy English model
RUN python -m spacy download en_core_web_sm

# Download HTMX and PicoCSS — no CDN in production
RUN mkdir -p app/static/js app/static/css && \
    curl -L https://unpkg.com/htmx.org/dist/htmx.min.js \
        -o app/static/js/htmx.min.js && \
    curl -L https://unpkg.com/@picocss/pico/css/pico.min.css \
        -o app/static/css/pico.min.css

# Copy application code
COPY . .

# Create the uploads directory
RUN mkdir -p /app/uploads

# Run as non-root user for security
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["./scripts/start.sh"]