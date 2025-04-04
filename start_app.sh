#!/bin/bash

# Exit on any error
set -e

# Clean up existing resources
echo "Cleaning up Docker environment..."
docker-compose down --remove-orphans --volumes || {
  echo "Warning: Failed to clean up some resources, continuing..."
}
docker system prune -f
docker volume prune -f

# Build the Docker containers with no-cache for a fresh build
echo "Building Docker containers..."
docker-compose build --no-cache || {
  echo "Error: Build failed. Check Dockerfile or requirements.txt."
  exit 1
}

# Start the containers in detached mode
echo "Starting Docker containers..."
docker-compose up -d || {
  echo "Error: Failed to start containers."
  exit 1
}

# Wait for the database to be ready (using pg_isready)
echo "Waiting for database to initialize..."
MAX_ATTEMPTS=30
COUNT=0
until docker-compose exec -T db pg_isready -h localhost -p 5432; do
  COUNT=$((COUNT + 1))
  if [ $COUNT -ge $MAX_ATTEMPTS ]; then
    echo "Error: Database did not become ready in time."
    docker-compose logs db
    exit 1
  fi
  echo "Database not ready yet, attempt $COUNT/$MAX_ATTEMPTS..."
  sleep 2
done
echo "Database is ready!"

# Run migrations in specific order
echo "Running migrations..."
docker-compose exec -T web python manage.py makemigrations user || {
  echo "Error: Failed to create user migrations."
  exit 1
}
docker-compose exec -T web python manage.py makemigrations products || {
  echo "Error: Failed to create products migrations."
  exit 1
}
docker-compose exec -T web python manage.py makemigrations || {
  echo "Error: Failed to create remaining migrations."
  exit 1
}
docker-compose exec -T web python manage.py migrate || {
  echo "Error: Failed to apply migrations."
  docker-compose logs web
  exit 1
}

# Collect static files (optional, uncomment if needed)
# echo "Collecting static files..."
# docker-compose exec -T web python manage.py collectstatic --noinput || {
#   echo "Error: Failed to collect static files."
#   exit 1
# }

# Check container