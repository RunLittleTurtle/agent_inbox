# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY src/config_api/requirements.txt ./requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire src directory (agents + config_api + interface_uis_config)
COPY src/ ./src/

# Python path includes /app so imports work correctly
ENV PYTHONPATH=/app

# Change to config_api for runtime
WORKDIR /app/src/config_api

# Expose port
EXPOSE 8000

# Start command using hypercorn
CMD hypercorn main:app --bind 0.0.0.0:${PORT:-8000}
