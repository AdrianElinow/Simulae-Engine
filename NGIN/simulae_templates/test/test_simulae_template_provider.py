import json
import tempfile
import unittest
from pathlib import Path

from NGIN.simulae_templates.lib.simulae_template_provider import (
    SimulaeTemplateProvider,
    SimulaeTemplateProviderError,
)


class TestSimulaeTemplateProvider(unittest.TestCase):
    def setUp(self):
        SimulaeTemplateProvider._default_providers.clear()
        self.tempdir = tempfile.TemporaryDirectory()
        self.template_root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()
        SimulaeTemplateProvider._default_providers.clear()

    def write_schema(self, relative_path, schema):
        path = self.template_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(schema), encoding="utf-8")
        return path.resolve()

    def write_text(self, relative_path, content):
        path = self.template_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path.resolve()

    def test_constructor_indexes_schema_ids_and_path_aliases(self):
        guid_path = self.write_schema(
            "simulae/datatypes/guid.json",
            {
                "$id": "@simulae/guid.json",
                "type": "string",
                "pattern": "^[a-f0-9]+$",
            },
        )
        human_path = self.write_schema(
            "POI/human.json",
            {
                "$id": "@simulae/human.json",
                "type": "object",
            },
        )

        provider = SimulaeTemplateProvider(self.template_root)

        self.assertEqual(provider.find_schema("@simulae/guid.json"), guid_path)
        self.assertEqual(provider.find_schema("@simulae/datatypes/guid.json"), guid_path)
        self.assertEqual(
            provider.find_schema("@simulae/simulae/datatypes/guid.json"),
            guid_path,
        )
        self.assertEqual(provider.find_schema("@simulae/human.json"), human_path)
        self.assertEqual(provider.find_schema("@simulae/POI/human.json"), human_path)

    def test_constructor_indexes_simulae_action_schema(self):
        action_path = self.write_schema(
            "simulae/simulae_action.json",
            {
                "$id": "@simulae/simulae_action.json",
                "title": "Simulae Action",
            },
        )

        provider = SimulaeTemplateProvider(self.template_root)

        self.assertEqual(provider.find_schema("@simulae/simulae_action.json"), action_path)

    def test_constructor_indexes_human_body_aliases(self):
        heart_path = self.write_schema(
            "OBJ/Human/heart.json",
            {
                "$id": "@simulae/OBJ/Human/heart.json",
                "title": "Human Heart",
            },
        )
        body_path = self.write_schema(
            "OBJ/human_body.json",
            {
                "$id": "@simulae/human_body.json",
                "title": "Human Body",
            },
        )

        provider = SimulaeTemplateProvider(self.template_root)

        self.assertEqual(provider.find_schema("@simulae/Human/heart.json"), heart_path)
        self.assertEqual(provider.find_schema("@simulae/OBJ/Human/heart.json"), heart_path)
        self.assertEqual(provider.find_schema("@simulae/human_body.json"), body_path)
        self.assertEqual(provider.find_schema("@simulae/Human/human_body.json"), body_path)
        self.assertEqual(
            provider.find_schema("@simulae/OBJ/Human/human_body.json"),
            body_path,
        )

    def test_load_schema_returns_deep_copy(self):
        self.write_schema(
            "simulae/datatypes/nodetype.json",
            {
                "$id": "@simulae/nodetype.json",
                "type": "string",
                "enum": ["Person", "Object"],
            },
        )
        provider = SimulaeTemplateProvider(self.template_root)

        loaded = provider.load_schema("@simulae/nodetype.json")
        loaded["enum"].append("Mutated")

        reloaded = provider.load_schema("@simulae/nodetype.json")
        self.assertEqual(reloaded["enum"], ["Person", "Object"])

    def test_static_find_and_load_use_cached_provider(self):
        schema_path = self.write_schema(
            "simulae/datatypes/color.json",
            {
                "$id": "@simulae/color.json",
                "type": "string",
            },
        )

        found_path = SimulaeTemplateProvider.find(
            "@simulae/color.json#/$defs/local",
            self.template_root,
        )
        loaded = SimulaeTemplateProvider.load("@simulae/color.json", self.template_root)

        self.assertEqual(found_path, schema_path)
        self.assertEqual(loaded["$id"], "@simulae/color.json")
        self.assertIn(
            self.template_root.resolve(),
            SimulaeTemplateProvider._default_providers,
        )

    def test_ignored_directories_are_not_indexed_or_parsed(self):
        self.write_schema(
            "OBJ/widget.json",
            {
                "$id": "@simulae/widget.json",
                "type": "object",
            },
        )
        self.write_text("resolved/invalid.json", "{")
        self.write_text("__pycache__/invalid.json", "{")

        provider = SimulaeTemplateProvider(self.template_root)

        self.assertEqual(
            provider.find_schema("@simulae/widget.json"),
            (self.template_root / "OBJ/widget.json").resolve(),
        )
        with self.assertRaises(SimulaeTemplateProviderError):
            provider.find_schema("@simulae/resolved/invalid.json")

    def test_find_schema_rejects_unknown_and_unsafe_schema_ids(self):
        provider = SimulaeTemplateProvider(self.template_root)

        for schema_id in (
            "@other/schema.json",
            "@simulae/",
            "@simulae/../outside.json",
            "@simulae/missing.json",
        ):
            with self.subTest(schema_id=schema_id):
                with self.assertRaises(SimulaeTemplateProviderError):
                    provider.find_schema(schema_id)

    def test_invalid_json_raises_provider_error_during_indexing(self):
        self.write_text("OBJ/broken.json", "{")

        with self.assertRaises(SimulaeTemplateProviderError):
            SimulaeTemplateProvider(self.template_root)

    def test_non_object_json_raises_provider_error_during_indexing(self):
        self.write_text("OBJ/not_object.json", "[]")

        with self.assertRaises(SimulaeTemplateProviderError):
            SimulaeTemplateProvider(self.template_root)


if __name__ == "__main__":
    unittest.main()
