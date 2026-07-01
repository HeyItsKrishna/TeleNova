#!/bin/bash
set -euo pipefail

echo "=== TeleNova AI Support - Local Development Setup ==="

if ! command -v python3 &>/dev/null; then
  echo "ERROR: Python 3.11+ is required."
  exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: ${PYTHON_VERSION}"

if [[ ! -f ".env" ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — please fill in your credentials."
fi

if command -v docker &>/dev/null; then
  echo "Starting local Postgres (AlloyDB-compatible) via Docker Compose..."
  docker compose up -d postgres
  echo "Waiting for Postgres to become healthy..."
  until [ "$(docker inspect -f '{{.State.Health.Status}}' telenova-postgres 2>/dev/null)" == "healthy" ]; do
    sleep 1
  done
  echo "Postgres is ready on localhost:5432 (schema + seed data loaded automatically)."
else
  echo "WARNING: Docker not found. Install Docker or point DATABASE_URL at an existing Postgres/AlloyDB instance."
fi

echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Loading knowledge base..."
python3 -c "
from app.rag.vector_store import knowledge_base
count = knowledge_base.load_knowledge_base(force_reload=True)
print(f'Loaded {count} document chunks into vector store.')
"

echo ""
echo "=== Setup Complete ==="
echo "Start the server with:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "Or with hot-reload for development:"
echo "  uvicorn main:app --reload --port 8080"
echo ""
echo "API Documentation:"
echo "  http://localhost:8080/docs"
echo "  http://localhost:8080/redoc"
