from __future__ import annotations

import unittest

from NGIN.NGIN_Socialization import SOCIAL_INTERACTION_TYPES
from NGIN.SimulaeConstants import SOCIAL

from .._gamemode_test_utils import (
    expected_relation,
    lead_type_for,
    load_botc_role_specs,
    make_actor_map,
    simulate_social_encounter,
)


PROMPT_DOMAIN_BY_TYPE = {
    "Open": "Identity",
    "Close": "Relationship",
    "Inform": "Policy",
    "Inquire": "Fact",
    "Stance": "Policy",
    "Coordinate": "Task",
    "Direct": "Task",
    "Negotiate": "Resource",
    "Boundary": "Policy",
    "Affect": "Relationship",
    "Deceive": "Intent",
    "Topic": "Fact",
}

GROUP_ORDER = {
    "Good": 0,
    "Evil": 1,
}


class TestBloodOnTheClocktowerGameFlow(unittest.TestCase):
    def setUp(self):
        self.specs = load_botc_role_specs()
        self.actors = make_actor_map(self.specs)

    def _expected_domain(self, prompt_type: str) -> str:
        return PROMPT_DOMAIN_BY_TYPE[prompt_type]

    def _assert_common_prompt_record(
        self,
        record: dict[str, object],
        *,
        prompt_type: str,
        relation: str,
        source_name: str,
        target_name: str,
    ) -> None:
        self.assertIsNotNone(record)
        self.assertEqual(record["prompt_event_type"], prompt_type)
        self.assertIn(record["response_type"], SOCIAL_INTERACTION_TYPES)

        prompt_event = record["prompt_event"]
        assert isinstance(prompt_event, dict)
        self.assertEqual(prompt_event["source"], source_name)
        self.assertEqual(prompt_event["target"], target_name)
        self.assertEqual(prompt_event["domain"], self._expected_domain(prompt_type))
        self.assertEqual(
            prompt_event["polarity"],
            "Positive" if relation == "Friendly" else "Negative" if relation == "Hostile" else "Neutral",
        )
        self.assertEqual(prompt_event["visibility"], "Dyadic")
        self.assertEqual(prompt_event["authority"], "Peer")

        appraisal = record["appraisal"]
        assert isinstance(appraisal, dict)
        self.assertEqual(appraisal["domain"], self._expected_domain(prompt_type))
        self.assertEqual(
            appraisal["polarity"],
            "Positive" if relation == "Friendly" else "Negative" if relation == "Hostile" else "Neutral",
        )
        self.assertEqual(appraisal["visibility"], "Dyadic")
        self.assertEqual(appraisal["authority"], "Peer")
        self.assertGreater(appraisal["salience"], 0)

    def test_full_table_round_all_roles_together(self):
        ordered_specs = sorted(self.specs, key=lambda spec: (GROUP_ORDER[spec.group], spec.details["role_type"], spec.name))
        history: list[dict[str, object]] = []
        seen_prompt_types: set[str] = set()
        seen_relations: set[str] = set()

        for index, source in enumerate(ordered_specs):
            target = ordered_specs[(index + 1) % len(ordered_specs)]
            with self.subTest(step=index, source=source.name, target=target.name):
                relation = expected_relation("botc", source, target)
                prompt_type = lead_type_for("botc", source, target, relation)
                before_memory = len(self.actors[target.name].Memory.get(SOCIAL, {}))

                relation_out, prompt_type_out, _, record = simulate_social_encounter(
                    "botc",
                    source,
                    target,
                    self.actors[source.name],
                    self.actors[target.name],
                    history=history,
                )

                self.assertEqual(relation_out, relation)
                self.assertEqual(prompt_type_out, prompt_type)
                self._assert_common_prompt_record(
                    record,
                    prompt_type=prompt_type,
                    relation=relation,
                    source_name=source.name,
                    target_name=target.name,
                )

                seen_relations.add(relation)
                seen_prompt_types.add(prompt_type)
                self.assertEqual(len(self.actors[target.name].Memory.get(SOCIAL, {})), before_memory + 1)

        self.assertEqual(len(history), len(ordered_specs))
        self.assertEqual(seen_relations, {"Friendly", "Hostile"})
        self.assertGreaterEqual(len(seen_prompt_types), 3)

        for spec in ordered_specs:
            with self.subTest(memory_of=spec.name):
                self.assertGreaterEqual(len(self.actors[spec.name].Memory.get(SOCIAL, {})), 1)


if __name__ == "__main__":
    unittest.main()
