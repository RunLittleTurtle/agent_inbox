# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy config_api requirements
COPY config_api/requirements.txt ./config_api/

# Install dependencies
RUN pip install --no-cache-dir -r config_api/requirements.txt

# Copy entire src directory (needed for agent imports)
COPY . .

# Change to config_api directory for runtime
WORKDIR /app/config_api

# Expose port
EXPOSE 8000

# Start command using hypercorn
CMD hypercorn main:app --bind 0.0.0.0:${PORT:-8000}
