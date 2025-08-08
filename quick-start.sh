#!/bin/bash

# Quick Start Script for Transcript Summarizer
# This script sets up the development environment and starts the application

set -e

echo "🚀 Transcript Summarizer Quick Start"
echo "====================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install it and try again."
    exit 1
fi

echo "✅ Docker is running"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data/chroma
mkdir -p data/redis
mkdir -p logs

# Pull the latest images
echo "📦 Pulling Docker images..."
docker-compose pull

# Build the application images
echo "🔨 Building application images..."
docker-compose build

# Start the services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are healthy
echo "🔍 Checking service health..."

# Function to check if a service is healthy
check_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is healthy"
            return 0
        fi
        echo "⏳ Waiting for $service_name... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done

    echo "❌ $service_name failed to start"
    return 1
}

# Check API health
check_service "API" "http://localhost:8000/health"

# Check Redis
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis is not responding"
fi

# Check ChromaDB
check_service "ChromaDB" "http://localhost:8001/api/v1/heartbeat"

# Check Gradio Frontend
check_service "Frontend" "http://localhost:7860"

echo ""
echo "🎉 All services are running!"
echo ""
echo "📱 Access the application:"
echo "   • Web Interface: http://localhost:7860"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • API Health: http://localhost:8000/health"
echo "   • ChromaDB Admin: http://localhost:8001"
echo ""
echo "📋 Useful commands:"
echo "   • View logs: docker-compose logs -f"
echo "   • Stop services: docker-compose down"
echo "   • Restart services: docker-compose restart"
echo "   • Update images: docker-compose pull && docker-compose up -d"
echo ""
echo "📚 For more information, see:"
echo "   • README.md - General documentation"
echo "   • CLOUD_DEPLOYMENT.md - Cloud deployment guide"
echo ""
echo "Happy summarizing! 🎯"
