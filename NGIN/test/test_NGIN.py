import unittest
from unittest.mock import patch

from NGIN.NGIN import NGIN


class TestNGIN(unittest.TestCase):
    def setUp(self):
        self.mission_struct = {"missions": []}
        self.settings = {"world_size": "small", "world_sizes": {"small": [1, 2]}}

    def test_requires_mission_structure_and_settings(self):
        with self.assertRaises(ValueError):
            NGIN(None, self.settings, generate=False)

        with self.assertRaises(ValueError):
            NGIN(self.mission_struct, None, generate=False)

    @patch.object(NGIN, "print_location_map")
    def test_initializes_empty_state_when_generation_is_disabled(self, print_location_map):
        engine = NGIN(self.mission_struct, self.settings, is_console=False, generate=False)

        self.assertEqual(engine.state.ID, "state")
        self.assertFalse(engine.is_console)
        self.assertIsNone(engine.world_root)
        print_location_map.assert_called_once()

    @patch("NGIN.NGIN.save_json_to_file")
    @patch.object(NGIN, "print_location_map")
    def test_save_serializes_the_current_state(self, print_location_map, save_json_to_file):
        engine = NGIN(self.mission_struct, self.settings, generate=False)

        engine.save_to_file("campaign.json")

        save_json_to_file.assert_called_once_with(
            "campaign.json", engine.state.toJSON(), pretty=True
        )
