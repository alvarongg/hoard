#!/bin/bash
set -e

echo "⏳ Waiting for database..."
until pg_isready -h db -U "${POSTGRES_USER:-hoard}" -d "${POSTGRES_DB:-hoard}" -q; do
  sleep 1
done
echo "✅ Database is ready."

echo "🌱 Running seed..."
python seed.py

echo "🚀 Starting server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
