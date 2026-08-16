#!/usr/bin/env bash

set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repository_root="$(CDPATH= cd -- "$script_dir/../.." && pwd)"

python_path="$repository_root"
if [[ -n "${PYTHONPATH:-}" ]]; then
    python_path="$python_path:$PYTHONPATH"
fi
export PYTHONPATH="$python_path"

if command -v python3 >/dev/null 2>&1; then
    python_command=python3
elif command -v python >/dev/null 2>&1; then
    python_command=python
else
    echo 'Python 3 was not found. Install Python or add it to PATH.' >&2
    exit 127
fi

exec "$python_command" -m unittest discover \
    -s "$script_dir/test" \
    -p 'test*.py' \
    -t "$repository_root" \
    -v
