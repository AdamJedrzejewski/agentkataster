#!/bin/bash
# Quick start script for AgentKataster

set -e

echo "🗺️  AgentKataster - Quick Start"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo "⚠️  Please edit .env with your settings before continuing"
    exit 0
fi

# Start Docker services
echo "Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Check if database is initialized
echo "Checking database status..."
if docker-compose exec -T postgres psql -U postgres -d agentkataster -c "SELECT 1 FROM municipalities LIMIT 1" &> /dev/null; then
    echo "✓ Database already initialized"
else
    echo "Initializing database..."
    docker-compose exec -T worker python -m src.main init
    echo "✓ Database initialized"
fi

# Show status
echo ""
echo "Getting current status..."
docker-compose exec -T worker python -m src.main status

echo ""
echo "================================"
echo "✓ AgentKataster is ready!"
echo ""
echo "Available commands:"
echo "  docker-compose logs -f worker     # View logs"
echo "  docker-compose exec worker python -m src.main status    # Check status"
echo "  docker-compose exec worker python -m src.main start     # Start scraping"
echo ""
echo "Access Flower (Celery monitoring) at: http://localhost:5555"
echo "(Run: docker-compose exec worker celery -A src.worker.celery_app flower)"
