from __future__ import annotations

from itertools import permutations
from pathlib import Path
import unittest

from NGIN.NGIN_Socialization import SOCIAL_INTERACTION_TYPES
from NGIN.SimulaeConstants import SOCIAL

from .._gamemode_test_utils import (
    HITMAN_WIKI_ROOT,
    expected_relation,
    lead_type_for,
    load_hitman_role_specs,
    make_actor_map,
    policy_diff_value,
    policy_disposition_label,
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
    "Agency": 0,
    "Security": 1,
    "Staff": 2,
    "Civilian": 3,
    "Target": 4,
}

GROUP_POLICY_EXPECTATIONS = {
    "Agency": {
        "Economy": (5, 2),
        "Diplomacy": (5, 2),
        "Government": (5, 2),
        "Justice": (5, 2),
        "Legality": (5, 2),
        "Technology": (5, 2),
    },
    "Security": {
        "Economy": (3, 3),
        "Diplomacy": (3, 3),
        "Government": (3, 3),
        "Justice": (3, 3),
        "Legality": (3, 3),
        "Militancy": (3, 3),
        "Technology": (3, 3),
    },
    "Staff": {
        "Economy": (4, 2),
        "Diplomacy": (4, 2),
        "Government": (4, 2),
        "Justice": (4, 2),
        "Legality": (4, 2),
        "Technology": (4, 2),
    },
    "Civilian": {
        "Economy": (4, 2),
        "Diplomacy": (4, 2),
        "Government": (4, 2),
        "Justice": (4, 2),
        "Legality": (4, 2),
        "Technology": (4, 2),
    },
    "Target": {
        "Economy": (3, 3),
        "Diplomacy": (3, 3),
        "Government": (3, 3),
        "Justice": (3, 3),
        "Legality": (3, 3),
        "Militancy": (3, 3),
        "Technology": (3, 3),
    },
}

ROLE_EXPECTATIONS = {
    "Agent 47": {
        "group": "Agency",
        "kind": "infiltrative",
        "plan": ("study the venue", "borrow a disguise", "eliminate the target"),
        "priorities": ("stay unseen", "keep escape options open", "leave no witnesses"),
        "alignment": "Agency",
        "faction": "ICA",
        "status": "Active",
    },
    "Diana Burnwood": {
        "group": "Agency",
        "kind": "handler",
        "plan": ("brief the contract", "monitor the mission", "arrange extraction"),
        "priorities": ("preserve deniability", "feed 47 the right intel", "keep the contract clean"),
        "alignment": "Agency",
        "faction": "ICA",
        "status": "Active",
    },
    "Guard": {
        "group": "Security",
        "kind": "security",
        "plan": ("patrol the venue", "question irregularities", "lock down exits"),
        "priorities": ("protect the target", "control access", "escalate suspicion fast"),
        "alignment": "Security",
        "faction": "Venue Security",
        "status": "Active",
    },
    "Head of Security": {
        "group": "Security",
        "kind": "security",
        "plan": ("coordinate patrols", "tighten lockdowns", "seal exits"),
        "priorities": ("control the response", "find the intruder", "avoid an embarrassing breach"),
        "alignment": "Security",
        "faction": "Venue Security",
        "status": "Elite",
    },
    "Staff Member": {
        "group": "Staff",
        "kind": "staff",
        "plan": ("serve the venue", "maintain routine", "spot anomalies"),
        "priorities": ("keep the place believable", "avoid panic", "stay helpful"),
        "alignment": "Staff",
        "faction": "Venue Staff",
        "status": "Active",
    },
    "Civilian": {
        "group": "Civilian",
        "kind": "civilian",
        "plan": ("move through the venue", "avoid danger", "flee if exposed"),
        "priorities": ("stay alive", "avoid direct involvement", "notice suspicious activity"),
        "alignment": "Civilian",
        "faction": "Public",
        "status": "Ambient",
    },
    "Mission Target": {
        "group": "Target",
        "kind": "target",
        "plan": ("keep to routine", "call for protection", "escape suspicion"),
        "priorities": ("survive the day", "spot intruders", "avoid exposure"),
        "alignment": "Target",
        "faction": "Contract Principal",
        "status": "Primary",
    },
}


def _discover_role_names(root: Path, required_markers: tuple[str, ...]) -> set[str]:
    names: set[str] = set()
    for path in root.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if all(marker in text for marker in required_markers):
            names.add(path.stem)
    return names


