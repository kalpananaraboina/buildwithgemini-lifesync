#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
export AGENT_ENGINE_RESOURCE_NAME="projects/976432994584/locations/us-east1/reasoningEngines/7912039493987729408"
export AGENT_DIRECTORY="app"
export PORT="${PORT:-8081}"
echo "Starting LifeSync Chat Frontend on http://127.0.0.1:${PORT}..."
exec .venv/bin/python main.py
