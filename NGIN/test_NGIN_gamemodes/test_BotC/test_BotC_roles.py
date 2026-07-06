from __future__ import annotations

from itertools import permutations
from pathlib import Path
import unittest

from NGIN.NGIN_Socialization import SOCIAL_INTERACTION_TYPES
from NGIN.SimulaeConstants import SOCIAL

from .._gamemode_test_utils import (
    BOTC_WIKI_ROOT,
    expected_relation,
    lead_type_for,
    load_botc_role_specs,
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

PLAN_BY_KIND = {
    "investigative": ("gather verified information", "cross-check claims"),
    "support": ("support trusted allies", "share safe information"),
    "deceptive": ("blend in", "misdirect suspicion"),
    "aggressive": ("apply pressure", "remove obstacles"),
}

ALLOWED_KINDS_BY_ROLE_TYPE = {
    "Townsfolk": {"investigative", "support"},
    "Outsider": {"support"},
    "Minion": {"deceptive"},
    "Demon": {"aggressive"},
}


def _discover_role_names(root: Path, required_markers: tuple[str, ...]) -> set[str]:
    names: set[str] = set()
    for path in root.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if all(marker in text for marker in required_markers):
            names.add(path.stem)
    return names


class TestBloodOnTheClocktowerRoles(unittest.TestCase):
    def setUp(self):
        self.specs = load_botc_role_specs()
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
        self.assertEqual(prompt_event["source"], source_name)
        self.assertEqual(prompt_event["target"], target_name)
        self.assertEqual(prompt_event["domain"], self._expected_domain(prompt_type))
        self.assertEqual(prompt_event["polarity"], "Positive" if relation == "Friendly" else "Negative")
        self.assertEqual(prompt_event["visibility"], "Dyadic")
        self.assertEqual(prompt_event["authority"], "Peer")

        appraisal = record["appraisal"]
        assert isinstance(appraisal, dict)
        self.assertEqual(appraisal["domain"], self._expected_domain(prompt_type))
        self.assertEqual(appraisal["polarity"], "Positive" if relation == "Friendly" else "Negative")
        self.assertEqual(appraisal["visibility"], "Dyadic")
        self.assertEqual(appraisal["authority"], "Peer")
        self.assertGreater(appraisal["salience"], 0)

    def test_role_inventory_and_initial_priorities(self):
        expected_names = _discover_role_names(BOTC_WIKI_ROOT, ("- Team:", "- Role Type:"))
        actual_names = {spec.name for spec in self.specs}
        self.assertCountEqual(actual_names, expected_names)

        for spec in self.specs:
            with self.subTest(role=spec.name):
                role_type = spec.details["role_type"]
                self.assertEqual(spec.mode, "botc")
                self.assertTrue(spec.summary)
                self.assertTrue(spec.source_path.exists())
                self.assertEqual(spec.priorities[0], spec.summary)
                self.assertEqual(spec.priorities[1], f"focus: {role_type}")
                self.assertEqual(spec.plan, PLAN_BY_KIND[spec.kind])
                self.assertIn(role_type, ALLOWED_KINDS_BY_ROLE_TYPE)
                self.assertIn(spec.kind, ALLOWED_KINDS_BY_ROLE_TYPE[role_type])

                if role_type in {"Townsfolk", "Outsider"}:
                    self.assertEqual(spec.group, "Good")
                    self.assertGreaterEqual(spec.policy_profile["Diplomacy"][0], 4)
                    self.assertGreaterEqual(spec.policy_profile["Justice"][0], 4)
                    self.assertLessEqual(spec.policy_profile["Militancy"][0], 4)
                else:
                    self.assertEqual(spec.group, "Evil")
                    self.assertLessEqual(spec.policy_profile["Diplomacy"][0], 2)
                    self.assertLessEqual(spec.policy_profile["Justice"][0], 2)
                    self.assertGreaterEqual(spec.policy_profile["Militancy"][0], 4)

                if spec.kind == "investigative":
                    self.assertGreaterEqual(spec.personality_profile["Curiosity"][0], 6)
                elif spec.kind == "support":
                    self.assertGreaterEqual(spec.personality_profile["Empathy"][0], 5)
                elif spec.kind == "deceptive":
                    self.assertLessEqual(spec.personality_profile["Trust"][0], 1)
                elif spec.kind == "aggressive":
                    self.assertGreaterEqual(spec.personality_profile["Conflict-Style"][0], 6)

    def test_pairwise_dispositions_and_social_openers(self):
        for source, target in permutations(self.specs, 2):
            with self.subTest(source=source.name, target=target.name):
                source_actor = self.actors[source.name]
                target_actor = self.actors[target.name]

                relation = expected_relation("botc", source, target)
                diff = policy_diff_value(source_actor, target_actor)
                reverse_diff = policy_diff_value(target_actor, source_actor)
                label = policy_disposition_label(source_actor, target_actor)

                self.assertIsNotNone(diff)
                assert isinstance(diff, int)
                self.assertEqual(diff, reverse_diff)
                self.assertEqual(relation, "Friendly" if source.group == target.group else "Hostile")

                if relation == "Friendly":
                    self.assertLessEqual(diff, 10)
                    self.assertEqual(label, "Friendly")
                else:
                    self.assertGreaterEqual(diff, 20)
                    self.assertEqual(label, "Hostile")

                before_memory = len(target_actor.Memory.get(SOCIAL, {}))
                history: list[dict[str, object]] = []
                relation_out, prompt_type, _, record = simulate_social_encounter(
                    "botc",
                    source,
                    target,
                    source_actor,
                    target_actor,
                    history=history,
                )

                self.assertEqual(relation_out, relation)
                self.assertEqual(prompt_type, lead_type_for("botc", source, target, relation))
                self.assertEqual(len(history), 1)
                self._assert_common_prompt_record(
                    record,
                    prompt_type=prompt_type,
                    relation=relation,
                    source_name=source.name,
                    target_name=target.name,
                )
                self.assertEqual(len(target_actor.Memory.get(SOCIAL, {})), before_memory + 1)

    def test_round_table_all_roles_together(self):
        ordered_specs = sorted(self.specs, key=lambda spec: (spec.group, spec.details["role_type"], spec.name))
        history: list[dict[str, object]] = []
        seen_prompt_types: set[str] = set()
        seen_relations: set[str] = set()

        for index, source in enumerate(ordered_specs):
            target = ordered_specs[(index + 1) % len(ordered_specs)]
            with self.subTest(step=index, source=source.name, target=target.name):
                relation, prompt_type, _, record = simulate_social_encounter(
                    "botc",
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
        self.assertEqual(seen_relations, {"Friendly", "Hostile"})
        self.assertGreaterEqual(len(seen_prompt_types), 3)

        for spec in ordered_specs:
            with self.subTest(memory_of=spec.name):
                self.assertGreaterEqual(len(self.actors[spec.name].Memory.get(SOCIAL, {})), 1)


if __name__ == "__main__":
    unittest.main()
