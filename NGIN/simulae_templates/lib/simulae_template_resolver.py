"""Resolve JSON Schema references inside the simulae template tree.

The resolver accepts an ``@simulae/...`` reference such as
``@simulae/human.json`` and emits a JSON document with local template
references expanded inline.

Recursive schemas cannot be fully inlined into finite JSON. When a cycle is
detected, the resolver preserves that ``$ref`` without adding extension
properties.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from .simulae_template_provider import (
        DEFAULT_TEMPLATE_ROOT,
        SIMULAE_PREFIX,
        SimulaeTemplateProvider,
        SimulaeTemplateProviderError,
    )
except ImportError:
    from simulae_template_provider import (
        DEFAULT_TEMPLATE_ROOT,
        SIMULAE_PREFIX,
        SimulaeTemplateProvider,
        SimulaeTemplateProviderError,
    )

EXTENSION_PREFIX = "x" + "-"


class TemplateResolverError(Exception):
    """Raised when a simulae template reference cannot be resolved."""


@dataclass(frozen=True)
class ResolvedTemplate:
    """A loaded template plus the file it came from."""

    ref: str
    path: Path
    schema: dict[str, Any]


class SimulaeTemplateResolver:
    """Resolve ``$ref`` values in JSON templates under ``simulae_templates``."""

    def __init__(
        self,
        template_root: str | Path | None = None,
        provider: SimulaeTemplateProvider | None = None,
    ):
        self.provider = provider or SimulaeTemplateProvider(template_root)
        self.template_root = self.provider.template_root

    def resolve(self, ref: str, *, preserve_cycles: bool = True) -> dict[str, Any]:
        """Return a JSON-serializable schema with references expanded inline."""

        template = self._load_ref(ref)
        return self._resolve_node(
            template.schema,
            current_file=template.path,
            ref_stack=(template.ref,),
            preserve_cycles=preserve_cycles,
        )

    def print_index(self) -> None:
        """Print known refs for debugging from the command line."""

        self.provider.print_index()

    def _load_ref(self, ref: str) -> ResolvedTemplate:
        normalized = self._normalize_ref(ref)

        try:
            path = self.provider.find_schema(normalized)
            schema = self.provider.load_schema(normalized)
        except SimulaeTemplateProviderError as exc:
            raise TemplateResolverError(f"Unknown template ref: {ref}")

        return ResolvedTemplate(ref=normalized, path=path, schema=schema)

    def _resolve_node(
        self,
        node: Any,
        *,
        current_file: Path,
        ref_stack: tuple[str, ...],
        preserve_cycles: bool,
    ) -> Any:
        if isinstance(node, list):
            return [
                self._resolve_node(
                    item,
                    current_file=current_file,
                    ref_stack=ref_stack,
                    preserve_cycles=preserve_cycles,
                )
                for item in node
            ]

        if not isinstance(node, dict):
            return node

        ref = node.get("$ref")
        if isinstance(ref, str):
            resolved_ref = self._resolve_ref_value(ref, current_file)

            if resolved_ref in ref_stack:
                if preserve_cycles:
                    return {"$ref": resolved_ref}
                raise TemplateResolverError(
                    "Cyclic template reference: " + " -> ".join((*ref_stack, resolved_ref))
                )

            template = self._load_ref(resolved_ref)
            resolved_schema = self._resolve_node(
                template.schema,
                current_file=template.path,
                ref_stack=(*ref_stack, resolved_ref),
                preserve_cycles=preserve_cycles,
            )

            sibling_keys = {k: v for k, v in node.items() if k != "$ref"}
            if sibling_keys:
                merged = copy.deepcopy(resolved_schema)
                merged.update(
                    self._resolve_node(
                        sibling_keys,
                        current_file=current_file,
                        ref_stack=ref_stack,
                        preserve_cycles=preserve_cycles,
                    )
                )
                return merged

            return resolved_schema

        return {
            key: self._resolve_node(
                value,
                current_file=current_file,
                ref_stack=ref_stack,
                preserve_cycles=preserve_cycles,
            )
            for key, value in node.items()
            if not key.startswith(EXTENSION_PREFIX)
        }

    def _resolve_ref_value(self, ref: str, current_file: Path) -> str:
        base_ref = ref.split("#", 1)[0]
        if base_ref.startswith(SIMULAE_PREFIX):
            return self._normalize_ref(base_ref)

        if not base_ref:
            return self._normalize_ref(str(current_file))

        relative_path = (current_file.parent / base_ref).resolve()
        for known_ref, known_path in self.provider.schema_id_to_filepath.items():
            if known_path == relative_path:
                return known_ref

        return self._normalize_ref(str(relative_path))

    def _normalize_ref(self, ref: str) -> str:
        return ref.split("#", 1)[0]


def resolve_template(ref: str, template_root: str | Path | None = None) -> dict[str, Any]:
    """Convenience function for callers that just need a resolved schema."""

    return SimulaeTemplateResolver(template_root).resolve(ref)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "ref",
        nargs="?",
        default="@simulae/human.json",
        help="Template ref to resolve, for example @simulae/human.json.",
    )
    parser.add_argument(
        "--template-root",
        default=str(DEFAULT_TEMPLATE_ROOT),
        help="Directory containing simulae template JSON files.",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Optional output file. Defaults to stdout.",
    )
    parser.add_argument(
        "--strict-cycles",
        action="store_true",
        help="Raise an error on cyclic refs instead of preserving the cycle ref.",
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="Print the discovered template ref index and exit.",
    )

    args = parser.parse_args(argv)
    resolver = SimulaeTemplateResolver(args.template_root)

    if args.index:
        resolver.print_index()
        return 0

    resolved = resolver.resolve(args.ref, preserve_cycles=not args.strict_cycles)
    rendered = json.dumps(resolved, indent=4, sort_keys=False)

    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except TemplateResolverError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
