import json
import tempfile
import unittest
from pathlib import Path

from NGIN.simulae_templates.lib.simulae_template_resolver import (
    SimulaeTemplateResolver,
    TemplateResolverError,
    main,
    resolve_template,
)


class TestSimulaeTemplateResolver(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.template_root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def write_schema(self, relative_path, schema):
        path = self.template_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(schema), encoding="utf-8")
        return path.resolve()

    def make_resolver(self):
        return SimulaeTemplateResolver(self.template_root)

    def test_resolve_expands_simulae_refs_and_strips_extension_properties(self):
        self.write_schema(
            "simulae/base.json",
            {
                "$id": "@simulae/base.json",
                "type": "object",
                "x-note": "debug only",
                "properties": {
                    "name": {
                        "type": "string",
                        "x-source": "fixture",
                    }
                },
            },
        )
        self.write_schema(
            "POI/person.json",
            {
                "$id": "@simulae/person.json",
                "$ref": "@simulae/base.json",
                "description": "Resolved person schema",
                "properties": {
                    "age": {"type": "integer"},
                },
                "x-template": "local only",
            },
        )

        resolved = self.make_resolver().resolve("@simulae/person.json")

        self.assertEqual(resolved["$id"], "@simulae/person.json")
        self.assertEqual(resolved["type"], "object")
        self.assertEqual(resolved["description"], "Resolved person schema")
        self.assertEqual(resolved["properties"]["name"], {"type": "string"})
        self.assertEqual(resolved["properties"]["age"], {"type": "integer"})
        self.assertNotIn("x-note", resolved)
        self.assertNotIn("x-template", resolved)

    def test_relative_refs_resolve_against_current_file(self):
        self.write_schema(
            "OBJ/shared/leaf.json",
            {
                "$id": "@simulae/leaf.json",
                "type": "string",
            },
        )
        self.write_schema(
            "OBJ/shared/container.json",
            {
                "$id": "@simulae/container.json",
                "type": "object",
                "properties": {
                    "leaf": {
                        "$ref": "leaf.json",
                    }
                },
            },
        )

        resolved = self.make_resolver().resolve("@simulae/container.json")

        self.assertEqual(resolved["properties"]["leaf"]["$id"], "@simulae/leaf.json")
        self.assertEqual(resolved["properties"]["leaf"]["type"], "string")

    def test_local_fragment_refs_are_preserved(self):
        self.write_schema(
            "simulae/action.json",
            {
                "$id": "@simulae/action.json",
                "type": "object",
                "properties": {
                    "references": {
                        "$ref": "#/$defs/actionReferences",
                    }
                },
                "$defs": {
                    "actionReferences": {
                        "type": "object",
                    }
                },
            },
        )

        resolved = self.make_resolver().resolve("@simulae/action.json")

        self.assertEqual(
            resolved["properties"]["references"],
            {"$ref": "#/$defs/actionReferences"},
        )
        self.assertEqual(resolved["$defs"]["actionReferences"], {"type": "object"})

    def test_flatten_compositions_is_on_by_default_and_local_properties_win(self):
        self.write_schema(
            "simulae/base.json",
            {
                "$id": "@simulae/base.json",
                "type": "object",
                "properties": {
                    "shared": {
                        "type": "string",
                        "description": "from base",
                    },
                    "base_only": {"type": "boolean"},
                },
                "required": ["shared"],
            },
        )
        self.write_schema(
            "POI/person.json",
            {
                "$id": "@simulae/person.json",
                "title": "Person",
                "allOf": [
                    {
                        "$ref": "@simulae/base.json",
                    }
                ],
                "properties": {
                    "shared": {
                        "type": "integer",
                    },
                    "local_only": {"type": "number"},
                },
            },
        )

        resolved = self.make_resolver().resolve("@simulae/person.json")

        self.assertNotIn("allOf", resolved)
        self.assertEqual(resolved["$id"], "@simulae/person.json")
        self.assertEqual(resolved["title"], "Person")
        self.assertEqual(resolved["type"], "object")
        self.assertEqual(resolved["required"], ["shared"])
        self.assertEqual(resolved["properties"]["shared"], {"type": "integer"})
        self.assertEqual(resolved["properties"]["base_only"], {"type": "boolean"})
        self.assertEqual(resolved["properties"]["local_only"], {"type": "number"})

    def test_flatten_compositions_can_be_disabled(self):
        self.write_schema(
            "simulae/base.json",
            {
                "$id": "@simulae/base.json",
                "type": "object",
            },
        )
        self.write_schema(
            "POI/person.json",
            {
                "$id": "@simulae/person.json",
                "allOf": [
                    {
                        "$ref": "@simulae/base.json",
                    }
                ],
            },
        )

        resolved = self.make_resolver().resolve(
            "@simulae/person.json",
            flatten_compositions=False,
        )

        self.assertEqual(resolved["$id"], "@simulae/person.json")
        self.assertIn("allOf", resolved)
        self.assertEqual(resolved["allOf"][0]["$id"], "@simulae/base.json")

    def test_single_item_anyof_and_oneof_are_flattened(self):
        self.write_schema(
            "simulae/base.json",
            {
                "$id": "@simulae/base.json",
                "anyOf": [
                    {
                        "type": "object",
                        "properties": {
                            "from_anyof": {"const": True},
                        },
                    }
                ],
                "oneOf": [
                    {
                        "properties": {
                            "from_oneof": {"type": "string"},
                        },
                    }
                ],
            },
        )

        resolved = self.make_resolver().resolve("@simulae/base.json")

        self.assertNotIn("anyOf", resolved)
        self.assertNotIn("oneOf", resolved)
        self.assertEqual(resolved["type"], "object")
        self.assertEqual(resolved["properties"]["from_anyof"], {"const": True})
        self.assertEqual(resolved["properties"]["from_oneof"], {"type": "string"})

    def test_multi_item_anyof_and_oneof_are_preserved(self):
        self.write_schema(
            "simulae/choice.json",
            {
                "$id": "@simulae/choice.json",
                "anyOf": [
                    {"type": "string"},
                    {"type": "integer"},
                ],
                "oneOf": [
                    {"const": "a"},
                    {"const": "b"},
                ],
            },
        )

        resolved = self.make_resolver().resolve("@simulae/choice.json")

        self.assertEqual(resolved["anyOf"], [{"type": "string"}, {"type": "integer"}])
        self.assertEqual(resolved["oneOf"], [{"const": "a"}, {"const": "b"}])

    def test_cycles_are_preserved_by_default_and_can_be_strict(self):
        self.write_schema(
            "simulae/node.json",
            {
                "$id": "@simulae/node.json",
                "type": "object",
                "properties": {
                    "child": {
                        "$ref": "@simulae/node.json",
                    }
                },
            },
        )
        resolver = self.make_resolver()

        resolved = resolver.resolve("@simulae/node.json")
        self.assertEqual(resolved["properties"]["child"], {"$ref": "@simulae/node.json"})

        with self.assertRaises(TemplateResolverError):
            resolver.resolve("@simulae/node.json", preserve_cycles=False)

    def test_unknown_refs_raise_template_resolver_error(self):
        self.write_schema(
            "simulae/root.json",
            {
                "$id": "@simulae/root.json",
                "$ref": "@simulae/missing.json",
            },
        )

        with self.assertRaises(TemplateResolverError):
            self.make_resolver().resolve("@simulae/root.json")

    def test_resolve_template_convenience_function(self):
        self.write_schema(
            "simulae/value.json",
            {
                "$id": "@simulae/value.json",
                "type": "number",
            },
        )

        resolved = resolve_template("@simulae/value.json", self.template_root)

        self.assertEqual(resolved["$id"], "@simulae/value.json")
        self.assertEqual(resolved["type"], "number")

    def test_main_writes_resolved_output_file(self):
        self.write_schema(
            "simulae/value.json",
            {
                "$id": "@simulae/value.json",
                "type": "number",
            },
        )
        output_path = self.template_root / "resolved.json"

        exit_code = main(
            [
                "@simulae/value.json",
                "--template-root",
                str(self.template_root),
                "--output",
                str(output_path),
            ]
        )

        self.assertEqual(exit_code, 0)
        resolved = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(resolved["$id"], "@simulae/value.json")
        self.assertEqual(resolved["type"], "number")


if __name__ == "__main__":
    unittest.main()