class TestHitmanWorldOfAssassination(unittest.TestCase):
    def setUp(self):
        self.specs = load_hitman_role_specs()
        self.actors = make_actor_map(self.specs)

    def _expected_domain(self, prompt_type: str) -> str:
        return PROMPT_DOMAIN_BY_TYPE[prompt_type]

    def _assert_common_prompt_record(
        self,
        record: dict[str, object] | None,
        *,
        prompt_type: str,
        relation: str,
        source_name: str,
        target_name: str,
    ) -> None:
        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record["prompt_event_type"], prompt_type)
        self.assertIn(record["response_type"], SOCIAL_INTERACTION_TYPES)

        prompt_event = record["prompt_event"]
        assert isinstance(prompt_event, dict)
        qualifiers = prompt_event["qualifiers"]
        assert isinstance(qualifiers, dict)

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

    def test_role_inventory_and_initial_priorities(self):
        expected_names = _discover_role_names(
            HITMAN_WIKI_ROOT,
            ("- Alignment:", "- Faction:", "- Roles:", "- Status:"),
        )
        actual_names = {spec.name for spec in self.specs}
        self.assertCountEqual(actual_names, expected_names)

        for spec in self.specs:
            with self.subTest(role=spec.name):
                expected = ROLE_EXPECTATIONS[spec.name]
                self.assertEqual(spec.mode, "hitman")
                self.assertEqual(spec.group, expected["group"])
                self.assertEqual(spec.kind, expected["kind"])
                self.assertEqual(spec.plan, expected["plan"])
                self.assertEqual(spec.priorities, expected["priorities"])
                self.assertTrue(spec.summary)
                self.assertTrue(spec.source_path.exists())
                self.assertEqual(spec.details["alignment"], expected["alignment"])
                self.assertEqual(spec.details["faction"], expected["faction"])
                self.assertEqual(spec.details["status"], expected["status"])
                self.assertTrue(spec.details["roles"])

                for key, value in GROUP_POLICY_EXPECTATIONS[spec.group].items():
                    self.assertEqual(spec.policy_profile[key], value)

    def test_pairwise_dispositions_and_social_openers(self):
        for source, target in permutations(self.specs, 2):
            with self.subTest(source=source.name, target=target.name):
                source_actor = self.actors[source.name]
                target_actor = self.actors[target.name]

                relation = expected_relation("hitman", source, target)
                diff = policy_diff_value(source_actor, target_actor)
                reverse_diff = policy_diff_value(target_actor, source_actor)
                label = policy_disposition_label(source_actor, target_actor)

                self.assertIsNotNone(diff)
                assert isinstance(diff, int)
                self.assertEqual(diff, reverse_diff)

                if relation == "Friendly":
                    self.assertLessEqual(diff, 10)
                    self.assertEqual(label, "Friendly")
                elif relation == "Hostile":
                    self.assertGreaterEqual(diff, 20)
                    self.assertEqual(label, "Hostile")
                else:
                    self.assertLess(diff, 20)
                    self.assertIn(label, {"Friendly", "Neutral"})

                before_memory = len(target_actor.Memory.get(SOCIAL, {}))
                history: list[dict[str, object]] = []
                relation_out, prompt_type, _, record = simulate_social_encounter(
                    "hitman",
                    source,
                    target,
                    source_actor,
                    target_actor,
                    history=history,
                )

                self.assertEqual(relation_out, relation)
                self.assertEqual(prompt_type, lead_type_for("hitman", source, target, relation))
                self.assertEqual(len(history), 1)
                self._assert_common_prompt_record(
                    record,
                    prompt_type=prompt_type,
                    relation=relation,
                    source_name=source.name,
                    target_name=target.name,
                )
                self.assertEqual(len(target_actor.Memory.get(SOCIAL, {})), before_memory + 1)

    def test_mission_table_round_all_roles_together(self):
        ordered_specs = sorted(self.specs, key=lambda spec: (GROUP_ORDER[spec.group], spec.kind, spec.name))
        history: list[dict[str, object]] = []
        seen_prompt_types: set[str] = set()
        seen_relations: set[str] = set()

        for index, source in enumerate(ordered_specs):
            target = ordered_specs[(index + 1) % len(ordered_specs)]
            with self.subTest(step=index, source=source.name, target=target.name):
                relation, prompt_type, _, record = simulate_social_encounter(
                    "hitman",
                    source,
                    target,
                    self.actors[source.name],
                    self.actors[target.name],
                    history=history,
                )

                seen_relations.add(relation)
                seen_prompt_types.add(prompt_type)
                self._assert_common_prompt_record(
                    record,
                    prompt_type=prompt_type,
                    relation=relation,
                    source_name=source.name,
                    target_name=target.name,
                )

        self.assertEqual(len(history), len(ordered_specs))
        self.assertEqual(seen_relations, {"Friendly", "Hostile", "Neutral"})
        self.assertGreaterEqual(len(seen_prompt_types), 4)

        for spec in ordered_specs:
            with self.subTest(memory_of=spec.name):
                self.assertGreaterEqual(len(self.actors[spec.name].Memory.get(SOCIAL, {})), 1)


if __name__ == "__main__":
    unittest.main()
