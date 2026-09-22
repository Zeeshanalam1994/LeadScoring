#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT"
exec uvicorn refinery_sim.backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
