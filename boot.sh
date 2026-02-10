#!/bin/bash

# Wait for database
echo "Waiting for database..."
while ! nc -z db 3306; do
  sleep 0.1
done
echo "Database started"

# Run migrations if needed (placeholder for now)
# flask db upgrade

# Start application
exec gunicorn -b 0.0.0.0:5000 wsgi:app
