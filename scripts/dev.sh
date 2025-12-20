#!/bin/bash

# AI Orchestrator Development Commands
# Usage: ./scripts/dev.sh <command>

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

show_help() {
    echo "AI Orchestrator Development Commands"
    echo ""
    echo "Usage: ./scripts/dev.sh <command>"
    echo ""
    echo "Commands:"
    echo "  venv          Activate virtual environment (source this script)"
    echo "  docker        Start Docker containers (Postgres + Redis)"
    echo "  docker-down   Stop Docker containers"
    echo "  migrate       Run database migrations"
    echo "  makemigration Create new migration (requires: ./scripts/dev.sh makemigration \"description\")"
    echo "  gateway       Run Gateway service (port 8000)"
    echo "  tts           Run TTS service (port 8001)"
    echo "  all           Run both Gateway and TTS services"
    echo "  web           Run Web frontend (port 3000)"
    echo "  help          Show this help message"
}

activate_venv() {
    if [ -d ".venv" ]; then
        echo "Run: source .venv/bin/activate"
        echo "(This command must be sourced, not executed)"
    else
        echo "Error: .venv directory not found"
        exit 1
    fi
}

start_docker() {
    echo "Starting Docker containers..."
    docker compose -f docker/docker-compose.yml up -d
    echo "Waiting for services to be healthy..."
    sleep 3
    docker compose -f docker/docker-compose.yml ps
}

stop_docker() {
    echo "Stopping Docker containers..."
    docker compose -f docker/docker-compose.yml down
}

run_migrate() {
    echo "Running database migrations..."
    alembic upgrade head
    echo "Migrations complete!"
}

make_migration() {
    if [ -z "$1" ]; then
        echo "Error: Migration description required"
        echo "Usage: ./scripts/dev.sh makemigration \"description\""
        exit 1
    fi
    echo "Creating migration: $1"
    alembic revision --autogenerate -m "$1"
}

run_gateway() {
    echo "Starting Gateway service on port 8000..."
    uvicorn app.gateway.main:app --reload --port 8000
}

run_tts() {
    echo "Starting TTS service on port 8001..."
    uvicorn app.tts.main:app --reload --port 8001
}

run_all() {
    echo "Starting Gateway (8000) and TTS (8001) services..."
    uvicorn app.tts.main:app --reload --port 8001 &
    TTS_PID=$!
    echo "TTS service started (PID: $TTS_PID)"

    uvicorn app.gateway.main:app --reload --port 8000 &
    GATEWAY_PID=$!
    echo "Gateway service started (PID: $GATEWAY_PID)"

    echo ""
    echo "Both services running. Press Ctrl+C to stop all."

    trap "kill $TTS_PID $GATEWAY_PID 2>/dev/null; exit" SIGINT SIGTERM
    wait
}

run_web() {
    echo "Starting Web frontend on port 3000..."
    cd app/web && npm run dev
}

case "${1:-help}" in
    venv)
        activate_venv
        ;;
    docker)
        start_docker
        ;;
    docker-down)
        stop_docker
        ;;
    migrate)
        run_migrate
        ;;
    makemigration)
        make_migration "$2"
        ;;
    gateway)
        run_gateway
        ;;
    tts)
        run_tts
        ;;
    all)
        run_all
        ;;
    web)
        run_web
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
