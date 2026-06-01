#!/bin/bash
# Quick start script for FastAPI

set -e

echo ""
echo "=========================================="
echo "Instagram Image Service - FastAPI Setup"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed"
    exit 1
fi

# Check if requirements are installed
echo ""
echo "1. Checking dependencies..."
pip list | grep -q fastapi || {
    echo "   Installing dependencies..."
    pip install -r requirements.txt
}
echo "   ✅ Dependencies ready"

# Check if LocalStack is running
echo ""
echo "2. Checking LocalStack..."
if ! curl -s http://localhost:4566/_localstack/health > /dev/null; then
    echo "   ❌ LocalStack is not running"
    echo "   Start it with: docker-compose up -d"
    exit 1
fi
echo "   ✅ LocalStack is running"

# Setup LocalStack resources
echo ""
echo "3. Setting up LocalStack resources..."
python3 setup_localstack.py 2>/dev/null || {
    echo "   Skipping (resources may already exist)"
}
echo "   ✅ Resources ready"

# Start API
echo ""
echo "=========================================="
echo "🚀 Starting FastAPI Server"
echo "=========================================="
echo ""
echo "📚 API Docs:    http://localhost:8000/docs"
echo "📖 ReDoc:       http://localhost:8000/redoc"
echo "❤️  Health:      http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m api.main
