#!/usr/bin/env bash
set -euo pipefail

# Build a Python 3.11 dependency tree for the container image.
# Site-packages are copied into Docker; .venv/bin symlinks are NOT (host-specific).
cd "$(dirname "$0")/.."

build_venv_in_docker() {
  echo "Creating .venv inside Python 3.11 Docker (preferred)..."
  rm -rf .venv
  docker run --rm \
    --network host \
    -v "$(pwd)":/app \
    -w /app \
    ghcr.io/astral-sh/uv:python3.11-bookworm-slim \
    sh -c "uv lock && uv sync --frozen --no-dev"
}

build_venv_on_host() {
  echo "Creating .venv on host with uv-managed Python 3.11..."
  uv python install 3.11
  rm -rf .venv
  uv lock
  uv sync --frozen --no-dev --python 3.11
}

if [ ! -d .venv/lib/python3.11/site-packages ]; then
  if ! build_venv_in_docker 2>/dev/null; then
    echo "Docker venv build failed (network/DNS). Falling back to host uv Python 3.11..."
    build_venv_on_host
  fi
else
  echo "Reusing existing .venv (run 'rm -rf .venv' to force refresh)."
fi

if ! grep -q "version_info = 3.11" .venv/pyvenv.cfg; then
  echo "ERROR: .venv must use Python 3.11 to match the container image." >&2
  exit 1
fi

if ! .venv/bin/python -c "import sqlalchemy_cockroachdb" 2>/dev/null; then
  echo "ERROR: sqlalchemy_cockroachdb missing from .venv. Re-run after uv lock." >&2
  exit 1
fi

echo "Building pipeline image..."
DOCKER_BUILDKIT=1 docker compose build --no-cache pipeline
echo "Done. Run: docker compose up pipeline"
