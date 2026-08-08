#!/usr/bin/env sh

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_root=$(CDPATH= cd -- "$script_dir/.." && pwd)

python_path="$repository_root"
if [ -n "${PYTHONPATH:-}" ]; then
    python_path="$python_path:$PYTHONPATH"
fi
export PYTHONPATH="$python_path"

if command -v python3 >/dev/null 2>&1; then
    python_command=python3
elif command -v python >/dev/null 2>&1; then
    python_command=python
else
    echo "Python 3 was not found. Install Python or add it to PATH." >&2
    exit 127
fi

template_root="$repository_root/NGIN/simulae_templates"
resolver="$template_root/lib/simulae_template_resolver.py"
ref="${1:-@simulae/human.json}"
resolved_template_dir="$template_root/resolved"
default_output_name=$(printf '%s\n' "$ref" | sed 's#^@simulae/##; s#[^A-Za-z0-9._-]#_#g')
output="${2:-$resolved_template_dir/$default_output_name}"
mkdir -p "$(dirname -- "$output")"

relative_to_repo() {
    case "$1" in
        "$repository_root")
            printf '.\n'
            ;;
        "$repository_root"/*)
            printf '%s\n' "${1#"$repository_root"/}"
            ;;
        *)
            printf '%s\n' "$1"
            ;;
    esac
}

echo "Testing simulae template resolver"
echo "  resolver: $(relative_to_repo "$resolver")"
echo "  ref:      $ref"
echo "  output:   $(relative_to_repo "$output")"

"$python_command" -c '
import py_compile
import sys
import tempfile

with tempfile.NamedTemporaryFile(suffix=".pyc") as compiled:
    py_compile.compile(sys.argv[1], cfile=compiled.name, doraise=True)
' "$resolver"

"$python_command" -c '
import json
import pathlib
import sys

template_root = pathlib.Path(sys.argv[1])
files = sorted(template_root.rglob("*.json"))
for path in files:
    with path.open("r", encoding="utf-8") as template_file:
        json.load(template_file)

print(f"validated {len(files)} template JSON files")
' "$template_root"

"$python_command" "$resolver" "$ref" --template-root "$template_root" --index >/dev/null
"$python_command" "$resolver" "$ref" --template-root "$template_root" -o "$output"
"$python_command" -m json.tool "$output" >/dev/null

"$python_command" -c '
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as resolved_file:
    resolved = json.load(resolved_file)

errors = []
schema_map_keys = (
    "$defs",
    "definitions",
    "properties",
    "patternProperties",
    "dependentSchemas",
)
schema_value_keys = (
    "additionalProperties",
    "contains",
    "else",
    "if",
    "items",
    "not",
    "propertyNames",
    "then",
    "unevaluatedItems",
    "unevaluatedProperties",
)
schema_array_keys = (
    "allOf",
    "anyOf",
    "oneOf",
    "prefixItems",
)

def is_schema(value):
    return isinstance(value, (dict, bool))

def check_schema(value, path="$"):
    if isinstance(value, bool):
        return

    if not isinstance(value, dict):
        errors.append(f"{path}: schema must be an object or boolean")
        return

    schema_type = value.get("type")
    if schema_type is not None:
        valid_type = isinstance(schema_type, str) or (
            isinstance(schema_type, list)
            and all(isinstance(item, str) for item in schema_type)
        )
        if not valid_type:
            errors.append(f"{path}.type: must be a string or list of strings")

    required = value.get("required")
    if required is not None and not (
        isinstance(required, list) and all(isinstance(item, str) for item in required)
    ):
        errors.append(f"{path}.required: must be a list of strings")

    for key in schema_map_keys:
        child_map = value.get(key)
        if child_map is None:
            continue
        if not isinstance(child_map, dict):
            errors.append(f"{path}.{key}: must be an object")
            continue
        for child_key, child_schema in child_map.items():
            if not is_schema(child_schema):
                errors.append(f"{path}.{key}.{child_key}: must be a schema")
                continue
            check_schema(child_schema, f"{path}.{key}.{child_key}")

    for key in schema_value_keys:
        child_schema = value.get(key)
        if child_schema is None:
            continue
        if not is_schema(child_schema):
            errors.append(f"{path}.{key}: must be a schema")
            continue
        check_schema(child_schema, f"{path}.{key}")

    for key in schema_array_keys:
        child_schemas = value.get(key)
        if child_schemas is None:
            continue
        if not isinstance(child_schemas, list):
            errors.append(f"{path}.{key}: must be a list")
            continue
        for index, child_schema in enumerate(child_schemas):
            if not is_schema(child_schema):
                errors.append(f"{path}.{key}[{index}]: must be a schema")
                continue
            check_schema(child_schema, f"{path}.{key}[{index}]")

check_schema(resolved)

if errors:
    print("resolved output is not schema-shaped:", file=sys.stderr)
    for error in errors[:40]:
        print(f"  {error}", file=sys.stderr)
    raise SystemExit(1)
' "$output"

"$python_command" -c '
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as resolved_file:
    resolved = json.load(resolved_file)

refs = 0
extension_prefix = "x" + "-"
extension_properties = []

def walk(value, path="$"):
    global refs
    if isinstance(value, dict):
        if "$ref" in value:
            refs += 1
        for key, child in value.items():
            if key.startswith(extension_prefix):
                extension_properties.append((path, key))
            walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk(child, f"{path}[{index}]")

walk(resolved)

if extension_properties:
    print("extension properties remain in resolved output:", file=sys.stderr)
    for path, key in extension_properties[:20]:
        print(f"  {path}: {key}", file=sys.stderr)
    raise SystemExit(1)

schema_id_key = "$id"
missing_schema_id = "<missing>"
print(f"resolved schema id: {resolved.get(schema_id_key, missing_schema_id)}")
print(f"remaining refs: {refs}")
' "$output"

echo "template resolver test passed"
