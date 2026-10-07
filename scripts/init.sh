#!/bin/sh

DB_PATH="/app/data/dummy_data.db"

if [ ! -f "$DB_PATH" ]; then
    echo "Database not found. Creating dummy database..."
    python /app/data/seed_database.py
else
    echo "Database already exists."
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000