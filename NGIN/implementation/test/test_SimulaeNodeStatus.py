import unittest

from NGIN.implementation.lib.SimulaeNodeStatus import SimulaeNodeStatus


class TestSimulaeNodeStatus(unittest.TestCase):
    def test_status_serializes_to_its_name(self):
        self.assertEqual(SimulaeNodeStatus.ALIVE.toJSON(), "ALIVE")
        self.assertEqual(SimulaeNodeStatus.DEAD.toJSON(), "DEAD")
