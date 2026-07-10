#!/usr/bin/env bash
#
# Set the frisk SDK version in one or all examples, then install.
#
#   ./set-versions.sh [--example <platform/name>] [--source-env production|local]
#
#   --example <platform/name>  e.g. python/basic-langchain-agent. If omitted,
#                              all examples under examples/python and
#                              examples/typescript are updated (auto-discovered).
#   --source-env <env>         production (default) reads sdk-versions.txt and
#                              pins registry versions; local reads
#                              sdk-versions.local.txt and installs the SDK from
#                              the local checkout paths listed there.
#
# python examples:     frisk-sdk (uv add, then uv sync)
# typescript examples: @friskai/frisk-js (bun add, then bun install)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<EOF
Usage: ./set-versions.sh [--example <platform/name>] [--source-env production|local]

Options:
  --example <platform/name>  single example to update (default: all examples)
  --source-env <env>         production (sdk-versions.txt, default) or
                             local (sdk-versions.local.txt, path-based installs)
EOF
}

die() {
  echo "Error: $1" >&2
  echo >&2
  usage >&2
  exit 1
}

EXAMPLE_ID=""
SOURCE_ENV="production"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --example)
      [[ $# -ge 2 ]] || die "--example requires a value"
      EXAMPLE_ID="$2"; shift 2 ;;
    --example=*)
      EXAMPLE_ID="${1#*=}"; shift ;;
    --source-env)
      [[ $# -ge 2 ]] || die "--source-env requires a value"
      SOURCE_ENV="$2"; shift 2 ;;
    --source-env=*)
      SOURCE_ENV="${1#*=}"; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      die "unknown argument '$1'" ;;
  esac
done

case "$SOURCE_ENV" in
  production) VERSIONS_FILE="$ROOT/sdk-versions.txt" ;;
  local)      VERSIONS_FILE="$ROOT/sdk-versions.local.txt" ;;
  *) die "invalid --source-env '$SOURCE_ENV' (expected: production or local)" ;;
esac
[[ -f "$VERSIONS_FILE" ]] || die "versions file not found: $VERSIONS_FILE"

PYTHON_SDK="$(grep -E '^python=' "$VERSIONS_FILE" | head -1 | cut -d= -f2- || true)"
TYPESCRIPT_SDK="$(grep -E '^typescript=' "$VERSIONS_FILE" | head -1 | cut -d= -f2- || true)"

# Collect target example dirs (relative to repo root).
TARGET_DIRS=()
if [[ -n "$EXAMPLE_ID" ]]; then
  case "$EXAMPLE_ID" in
    python/*|typescript/*) ;;
    *) die "invalid --example '$EXAMPLE_ID' (expected python/<name> or typescript/<name>)" ;;
  esac
  # Allow deeper paths (e.g. python/foo/src/bar.py): trim to <platform>/<name>.
  EXAMPLE_ID="$(printf '%s' "$EXAMPLE_ID" | cut -d/ -f1,2)"
  [[ -d "$ROOT/examples/$EXAMPLE_ID" ]] || die "example not found: examples/$EXAMPLE_ID"
  TARGET_DIRS+=("examples/$EXAMPLE_ID")
else
  for d in "$ROOT"/examples/python/*/ "$ROOT"/examples/typescript/*/; do
    [[ -d "$d" ]] || continue
    d="${d%/}"
    TARGET_DIRS+=("${d#"$ROOT"/}")
  done
fi
[[ ${#TARGET_DIRS[@]} -gt 0 ]] || die "no examples found"

set_python() {
  local dir="$1"
  echo "==> $dir (python, source-env: $SOURCE_ENV)"
  (
    cd "$ROOT/$dir"
    uv remove --no-sync frisk-sdk
    if [[ "$SOURCE_ENV" == "production" ]]; then
      [[ -n "$PYTHON_SDK" ]] || die "python= is not set in $VERSIONS_FILE"
      uv add --no-sync "frisk-sdk~=$PYTHON_SDK"
    else
      [[ -d "$PYTHON_SDK" ]] || die "local python SDK path not found: $PYTHON_SDK"
      uv add --no-sync --editable "$PYTHON_SDK"
    fi
    uv sync
  )
}

set_typescript() {
  local dir="$1"
  echo "==> $dir (typescript, source-env: $SOURCE_ENV)"
  (
    cd "$ROOT/$dir"
    if [[ "$SOURCE_ENV" == "production" ]]; then
      [[ -n "$TYPESCRIPT_SDK" ]] || die "typescript= is not set in $VERSIONS_FILE"
      bun add "@friskai/frisk-js@^$TYPESCRIPT_SDK"
    else
      [[ -d "$TYPESCRIPT_SDK" ]] || die "local typescript SDK path not found: $TYPESCRIPT_SDK"
      bun add "@friskai/frisk-js@file:$TYPESCRIPT_SDK"
    fi
    bun install
  )
}

for dir in "${TARGET_DIRS[@]}"; do
  case "$dir" in
    examples/python/*)     set_python "$dir" ;;
    examples/typescript/*) set_typescript "$dir" ;;
  esac
done

echo "Done."
