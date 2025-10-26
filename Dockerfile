FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies and Python requirements
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY service/ ./service/

# Create non-root user and set ownership
RUN useradd --uid 1000 theia && chown -R theia /app
USER theia

EXPOSE 8080
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--log-level=info", "service:app"]
