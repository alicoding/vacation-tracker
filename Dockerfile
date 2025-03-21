# Multi-stage build for the Vacation Tracker application

# ------- Build Stage -------
FROM python:3.9-slim AS builder

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# ------- Runtime Stage -------
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    DATABASE_PATH=/data/vacation.db

# Install runtime dependencies and gunicorn
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir gunicorn

# Copy built artifacts from builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /app /app

# Create data directory for persistent storage
RUN mkdir -p /data && chmod 777 /data

# Create a non-root user to run the application
RUN useradd -m appuser

# Set proper permissions for the application directory
RUN chmod -R 755 /app

# Switch to non-root user
USER appuser

# Expose the port the app will run on
EXPOSE 8080

# Use tini as init system to handle signals properly
ENTRYPOINT ["/usr/bin/tini", "--"]

# Command to run the application with the correct entry point
CMD gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 "run:app"
