"""Provider for locating and loading simulae JSON template schemas."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


SIMULAE_PREFIX = "@simulae/"
DEFAULT_TEMPLATE_ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRECTORIES = {"__pycache__", "resolved"}


class SimulaeTemplateProviderError(Exception):
    """Raised when a simulae template schema cannot be found or loaded."""


class SimulaeTemplateProvider:
    """Find and load schemas from the simulae template tree.

    The constructor eagerly scans the template tree and creates a ref-to-path
    index for fast repeated lookups. Static ``find`` and ``load`` helpers are
    provided for one-off use.
    """

    _default_providers: dict[Path, "SimulaeTemplateProvider"] = {}

    def __init__(self, template_root: str | Path | None = None):
        self.template_root = Path(template_root or DEFAULT_TEMPLATE_ROOT).resolve()
        self.schema_id_to_filepath: dict[str, Path] = {}
        self.filepath_to_schema_id: dict[Path, str] = {}
        self._schema_cache: dict[Path, dict[str, Any]] = {}
        self._index_schemas()

    @staticmethod
    def find(schema_id: str, template_root: str | Path | None = None) -> Path:
        """Return the filepath for ``schema_id`` using a cached provider."""

        return SimulaeTemplateProvider._get_provider(template_root).find_schema(schema_id)

    @staticmethod
    def load(schema_id: str, template_root: str | Path | None = None) -> dict[str, Any]:
        """Load and return a copy of the JSON schema for ``schema_id``."""

        return SimulaeTemplateProvider._get_provider(template_root).load_schema(schema_id)

    @classmethod
    def _get_provider(cls, template_root: str | Path | None = None) -> "SimulaeTemplateProvider":
        root = Path(template_root or DEFAULT_TEMPLATE_ROOT).resolve()
        provider = cls._default_providers.get(root)
        if provider is None:
            provider = cls(root)
            cls._default_providers[root] = provider
        return provider

    def find_schema(self, schema_id: str) -> Path:
        """Return the filepath for ``schema_id`` using this provider's index."""

        normalized = self.normalize_schema_id(schema_id)
        path = self.schema_id_to_filepath.get(normalized)

        if path is None:
            candidate = self._path_from_schema_id(normalized)
            if candidate and candidate.exists() and self._is_template_path(candidate):
                path = candidate
                self._add_ref(normalized, path)

        if path is None:
            raise SimulaeTemplateProviderError(f"Unknown template schema id: {schema_id}")

        return path

    def load_schema(self, schema_id: str) -> dict[str, Any]:
        """Load and return a copy of a schema using this provider's index."""

        return copy.deepcopy(self._load_path(self.find_schema(schema_id)))

    def print_index(self) -> None:
        """Print known schema refs for debugging."""

        for schema_id in sorted(self.schema_id_to_filepath):
            print(f"{schema_id}\t{self.schema_id_to_filepath[schema_id]}")

    def _index_schemas(self) -> None:
        for path in sorted(self.template_root.rglob("*.json")):
            if not self._is_template_path(path):
                continue

            try:
                schema = self._load_path(path)
            except json.JSONDecodeError as exc:
                raise SimulaeTemplateProviderError(f"Invalid JSON in {path}: {exc}") from exc

            schema_id = schema.get("$id")
            if isinstance(schema_id, str):
                self._add_ref(schema_id, path)
                self.filepath_to_schema_id[path.resolve()] = self.normalize_schema_id(schema_id)

            for alias in self._path_aliases(path):
                self._add_ref(alias, path)

    def _is_template_path(self, path: Path) -> bool:
        try:
            relative = path.resolve().relative_to(self.template_root)
        except ValueError:
            return False

        return not any(part in IGNORED_DIRECTORIES for part in relative.parts)

    def _add_ref(self, schema_id: str, path: Path) -> None:
        normalized = self.normalize_schema_id(schema_id)
        resolved_path = path.resolve()

        existing_path = self.schema_id_to_filepath.get(normalized)
        if existing_path is not None and existing_path != resolved_path:
            return

        self.schema_id_to_filepath[normalized] = resolved_path

    def _load_path(self, path: Path) -> dict[str, Any]:
        resolved_path = path.resolve()
        schema = self._schema_cache.get(resolved_path)
        if schema is None:
            with resolved_path.open("r", encoding="utf-8") as schema_file:
                loaded = json.load(schema_file)
            if not isinstance(loaded, dict):
                raise SimulaeTemplateProviderError(f"Template is not a JSON object: {path}")
            schema = loaded
            self._schema_cache[resolved_path] = schema
        return schema

    def _path_aliases(self, path: Path) -> list[str]:
        relative = path.resolve().relative_to(self.template_root)
        aliases = [f"{SIMULAE_PREFIX}{relative.as_posix()}"]

        parts = relative.parts
        if parts and parts[0] in {"simulae", "POI", "PTY", "LOC", "OBJ", "FAC", "EVT"}:
            aliases.append(f"{SIMULAE_PREFIX}{Path(*parts[1:]).as_posix()}")

        if len(parts) >= 3 and parts[0] == "OBJ" and parts[1] == "Human":
            aliases.append(f"{SIMULAE_PREFIX}Human/{Path(*parts[2:]).as_posix()}")

        if parts[-1] == "human_body.json":
            aliases.append(f"{SIMULAE_PREFIX}Human/human_body.json")
            aliases.append(f"{SIMULAE_PREFIX}OBJ/Human/human_body.json")

        return aliases

    def _path_from_schema_id(self, schema_id: str) -> Path | None:
        if not schema_id.startswith(SIMULAE_PREFIX):
            return None

        relative_id = schema_id[len(SIMULAE_PREFIX) :]
        if not relative_id or relative_id.startswith(("/", "..")):
            return None

        return (self.template_root / relative_id).resolve()

    @staticmethod
    def normalize_schema_id(schema_id: str) -> str:
        """Drop any JSON pointer fragment from a schema id/ref."""

        return schema_id.split("#", 1)[0]
