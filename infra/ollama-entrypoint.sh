#!/bin/sh
# Start Ollama, wait until its API is ready, and make the configured generation
# model available before Docker reports the service healthy.

set -eu

OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:0.5b}"
export OLLAMA_MODEL

ollama serve &
server_pid=$!

cleanup() {
  kill "$server_pid" 2>/dev/null || true
  wait "$server_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

until curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; do
  if ! kill -0 "$server_pid" 2>/dev/null; then
    wait "$server_pid"
    exit 1
  fi
  sleep 1
done

ollama pull "$OLLAMA_MODEL"
touch /tmp/openuni-generation-model-ready

wait "$server_pid"
