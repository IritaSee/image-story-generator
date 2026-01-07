# Image Story Generator - Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies for Pillow and build tools
RUN apt-get update \ 
    && apt-get install -y --no-install-recommends \
       build-essential \
       libjpeg62-turbo-dev \
       zlib1g-dev \
       libpng-dev \
       libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better caching)
COPY requirements.txt ./
RUN pip install --upgrade pip \ 
    && pip install -r requirements.txt

# Copy application source
COPY . .

# Create uploads directory
RUN mkdir -p static/uploads

# Default environment (override in compose if needed)
ENV FLASK_ENV=production

EXPOSE 5000

# Use Gunicorn for production serving
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
