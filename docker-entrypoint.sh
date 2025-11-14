#!/bin/bash
set -e

echo "========================================="
echo "SOAR Platform Docker Entrypoint"
echo "========================================="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 0.1
done
echo "✓ PostgreSQL is ready"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "✓ Redis is ready"

# Initialize database
echo "Initializing database..."
python scripts/init_db.py || echo "Database already initialized"

echo "========================================="
echo "Starting SOAR Platform..."
echo "========================================="

# Execute the main command
exec "$@"
