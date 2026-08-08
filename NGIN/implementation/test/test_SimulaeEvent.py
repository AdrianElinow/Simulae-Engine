import unittest

from NGIN.implementation.lib.SimulaeEvent import SimulaeEvent
from NGIN.utilities.lib.SimulaeConstants import OBS, SRC, TGT


class TestSimulaeEvent(unittest.TestCase):
    def test_event_normalizes_and_tracks_participants(self):
        event = SimulaeEvent(
            "event-1", "social", "conversation", "gossip", None, None,
            [" actor-1 ", "actor-1"], ["target-1"], ["observer-1"], ["rumor"],
        )

        self.assertEqual(event.source_ids, ["actor-1"])
        self.assertEqual(event.Relations[SRC], {"actor-1": {}})
        self.assertEqual(event.Relations[TGT], {"target-1": {}})
        self.assertEqual(event.Relations[OBS], {"observer-1": {}})
        self.assertTrue(event.add_observer("observer-2"))
        self.assertTrue(event.was_observed_by("observer-2"))
        self.assertTrue(event.remove_observer("observer-2"))
        self.assertFalse(event.remove_observer("observer-2"))
