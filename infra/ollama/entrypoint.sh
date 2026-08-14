#!/bin/sh
# Start Ollama, wait for its API, and make the configured generation model
# available before Docker reports the service healthy.

set -eu

OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:0.5b}"
OLLAMA_STARTUP_TIMEOUT="${OLLAMA_STARTUP_TIMEOUT:-60}"
OLLAMA_PULL_RETRIES="${OLLAMA_PULL_RETRIES:-3}"
export OLLAMA_MODEL

ollama serve &
server_pid=$!

cleanup() {
  kill "$server_pid" 2>/dev/null || true
  wait "$server_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

startup_attempt=0
until ollama list >/dev/null 2>&1; do
  if ! kill -0 "$server_pid" 2>/dev/null; then
    wait "$server_pid"
    exit 1
  fi

  startup_attempt=$((startup_attempt + 1))
  if [ "$startup_attempt" -ge "$OLLAMA_STARTUP_TIMEOUT" ]; then
    echo "Ollama did not become ready within ${OLLAMA_STARTUP_TIMEOUT}s" >&2
    exit 1
  fi
  sleep 1
done

pull_attempt=1
pull_delay=2
until ollama pull "$OLLAMA_MODEL"; do
  if [ "$pull_attempt" -ge "$OLLAMA_PULL_RETRIES" ]; then
    echo "Failed to pull Ollama model '${OLLAMA_MODEL}' after ${OLLAMA_PULL_RETRIES} attempts" >&2
    exit 1
  fi

  echo "Ollama model pull failed; retrying in ${pull_delay}s (attempt $((pull_attempt + 1))/${OLLAMA_PULL_RETRIES})" >&2
  sleep "$pull_delay"
  pull_attempt=$((pull_attempt + 1))
  pull_delay=$((pull_delay * 2))
done

touch /tmp/openuni-generation-model-ready

wait "$server_pid"
