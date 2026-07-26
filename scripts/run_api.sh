#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
echo "Starting NGIN API from $(pwd)"

# Try module run first
if python3 -m NGIN.api; then
  exit 0
else
  echo "Module run failed, trying direct script..."
  python3 NGIN/api.py
fi
