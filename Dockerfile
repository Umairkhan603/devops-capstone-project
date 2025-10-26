# Use Python 3.9 slim as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for psycopg2 and build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        curl \
        build-essential \
        && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install Python dependencies
COPY requirements.txt .
RUN python -m pip install --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY service/ ./service/
COPY setup.cfg ./

# Create non-root user and set ownership
RUN useradd --uid 1000 theia && chown -R theia /app
USER theia

# Expose port for the app
EXPOSE 8080

# Default command to run the application
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--log-level=info", "service:app"]
