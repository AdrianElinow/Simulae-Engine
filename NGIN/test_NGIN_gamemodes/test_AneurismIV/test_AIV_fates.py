from __future__ import annotations

from itertools import permutations
from pathlib import Path
import unittest

from NGIN.NGIN_Socialization import SOCIAL_INTERACTION_TYPES
from NGIN.SimulaeConstants import SOCIAL

from .._gamemode_test_utils import (
    AIV_WIKI_ROOT,
    expected_relation,
    lead_type_for,
    load_aiv_role_specs,
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

GROUP_POLICY_EXPECTATIONS = {
    "Neutral": {
        "Economy": (3, 3),
        "Government": (3, 3),
        "Legality": (3, 3),
        "Militancy": (3, 3),
        "Justice": (3, 3),
        "Diplomacy": (3, 3),
    },
    "P.L.F.": {
        "Economy": (4, 4),
        "Diplomacy": (5, 4),
        "Justice": (5, 4),
        "Legality": (5, 4),
        "Militancy": (2, 4),
    },
    "M.B.": {
        "Economy": (5, 4),
        "Diplomacy": (5, 4),
        "Justice": (4, 4),
        "Legality": (5, 4),
        "Militancy": (2, 4),
    },
    "Cortex": {
        "Government": (6, 5),
        "Legality": (6, 5),
        "Militancy": (6, 5),
        "Justice": (5, 4),
        "Diplomacy": (1, 4),
    },
    "Scum": {
        "Government": (0, 5),
        "Legality": (0, 5),
        "Militancy": (5, 5),
        "Justice": (0, 5),
        "Diplomacy": (0, 4),
    },
    "Spoiler": {
        "Economy": (3, 3),
        "Government": (3, 3),
        "Legality": (3, 3),
        "Militancy": (3, 3),
        "Justice": (3, 3),
        "Diplomacy": (3, 3),
    },
}

ROLE_EXPECTATIONS = {
    "Spirit": {
        "group": "Neutral",
        "kind": "observer",
        "plan": ("find a living fate", "choose a body to possess", "enter active play"),
        "priorities": ("become a fate", "learn the city's pressures", "stay unbound until possession"),
    },
    "Prole": {
        "group": "P.L.F.",
        "kind": "support",
        "plan": ("work public jobs", "scavenge safely", "keep the city moving"),
        "priorities": ("earn Anamnecytes", "stay employed", "support the labor flow"),
    },
    "Liquidator": {
        "group": "P.L.F.",
        "kind": "support",
        "plan": ("repair machinery", "dispose corpses", "burn Rot growths"),
        "priorities": ("prevent decay", "keep generators alive", "maintain public order"),
    },
    "Corpsman": {
        "group": "P.L.F.",
        "kind": "support",
        "plan": ("heal workers", "produce medicine", "restock treatment systems"),
        "priorities": ("keep bodies functional", "manage blood", "support the labor line"),
    },
    "Dealer": {
        "group": "M.B.",
        "kind": "economic",
        "plan": ("run Night Market orders", "trade goods", "expand DealerNet reach"),
        "priorities": ("move supply", "build market leverage", "grow Credits"),
    },
    "Banker": {
        "group": "M.B.",
        "kind": "economic",
        "plan": ("store Credits", "fulfill DealerNet orders", "protect wealth between lives"),
        "priorities": ("secure money", "support market networks", "preserve long-term value"),
    },
    "Controller": {
        "group": "Cortex",
        "kind": "enforcement",
        "plan": ("patrol the city", "confiscate contraband", "execute Limits"),
        "priorities": ("maintain order", "pressure dissent", "keep authority visible"),
    },
    "Sanitar": {
        "group": "Cortex",
        "kind": "enforcement",
        "plan": ("clean Rot", "repair damaged systems", "support Cortex operations"),
        "priorities": ("stop decay", "combine maintenance with force", "deny Rot safe ground"),
    },
    "Limitator": {
        "group": "Cortex",
        "kind": "enforcement",
        "plan": ("overwhelm resistance", "execute dissent", "deputize allies"),
        "priorities": ("enforce Limits", "protect Cortex power", "use maximum force when needed"),
    },
    "Scumbag": {
        "group": "Scum",
        "kind": "aggressive",
        "plan": ("destroy machinery", "spread disorder", "attack Cortex infrastructure"),
        "priorities": ("break the city", "build Rot momentum", "survive by chaos"),
    },
    "Zealot": {
        "group": "Scum",
        "kind": "ritual",
        "plan": ("feed Ritual Pits", "consecrate members", "turn Rot into faith"),
        "priorities": ("grow the cult", "weaponize belief", "bind the group to Rot"),
    },
    "Rogue": {
        "group": "Scum",
        "kind": "deceptive",
        "plan": ("use defector knowledge", "sabotage from within", "propagate Rot"),
        "priorities": ("betray institutions", "stay flexible", "exploit enforcement habits"),
    },
    "Malpractitioner": {
        "group": "Scum",
        "kind": "deceptive",
        "plan": ("weaponize medicine", "craft atrocity", "support Scum operations"),
        "priorities": ("corrupt healing", "turn care into harm", "keep the Rot moving"),
    },
    "Slave": {
        "group": "Cortex",
        "kind": "penalty",
        "plan": ("obey", "work off debt", "avoid further punishment"),
        "priorities": ("survive the camp", "reduce debt", "escape the worst outcomes"),
    },
    "Vomit Coffin": {
        "group": "Spoiler",
        "kind": "penalty",
        "plan": ("remain hidden", "mark the final corruption", "end the punishment chain"),
        "priorities": ("avoid further exposure", "stay classified", "signal the cursed state"),
    },
}

PERSONALITY_MARKERS = {
    "observer": ("Curiosity", 4),
    "support": ("Empathy", 5),
    "economic": ("Ambition", 4),
    "enforcement": ("Conscientiousness", 5),
    "aggressive": ("Conflict-Style", 6),
    "ritual": ("Loyalty", 5),
    "deceptive": ("Trust", 1),
    "penalty": ("Social-Energy", 1),
}

GROUP_ORDER = {
    "Neutral": 0,
    "P.L.F.": 1,
    "M.B.": 2,
    "Cortex": 3,
    "Scum": 4,
    "Spoiler": 5,
}


def _discover_role_names(root: Path, required_markers: tuple[str, ...]) -> set[str]:
    names: set[str] = set()
    for path in root.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if all(marker in text for marker in required_markers):
            names.add(path.stem)
    return names


class TestAneurismIVFates(unittest.TestCase):
    def setUp(self):
        self.specs = load_aiv_role_specs()
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

    def test_fate_inventory_and_initial_directives(self):
        expected_names = _discover_role_names(AIV_WIKI_ROOT, ("- Alignment:",)) | _discover_role_names(
            AIV_WIKI_ROOT, ("- Status:",)
        )
        actual_names = {spec.name for spec in self.specs}
        self.assertCountEqual(actual_names, expected_names)

        for spec in self.specs:
            with self.subTest(role=spec.name):
                expected = ROLE_EXPECTATIONS[spec.name]
                self.assertEqual(spec.mode, "aiv")
                self.assertEqual(spec.group, expected["group"])
                self.assertEqual(spec.kind, expected["kind"])
                self.assertEqual(spec.plan, expected["plan"])
                self.assertEqual(spec.priorities, expected["priorities"])
                self.assertTrue(spec.summary)
                self.assertTrue(spec.source_path.exists())

                for key, value in GROUP_POLICY_EXPECTATIONS[spec.group].items():
                    self.assertEqual(spec.policy_profile[key], value)

                marker_name, marker_index = PERSONALITY_MARKERS[spec.kind]
                self.assertEqual(spec.personality_profile[marker_name][0], marker_index)

    def test_pairwise_dispositions_and_social_openers(self):
        for source, target in permutations(self.specs, 2):
            with self.subTest(source=source.name, target=target.name):
                source_actor = self.actors[source.name]
                target_actor = self.actors[target.name]

                relation = expected_relation("aiv", source, target)
                diff = policy_diff_value(source_actor, target_actor)
                reverse_diff = policy_diff_value(target_actor, source_actor)
                label = policy_disposition_label(source_actor, target_actor)

                self.assertIsNotNone(diff)
                self.assertEqual(diff, reverse_diff)

                if relation == "Friendly":
                    self.assertLessEqual(diff, 10)
                    self.assertEqual(label, "Friendly")
                elif relation == "Hostile":
                    self.assertGreaterEqual(diff, 20)
                    self.assertEqual(label, "Hostile")
                else:
                    self.assertLessEqual(diff, 10)
                    self.assertIn(label, {"Friendly", "Neutral"})

                before_memory = len(target_actor.Memory.get(SOCIAL, {}))
                history: list[dict[str, object]] = []
                relation_out, prompt_type, _, record = simulate_social_encounter(
                    "aiv",
                    source,
                    target,
                    source_actor,
                    target_actor,
                    history=history,
                )

                self.assertEqual(relation_out, relation)
                self.assertEqual(prompt_type, lead_type_for("aiv", source, target, relation))
                self.assertEqual(len(history), 1)
                self._assert_common_prompt_record(
                    record,
                    prompt_type=prompt_type,
                    relation=relation,
                    source_name=source.name,
                    target_name=target.name,
                )
                self.assertEqual(len(target_actor.Memory.get(SOCIAL, {})), before_memory + 1)

    def test_full_city_sprawl_all_fates_together(self):
        ordered_specs = sorted(self.specs, key=lambda spec: (GROUP_ORDER[spec.group], spec.kind, spec.name))
        history: list[dict[str, object]] = []
        seen_prompt_types: set[str] = set()
        seen_relations: set[str] = set()

        for index, source in enumerate(ordered_specs):
            target = ordered_specs[(index + 1) % len(ordered_specs)]
            with self.subTest(step=index, source=source.name, target=target.name):
                relation, prompt_type, _, record = simulate_social_encounter(
                    "aiv",
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
        self.assertEqual(seen_relations, {"Neutral", "Friendly", "Hostile"})
        self.assertGreaterEqual(len(seen_prompt_types), 4)

        for spec in ordered_specs:
            with self.subTest(memory_of=spec.name):
                self.assertGreaterEqual(len(self.actors[spec.name].Memory.get(SOCIAL, {})), 1)


if __name__ == "__main__":
    unittest.main()
