# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY src/config_api/requirements.txt ./requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy ui_config.py from root (needed for global config)
COPY ui_config.py ./ui_config.py

# Copy entire src directory (agents + config_api)
COPY src/ ./src/

# Python path includes /app so imports work correctly
ENV PYTHONPATH=/app

# Change to config_api for runtime
WORKDIR /app/src/config_api

# Expose port
EXPOSE 8000

# Start command using hypercorn
CMD hypercorn main:app --bind 0.0.0.0:${PORT:-8000}
