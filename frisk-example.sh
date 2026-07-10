#!/usr/bin/env bash
#
# Run any example in this repo against a chosen Frisk environment.
#
#   ./frisk-example.sh <path> [--frisk-env local|staging|production] [--example <filename>] [args...]
#
#   <path>                 Path under examples/, e.g. python/basic-langchain-agent.
#                          A directory runs src/<filename>.py|.ts in it; a file
#                          (e.g. python/foo/src/bar.py) is exec'd directly.
#   --frisk-env <env>      Frisk environment: local, staging, or production
#                          (default: local)
#   --example <filename>   Entry file name without extension (default: main).
#                          Only used when <path> is a directory.
#   args...                Anything else is forwarded verbatim, in order, to
#                          the underlying script. Use `--` to force everything
#                          after it to be forwarded (even --frisk-env/--example).
#
# All variables come from the root .env and are injected verbatim, except
# FRISK_API_KEY, which is taken from FRISK_API_KEY_<ENV> depending on
# --frisk-env. For non-local environments, the matching entry in
# frisk-envs.json wins over anything in .env.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$ROOT/.env"
FRISK_ENVS_JSON="$ROOT/frisk-envs.json"

usage() {
  cat <<EOF
Usage: ./frisk-example.sh <path> [--frisk-env local|staging|production] [--example <filename>] [args...]

<path> is relative to examples/. A directory runs src/main.py|.ts (or
--example); a file (e.g. python/foo/src/bar.py) is exec'd directly.

Available examples:
$(for d in "$ROOT"/examples/*/*/; do d="${d%/}"; [[ -d "$d" ]] && echo "  ${d#"$ROOT"/examples/}"; done)

Options:
  --frisk-env <env>     local, staging, or production (default: local)
  --example <filename>  entry file name without extension (default: main)
  --                    forward all remaining args to the underlying script

All other arguments are forwarded to the underlying script in order.
EOF
}

die() {
  echo "Error: $1" >&2
  echo >&2
  usage >&2
  exit 1
}

EXAMPLE_ID=""
FRISK_ENV="local"
ENTRY="main"
FORWARD=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --frisk-env)
      [[ $# -ge 2 ]] || die "--frisk-env requires a value"
      FRISK_ENV="$2"; shift 2 ;;
    --frisk-env=*)
      FRISK_ENV="${1#*=}"; shift ;;
    --example)
      [[ $# -ge 2 ]] || die "--example requires a value"
      ENTRY="$2"; shift 2 ;;
    --example=*)
      ENTRY="${1#*=}"; shift ;;
    -h|--help)
      usage; exit 0 ;;
    --)
      shift
      FORWARD+=("$@")
      break ;;
    *)
      if [[ -z "$EXAMPLE_ID" ]]; then
        EXAMPLE_ID="$1"
      else
        FORWARD+=("$1")
      fi
      shift ;;
  esac
done

[[ -n "$EXAMPLE_ID" ]] || die "missing <example> argument"

case "$FRISK_ENV" in
  local|staging|production) ;;
  *) die "invalid --frisk-env '$FRISK_ENV' (expected: local, staging, or production)" ;;
esac

PLATFORM="${EXAMPLE_ID%%/*}"
case "$PLATFORM" in
  python)     EXT="py" ;;
  typescript) EXT="ts" ;;
  *) die "cannot determine platform from '$EXAMPLE_ID' (expected python/... or typescript/...)" ;;
esac

REST="${EXAMPLE_ID#*/}"
[[ "$REST" != "$EXAMPLE_ID" && -n "$REST" ]] || die "expected <platform>/<example>[/path], got '$EXAMPLE_ID'"
EXAMPLE_NAME="${REST%%/*}"
EXAMPLE_DIR="$ROOT/examples/$PLATFORM/$EXAMPLE_NAME"
[[ -d "$EXAMPLE_DIR" ]] || die "example directory not found: examples/$PLATFORM/$EXAMPLE_NAME"

TARGET="$ROOT/examples/$EXAMPLE_ID"
if [[ -f "$TARGET" ]]; then
  ENTRY_ABS="$TARGET"
elif [[ -d "$TARGET" ]]; then
  if [[ -f "$TARGET/src/${ENTRY}.${EXT}" ]]; then
    ENTRY_ABS="$TARGET/src/${ENTRY}.${EXT}"
  elif [[ -f "$TARGET/${ENTRY}.${EXT}" ]]; then
    ENTRY_ABS="$TARGET/${ENTRY}.${EXT}"
  else
    die "entry file not found: examples/$EXAMPLE_ID/src/${ENTRY}.${EXT}"
  fi
else
  die "path not found: examples/$EXAMPLE_ID"
fi
ENTRY_FILE="${ENTRY_ABS#"$EXAMPLE_DIR"/}"

# --- Load root .env and inject everything verbatim (except FRISK_API_KEY) ---
[[ -f "$ENV_FILE" ]] || die "root .env not found at $ENV_FILE (copy .env.example to .env)"
set -a
# shellcheck source=/dev/null
source "$ENV_FILE"
set +a

# FRISK_API_KEY is never taken from .env directly; it is derived from the
# environment-specific key.
KEY_VAR="FRISK_API_KEY_$(printf '%s' "$FRISK_ENV" | tr '[:lower:]' '[:upper:]')"
FRISK_API_KEY="${!KEY_VAR:-}"
[[ -n "$FRISK_API_KEY" ]] || die "$KEY_VAR is not set in $ENV_FILE (required for --frisk-env $FRISK_ENV)"
export FRISK_API_KEY
unset FRISK_API_KEY_LOCAL FRISK_API_KEY_STAGING FRISK_API_KEY_PRODUCTION

# --- Non-local environments: frisk-envs.json wins over .env ---
if [[ "$FRISK_ENV" != "local" ]]; then
  [[ -f "$FRISK_ENVS_JSON" ]] || die "frisk-envs.json not found at $FRISK_ENVS_JSON"
  ENV_EXPORTS="$(python3 - "$FRISK_ENVS_JSON" "$FRISK_ENV" <<'PY'
import json, shlex, sys
with open(sys.argv[1]) as f:
    cfg = json.load(f)[sys.argv[2]]
for key, value in cfg.items():
    if "TODO" in str(value):
        sys.exit(f"Error: {key} for '{sys.argv[2]}' is still a TODO in frisk-envs.json")
    print(f"export {key}={shlex.quote(value)}")
PY
)" || die "failed to load '$FRISK_ENV' from frisk-envs.json"
  eval "$ENV_EXPORTS"
fi

echo "==> example:   $PLATFORM/$EXAMPLE_NAME ($ENTRY_FILE)" >&2
echo "==> frisk-env: $FRISK_ENV (FRISK_BASE_URL=${FRISK_BASE_URL:-<unset>})" >&2

cd "$EXAMPLE_DIR"
case "$PLATFORM" in
  python)     exec uv run python "$ENTRY_FILE" ${FORWARD[@]+"${FORWARD[@]}"} ;;
  typescript) exec bun run "$ENTRY_FILE" ${FORWARD[@]+"${FORWARD[@]}"} ;;
esac
