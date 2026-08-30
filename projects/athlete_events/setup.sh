#!/usr/bin/env bash
set -euo pipefail

RECREATE_VENV="false"
for arg in "$@"; do
  case "$arg" in
    --recreate)
      RECREATE_VENV="true"
      ;;
    *)
      echo "Unknown option: $arg"
      echo "Usage: ./setup.sh [--recreate]"
      exit 1
      ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found in PATH."
  exit 1
fi

if [[ "$RECREATE_VENV" == "true" && -d ".venv" ]]; then
  echo "Removing existing .venv ..."
  rm -rf .venv
fi

if [[ ! -d ".venv" ]]; then
  echo "Creating virtual environment (.venv) ..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing pinned dependencies ..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo
echo "Setup complete."
echo "Run the app with:"
echo "  source .venv/bin/activate"
echo "  python athlete_events.py"
