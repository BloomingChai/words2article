#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f .env ]]; then
  echo "Missing .env file. Create it from .env.example first." >&2
  exit 1
fi

set -a
source .env
set +a

python3 -m momo "$@"
