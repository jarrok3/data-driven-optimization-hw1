#!/bin/sh

ENV_PATH="/app/.env"
DB_PATH="/app/data/dummy_data.db"

# Load environment variables from .env
if [ -f "$ENV_PATH" ]; then
    echo "Loading environment variables from .env..."

    set -a
    . "$ENV_PATH"
    set +a
else
    echo "Warning: .env file not found."
fi


# Create database if it does not exist
if [ ! -f "$DB_PATH" ]; then
    echo "Database not found. Creating dummy database..."
    python /app/data/seed_database.py
else
    echo "Database already exists."
fi


# Start application
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000