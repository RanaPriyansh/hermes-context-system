#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

VENV_DIR="$TMP_DIR/venv"
python3 -m venv "$VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

python -m pip install --quiet --upgrade pip
python -m pip install --quiet -e "$ROOT_DIR"

mkdir -p "$TMP_DIR/vault/protocols" "$TMP_DIR/rag" "$TMP_DIR/.hermes/memory"
printf 'CLI protocol\n' > "$TMP_DIR/vault/protocols/cli-protocol.md"
printf '{"entries":[{"content":"cli memory entry"}]}' > "$TMP_DIR/.hermes/memory/memory.json"

export HERMES_VAULT_PATH="$TMP_DIR/vault"
export HERMES_RAG_PATH="$TMP_DIR/rag"
export HERMES_HOME="$TMP_DIR/.hermes"

L0_OUT="$(hermes-context l0)"
[[ "$L0_OUT" == *"=== IDENTITY ==="* ]]

MANAGER_OUT="$(hermes-context-manager load --tier L0)"
[[ "$MANAGER_OUT" == *"=== HERMES IDENTITY ==="* ]]
[[ "$MANAGER_OUT" == *"cli memory entry"* ]]

hermes-session-preloader >/dev/null

CACHE_FILE="$(find "$TMP_DIR/.hermes/context-cache" -maxdepth 1 -name 'session-*.json' -print -quit || true)"
[[ -n "$CACHE_FILE" ]]

python -m compileall \
  "$ROOT_DIR/context_manager.py" \
  "$ROOT_DIR/hermes_context.py" \
  "$ROOT_DIR/hermes_paths.py" \
  "$ROOT_DIR/integration.py" \
  "$ROOT_DIR/rag_integration.py" \
  "$ROOT_DIR/session_preloader.py" \
  "$ROOT_DIR/smart_preloader.py" \
  "$ROOT_DIR/vault_integration.py" \
  "$ROOT_DIR/tests" >/dev/null

echo "OK: main Hermes context flow validated in isolated temp environment."
