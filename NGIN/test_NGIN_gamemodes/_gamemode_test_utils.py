from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re

from NGIN.NGIN_AI import NGIN_Simulae_Actor, generate_person
from NGIN.NGIN_config.madlibs import PERSONALITY_SCALE, POLICY_SCALE
from NGIN.SimulaeConstants import (
    EXHAUSTION,
    HUNGER,
    LONELINESS,
    NAME,
    SICK,
    TEMPERATURE,
    THIRST,
)
from NGIN.SimulaeNode import PERSONALITY, POLICY


REPO_ROOT = Path(__file__).resolve().parents[2]
TTT_WIKI_ROOT = REPO_ROOT / "NGINwiki" / "Gamemodes" / "Social Deduction" / "Trouble in Terrorist Town" / "Roles"
BOTC_WIKI_ROOT = REPO_ROOT / "NGINwiki" / "Gamemodes" / "Social Deduction" / "Blood on the Clocktower" / "Roles"
AIV_WIKI_ROOT = REPO_ROOT / "NGINwiki" / "Immersive Sim" / "Aneurism IV" / "roles"
HITMAN_WIKI_ROOT = (
    REPO_ROOT / "NGINwiki" / "Immersive Sim" / "Hitman World of Assassination" / "roles"
)


@dataclass(frozen=True)
class RoleSpec:
    mode: str
    name: str
    group: str
    kind: str
    summary: str
    source_path: Path
    plan: tuple[str, ...]
    priorities: tuple[str, ...]
    policy_profile: dict[str, tuple[int, int]]
    personality_profile: dict[str, tuple[int, int]]
    details: dict[str, str]


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_wiki_markup(text: str) -> str:
    if not text:
        return ""

    cleaned = text.strip()
    cleaned = re.sub(r"\[\[([^\]]+)\]\]", r"\1", cleaned)
    cleaned = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", cleaned)
    cleaned = cleaned.replace("```", "")
    return _normalize_whitespace(cleaned)


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _extract_prefixed_value(text: str, prefixes: tuple[str, ...]) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        for prefix in prefixes:
            if stripped.startswith(prefix):
                return strip_wiki_markup(stripped[len(prefix) :].strip())
    return ""


def _extract_heading_summary(text: str, heading: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == heading:
            for candidate in lines[index + 1 :]:
                stripped = candidate.strip()
                if not stripped:
                    continue
                if stripped.startswith("##") or stripped.startswith("#") or stripped.startswith("```"):
                    continue
                if stripped.startswith("- "):
                    continue
                return strip_wiki_markup(stripped)
            break
    return ""


def _extract_ttt_summary(text: str) -> str:
    return strip_wiki_markup(_first_nonempty_line(text))


def _extract_aiv_summary(text: str) -> str:
    lines = text.splitlines()
    saw_heading = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            saw_heading = True
            continue
        if not saw_heading:
            continue
        if stripped.startswith("- ") or stripped.startswith("##") or stripped.startswith("```"):
            continue
        return strip_wiki_markup(stripped)

    return ""


def _extract_title(text: str, fallback_name: str) -> str:
    first_line = _first_nonempty_line(text)
    if not first_line:
        return fallback_name

    heading_match = re.search(r"\[\[([^\]]+)\]\]", first_line)
    if heading_match:
        return strip_wiki_markup(heading_match.group(1))

    if first_line.startswith("#"):
        return strip_wiki_markup(first_line.lstrip("#").strip())

    if " is " in first_line:
        return strip_wiki_markup(first_line.split(" is ", 1)[0])

    return strip_wiki_markup(first_line)


def _neutral_policy_profile() -> dict[str, tuple[int, int]]:
    return {key: (3, 3) for key in POLICY_SCALE}


def _neutral_personality_profile() -> dict[str, tuple[int, int]]:
    return {key: (3, 3) for key in PERSONALITY_SCALE}


def _profile_with_overrides(base: dict[str, tuple[int, int]], overrides: dict[str, tuple[int, int]]) -> dict[str, tuple[int, int]]:
    profile = dict(base)
    profile.update(overrides)
    return profile


def _good_policy_profile() -> dict[str, tuple[int, int]]:
    return _profile_with_overrides(
        _neutral_policy_profile(),
        {
            "Diplomacy": (5, 4),
            "Justice": (5, 4),
            "Legality": (5, 4),
            "Militancy": (1, 4),
        },
    )


def _evil_policy_profile() -> dict[str, tuple[int, int]]:
    return _profile_with_overrides(
        _neutral_policy_profile(),
        {
            "Diplomacy": (1, 4),
            "Justice": (1, 4),
            "Legality": (1, 4),
            "Militancy": (5, 4),
        },
    )


def _aiv_policy_profile(group: str) -> dict[str, tuple[int, int]]:
    if group == "P.L.F.":
        return _profile_with_overrides(
            _neutral_policy_profile(),
            {
                "Economy": (4, 4),
                "Diplomacy": (5, 4),
                "Justice": (5, 4),
                "Legality": (5, 4),
                "Militancy": (2, 4),
            },
        )

    if group == "M.B.":
        return _profile_with_overrides(
            _neutral_policy_profile(),
            {
                "Economy": (5, 4),
                "Diplomacy": (5, 4),
                "Justice": (4, 4),
                "Legality": (5, 4),
                "Militancy": (2, 4),
            },
        )

    if group == "Cortex":
        return _profile_with_overrides(
            _neutral_policy_profile(),
            {
                "Government": (6, 5),
                "Legality": (6, 5),
                "Militancy": (6, 5),
                "Justice": (5, 4),
                "Diplomacy": (1, 4),
            },
        )

    if group == "Scum":
        return _profile_with_overrides(
            _neutral_policy_profile(),
            {
                "Government": (0, 5),
                "Legality": (0, 5),
                "Militancy": (5, 5),
                "Justice": (0, 5),
                "Diplomacy": (0, 4),
            },
        )

    if group == "Slave":
        return _aiv_policy_profile("Cortex")

    return _neutral_policy_profile()


def _hitman_policy_profile(group: str) -> dict[str, tuple[int, int]]:
    if group == "Agency":
        return _profile_with_overrides(
            _neutral_policy_profile(),
            {
                "Economy": (5, 2),
                "Diplomacy": (5, 2),
                "Government": (5, 2),
                "Justice": (5, 2),
                "Legality": (5, 2),
                "Technology": (5, 2),
            },
        )

    if group == "Security":
        return _neutral_policy_profile()

    if group == "Staff":
        return _profile_with_overrides(
            _neutral_policy_profile(),
            {
                "Economy": (4, 2),
                "Diplomacy": (4, 2),
                "Government": (4, 2),
                "Justice": (4, 2),
                "Legality": (4, 2),
                "Technology": (4, 2),
            },
        )

    if group == "Civilian":
        return _profile_with_overrides(
            _neutral_policy_profile(),
            {
                "Economy": (4, 2),
                "Diplomacy": (4, 2),
                "Government": (4, 2),
                "Justice": (4, 2),
                "Legality": (4, 2),
                "Technology": (4, 2),
            },
        )

    if group == "Target":
        return _neutral_policy_profile()

    return _neutral_policy_profile()


KIND_PERSONALITY_OVERRIDES = {
    "investigative": {
        "Curiosity": (6, 5),
        "Conscientiousness": (5, 4),
        "Trust": (5, 4),
        "Cooperativeness": (5, 4),
        "Social-Energy": (4, 4),
        "Assertiveness": (4, 3),
    },
    "support": {
        "Empathy": (5, 4),
        "Trust": (5, 4),
        "Conscientiousness": (5, 4),
        "Cooperativeness": (5, 4),
        "Social-Energy": (5, 4),
        "Curiosity": (4, 3),
    },
    "deceptive": {
        "Ambition": (5, 4),
        "Risk": (5, 4),
        "Assertiveness": (5, 4),
        "Trust": (1, 4),
        "Conscience": (1, 4),
        "Conflict-Style": (5, 4),
        "Curiosity": (4, 3),
    },
    "aggressive": {
        "Risk": (5, 4),
        "Assertiveness": (5, 4),
        "Conflict-Style": (6, 4),
        "Ambition": (5, 4),
        "Trust": (1, 4),
        "Conscience": (1, 4),
    },
    "economic": {
        "Conscientiousness": (5, 4),
        "Ambition": (4, 3),
        "Trust": (4, 3),
        "Curiosity": (4, 3),
        "Assertiveness": (4, 3),
    },
    "enforcement": {
        "Assertiveness": (5, 4),
        "Conscientiousness": (5, 4),
        "Resilience": (5, 4),
        "Trust": (3, 3),
        "Cooperativeness": (3, 3),
    },
    "ritual": {
        "Loyalty": (5, 4),
        "Conscience": (5, 4),
        "Emotionality": (5, 4),
        "Assertiveness": (5, 4),
        "Attachment": (5, 4),
    },
    "penalty": {
        "Social-Energy": (1, 4),
        "Assertiveness": (1, 4),
        "Resilience": (5, 4),
        "Curiosity": (3, 3),
    },
    "observer": {
        "Curiosity": (4, 3),
        "Social-Energy": (1, 3),
        "Trust": (3, 3),
        "Resilience": (4, 3),
    },
    "infiltrative": {
        "Curiosity": (5, 4),
        "Conscientiousness": (5, 4),
        "Trust": (1, 4),
        "Social-Energy": (2, 3),
        "Risk": (5, 4),
        "Assertiveness": (4, 3),
    },
    "handler": {
        "Empathy": (5, 4),
        "Trust": (5, 4),
        "Conscientiousness": (5, 4),
        "Social-Energy": (4, 3),
        "Curiosity": (4, 3),
        "Attachment": (4, 3),
    },
    "security": {
        "Assertiveness": (5, 4),
        "Conscientiousness": (5, 4),
        "Trust": (4, 3),
        "Conflict-Style": (5, 4),
        "Risk": (4, 3),
    },
    "staff": {
        "Empathy": (5, 4),
        "Cooperativeness": (5, 4),
        "Trust": (4, 3),
        "Conscientiousness": (4, 3),
        "Social-Energy": (4, 3),
    },
    "civilian": {
        "Curiosity": (4, 3),
        "Social-Energy": (3, 3),
        "Trust": (4, 3),
        "Conscientiousness": (3, 3),
        "Attachment": (4, 3),
    },
    "target": {
        "Ambition": (5, 4),
        "Assertiveness": (5, 4),
        "Trust": (1, 4),
        "Conscience": (2, 3),
        "Risk": (5, 4),
        "Conflict-Style": (4, 3),
    },
}


def _personality_profile_for_kind(kind: str) -> dict[str, tuple[int, int]]:
    return _profile_with_overrides(_neutral_personality_profile(), KIND_PERSONALITY_OVERRIDES.get(kind, {}))


KIND_PLANS = {
    "investigative": (
        "gather verified information",
        "cross-check claims",
    ),
    "support": (
        "support trusted allies",
        "share safe information",
    ),
    "deceptive": (
        "blend in",
        "misdirect suspicion",
    ),
    "aggressive": (
        "apply pressure",
        "remove obstacles",
    ),
    "economic": (
        "stabilize trade",
        "protect resources",
    ),
    "enforcement": (
        "patrol and intervene",
        "maintain order",
    ),
    "ritual": (
        "perform rites",
        "recruit believers",
    ),
    "penalty": (
        "survive the penalty state",
        "avoid worse outcomes",
    ),
    "observer": (
        "find a body to inhabit",
        "choose a fate",
    ),
    "infiltrative": (
        "map the venue",
        "borrow a disguise",
        "eliminate the target",
    ),
    "handler": (
        "brief the contract",
        "monitor the mission",
        "arrange extraction",
    ),
    "security": (
        "patrol the venue",
        "question irregularities",
        "lock down exits",
    ),
    "staff": (
        "serve the venue",
        "maintain routine",
        "spot anomalies",
    ),
    "civilian": (
        "move through the venue",
        "avoid danger",
        "flee if exposed",
    ),
    "target": (
        "keep to routine",
        "call for protection",
        "escape suspicion",
    ),
}


def _generic_plan_priorities(kind: str, focus: str, summary: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    plan = KIND_PLANS.get(kind, KIND_PLANS["support"])
    priorities = (
        summary or focus,
        f"focus: {focus}",
    )
    return plan, priorities


def _kind_to_policy_profile(mode: str, group: str) -> dict[str, tuple[int, int]]:
    if mode in {"ttt", "botc"}:
        return _good_policy_profile() if group == "Good" else _evil_policy_profile()
    if mode == "hitman":
        return _hitman_policy_profile(group)
    return _aiv_policy_profile(group)


def _kind_to_personality_profile(kind: str) -> dict[str, tuple[int, int]]:
    return _personality_profile_for_kind(kind)


def _build_role_spec(
    *,
    mode: str,
    name: str,
    group: str,
    kind: str,
    summary: str,
    source_path: Path,
    plan: tuple[str, ...],
    priorities: tuple[str, ...],
    details: dict[str, str],
) -> RoleSpec:
    policy_profile = _kind_to_policy_profile(mode, group)
    personality_profile = _kind_to_personality_profile(kind)
    return RoleSpec(
        mode=mode,
        name=name,
        group=group,
        kind=kind,
        summary=summary,
        source_path=source_path,
        plan=plan,
        priorities=priorities,
        policy_profile=policy_profile,
        personality_profile=personality_profile,
        details=details,
    )


def make_actor(spec: RoleSpec) -> NGIN_Simulae_Actor:
    actor = NGIN_Simulae_Actor(generate_person())
    actor.set_reference(NAME, spec.name)
    actor.Scales[PERSONALITY] = dict(spec.personality_profile)
    actor.Scales[POLICY] = dict(spec.policy_profile)

    actor.set_attribute(HUNGER, 0)
    actor.set_attribute(THIRST, 0)
    actor.set_attribute(EXHAUSTION, 0)
    actor.set_attribute(SICK, 0)
    actor.set_attribute(TEMPERATURE, 50)
    actor.set_attribute(LONELINESS, 0)

    return actor


def make_actor_map(specs: tuple[RoleSpec, ...] | list[RoleSpec]) -> dict[str, NGIN_Simulae_Actor]:
    return {spec.name: make_actor(spec) for spec in specs}


def policy_diff_value(actor: NGIN_Simulae_Actor, other: NGIN_Simulae_Actor) -> int | None:
    beliefs = other.get_political_beliefs()
    if beliefs is None:
        return None

    diff = actor.policy_diff(beliefs, warn=False)
    if diff is None:
        return None

    return diff[0]


def policy_disposition_label(actor: NGIN_Simulae_Actor, other: NGIN_Simulae_Actor) -> str | None:
    diff = policy_diff_value(actor, other)
    if diff is None:
        return None

    return actor.get_policy_disposition(diff)


TTT_BEHAVIOR = {
    "Innocent": {
        "kind": "support",
        "plan": (
            "build trust",
            "share evidence",
            "eliminate traitors",
        ),
        "priorities": (
            "protect confirmed allies",
            "stay alive",
            "keep suspicion pointed at traitors",
        ),
    },
    "Detective": {
        "kind": "investigative",
        "plan": (
            "investigate claims",
            "announce verified evidence",
            "coordinate innocents",
        ),
        "priorities": (
            "find traitors",
            "avoid wasted lynches",
            "protect the town's information flow",
        ),
    },
    "Traitor": {
        "kind": "deceptive",
        "plan": (
            "blend in",
            "misdirect suspicion",
            "remove confirmed threats",
        ),
        "priorities": (
            "hide the traitor team",
            "shape the narrative",
            "isolate detectives",
        ),
    },
}


AIV_BEHAVIOR = {
    "Spirit": {
        "kind": "observer",
        "plan": (
            "find a living fate",
            "choose a body to possess",
            "enter active play",
        ),
        "priorities": (
            "become a fate",
            "learn the city's pressures",
            "stay unbound until possession",
        ),
    },
    "Prole": {
        "kind": "support",
        "plan": (
            "work public jobs",
            "scavenge safely",
            "keep the city moving",
        ),
        "priorities": (
            "earn Anamnecytes",
            "stay employed",
            "support the labor flow",
        ),
    },
    "Liquidator": {
        "kind": "support",
        "plan": (
            "repair machinery",
            "dispose corpses",
            "burn Rot growths",
        ),
        "priorities": (
            "prevent decay",
            "keep generators alive",
            "maintain public order",
        ),
    },
    "Corpsman": {
        "kind": "support",
        "plan": (
            "heal workers",
            "produce medicine",
            "restock treatment systems",
        ),
        "priorities": (
            "keep bodies functional",
            "manage blood",
            "support the labor line",
        ),
    },
    "Dealer": {
        "kind": "economic",
        "plan": (
            "run Night Market orders",
            "trade goods",
            "expand DealerNet reach",
        ),
        "priorities": (
            "move supply",
            "build market leverage",
            "grow Credits",
        ),
    },
    "Banker": {
        "kind": "economic",
        "plan": (
            "store Credits",
            "fulfill DealerNet orders",
            "protect wealth between lives",
        ),
        "priorities": (
            "secure money",
            "support market networks",
            "preserve long-term value",
        ),
    },
    "Controller": {
        "kind": "enforcement",
        "plan": (
            "patrol the city",
            "confiscate contraband",
            "execute Limits",
        ),
        "priorities": (
            "maintain order",
            "pressure dissent",
            "keep authority visible",
        ),
    },
    "Sanitar": {
        "kind": "enforcement",
        "plan": (
            "clean Rot",
            "repair damaged systems",
            "support Cortex operations",
        ),
        "priorities": (
            "stop decay",
            "combine maintenance with force",
            "deny Rot safe ground",
        ),
    },
    "Limitator": {
        "kind": "enforcement",
        "plan": (
            "overwhelm resistance",
            "execute dissent",
            "deputize allies",
        ),
        "priorities": (
            "enforce Limits",
            "protect Cortex power",
            "use maximum force when needed",
        ),
    },
    "Scumbag": {
        "kind": "aggressive",
        "plan": (
            "destroy machinery",
            "spread disorder",
            "attack Cortex infrastructure",
        ),
        "priorities": (
            "break the city",
            "build Rot momentum",
            "survive by chaos",
        ),
    },
    "Zealot": {
        "kind": "ritual",
        "plan": (
            "feed Ritual Pits",
            "consecrate members",
            "turn Rot into faith",
        ),
        "priorities": (
            "grow the cult",
            "weaponize belief",
            "bind the group to Rot",
        ),
    },
    "Rogue": {
        "kind": "deceptive",
        "plan": (
            "use defector knowledge",
            "sabotage from within",
            "propagate Rot",
        ),
        "priorities": (
            "betray institutions",
            "stay flexible",
            "exploit enforcement habits",
        ),
    },
    "Malpractitioner": {
        "kind": "deceptive",
        "plan": (
            "weaponize medicine",
            "craft atrocity",
            "support Scum operations",
        ),
        "priorities": (
            "corrupt healing",
            "turn care into harm",
            "keep the Rot moving",
        ),
    },
    "Slave": {
        "kind": "penalty",
        "plan": (
            "obey",
            "work off debt",
            "avoid further punishment",
        ),
        "priorities": (
            "survive the camp",
            "reduce debt",
            "escape the worst outcomes",
        ),
    },
    "Vomit Coffin": {
        "kind": "penalty",
        "plan": (
            "remain hidden",
            "mark the final corruption",
            "end the punishment chain",
        ),
        "priorities": (
            "avoid further exposure",
            "stay classified",
            "signal the cursed state",
        ),
    },
}


def _botc_kind(role_type: str, summary: str) -> str:
    summary = summary.casefold()
    if role_type == "Minion":
        return "deceptive"
    if role_type == "Demon":
        return "aggressive"
    if role_type == "Outsider":
        return "support"
    if any(
        keyword in summary
        for keyword in (
            "learn",
            "see",
            "know",
            "discover",
            "identify",
            "information",
            "narrow",
            "announce",
            "test",
            "investigate",
            "detect",
        )
    ):
        return "investigative"
    if any(keyword in summary for keyword in ("protect", "heal", "save", "guard", "support", "prevent")):
        return "support"
    return "support"


def expected_relation(mode: str, left: RoleSpec, right: RoleSpec) -> str:
    if left.name == right.name:
        return "Friendly"

    if mode == "hitman":
        if left.group == right.group:
            return "Friendly"
        if "Agency" in {left.group, right.group} and {left.group, right.group} & {"Security", "Target"}:
            return "Hostile"
        return "Neutral"

    if mode in {"ttt", "botc"}:
        return "Friendly" if left.group == right.group else "Hostile"

    if left.group in {"Neutral", "Spoiler"} or right.group in {"Neutral", "Spoiler"}:
        return "Neutral"

    if left.group == right.group:
        return "Friendly"

    if {left.group, right.group} <= {"P.L.F.", "M.B."}:
        return "Friendly"

    if left.group == "Slave" and right.group == "Cortex":
        return "Friendly"
    if right.group == "Slave" and left.group == "Cortex":
        return "Friendly"

    if left.group in {"P.L.F.", "M.B."} and right.group in {"Cortex", "Scum"}:
        return "Hostile"
    if right.group in {"P.L.F.", "M.B."} and left.group in {"Cortex", "Scum"}:
        return "Hostile"

    if {left.group, right.group} == {"Cortex", "Scum"}:
        return "Hostile"

    return "Neutral"


def lead_type_for(mode: str, left: RoleSpec, right: RoleSpec, relation: str | None = None) -> str:
    relation = relation or expected_relation(mode, left, right)

    if mode == "hitman":
        if relation == "Friendly":
            return {
                "infiltrative": "Coordinate",
                "handler": "Inform",
                "security": "Coordinate",
                "staff": "Inform",
                "civilian": "Open",
                "target": "Inform",
            }.get(left.kind, "Inform")

        if relation == "Hostile":
            return {
                "infiltrative": "Direct",
                "handler": "Inquire",
                "security": "Direct",
                "staff": "Inquire",
                "civilian": "Inquire",
                "target": "Stance",
            }.get(left.kind, "Direct")

        return {
            "infiltrative": "Inquire",
            "handler": "Inform",
            "security": "Direct",
            "staff": "Inform",
            "civilian": "Open",
            "target": "Inquire",
        }.get(left.kind, "Inform")

    if relation == "Friendly":
        return {
            "investigative": "Inquire",
            "support": "Inform",
            "deceptive": "Coordinate",
            "aggressive": "Stance",
            "economic": "Coordinate",
            "enforcement": "Coordinate",
            "ritual": "Coordinate",
            "penalty": "Inform",
            "observer": "Open",
        }.get(left.kind, "Inform")

    if relation == "Hostile":
        return {
            "investigative": "Inquire",
            "support": "Inquire",
            "deceptive": "Inform",
            "aggressive": "Stance",
            "economic": "Inquire",
            "enforcement": "Direct",
            "ritual": "Stance",
            "penalty": "Close",
            "observer": "Open",
        }.get(left.kind, "Stance")

    return {
        "investigative": "Inquire",
        "support": "Inform",
        "deceptive": "Inform",
        "aggressive": "Stance",
        "economic": "Inquire",
        "enforcement": "Direct",
        "ritual": "Inquire",
        "penalty": "Close",
        "observer": "Open",
    }.get(left.kind, "Inform")


def _subtype_for(prompt_type: str, relation: str) -> str:
    if prompt_type == "Open":
        return "initiate"
    if prompt_type == "Close":
        return "farewell"
    if prompt_type == "Inform":
        return "share"
    if prompt_type == "Inquire":
        return "ask"
    if prompt_type == "Stance":
        return "agree" if relation == "Friendly" else "deny"
    if prompt_type == "Coordinate":
        return "organize"
    if prompt_type == "Direct":
        return "request"
    if prompt_type == "Negotiate":
        return "offer"
    if prompt_type == "Boundary":
        return "set-boundary"
    if prompt_type == "Affect":
        return "praise" if relation != "Hostile" else "criticize"
    if prompt_type == "Deceive":
        return "mislead"
    if prompt_type == "Topic":
        return "stay-topic"
    return "share"


def _domain_for_prompt(prompt_type: str) -> str:
    if prompt_type in {"Inform", "Stance", "Boundary"}:
        return "Policy"
    if prompt_type in {"Coordinate", "Direct"}:
        return "Task"
    if prompt_type == "Open":
        return "Identity"
    if prompt_type == "Close":
        return "Relationship"
    if prompt_type == "Negotiate":
        return "Resource"
    if prompt_type == "Affect":
        return "Relationship"
    if prompt_type == "Deceive":
        return "Intent"
    return "Fact"


def build_prompt(
    prompt_type: str,
    speaker_name: str,
    target_name: str,
    *,
    topic: str,
    relation: str,
    claim: str | None = None,
    question: str | None = None,
    subject: str | None = None,
    evidence: str | None = None,
    polarity: str | None = None,
    force: str | None = None,
    honesty: str | None = None,
    visibility: str | None = None,
    authority: str | None = None,
    time: str | None = None,
    domain: str | None = None,
) -> dict[str, object]:
    domain = domain or _domain_for_prompt(prompt_type)
    subtype = _subtype_for(prompt_type, relation)
    polarity = polarity or (
        "Positive" if relation == "Friendly" else "Negative" if relation == "Hostile" else "Neutral"
    )

    if evidence is None:
        evidence = "Strong" if prompt_type in {"Inform", "Coordinate", "Direct", "Negotiate", "Stance"} else "Weak"
    if force is None:
        if prompt_type in {"Open", "Topic"}:
            force = "Low"
        elif prompt_type in {"Direct", "Stance", "Close", "Boundary"} or relation == "Hostile":
            force = "High"
        else:
            force = "Medium"
    if honesty is None:
        honesty = "Deceptive" if prompt_type == "Deceive" else "Truthful"
    if visibility is None:
        visibility = "Dyadic"
    if authority is None:
        authority = "Peer"
    if time is None:
        time = "Present"

    if claim is None and prompt_type in {"Inform", "Stance", "Coordinate", "Direct", "Negotiate", "Boundary", "Deceive"}:
        if prompt_type == "Inform":
            claim = f"{speaker_name} shares an assessment of {topic}."
        elif prompt_type == "Stance":
            claim = f"{speaker_name} takes a position on {topic}."
        elif prompt_type == "Coordinate":
            claim = f"{speaker_name} wants to coordinate around {topic}."
        elif prompt_type == "Direct":
            claim = f"{speaker_name} wants action on {topic}."
        elif prompt_type == "Negotiate":
            claim = f"{speaker_name} offers terms about {topic}."
        elif prompt_type == "Boundary":
            claim = f"{speaker_name} sets a boundary around {topic}."
        elif prompt_type == "Deceive":
            claim = f"{speaker_name} conceals the truth about {topic}."

    if question is None and prompt_type == "Inquire":
        question = f"What is your position on {topic}?"

    if subject is None:
        subject = topic

    return {
        "eventtype": prompt_type,
        "event_subtype": subtype,
        "domain": domain,
        "subject": subject,
        "topic": topic,
        "claim": claim,
        "question": question,
        "source": speaker_name,
        "target": target_name,
        "qualifiers": {
            "Domain": domain,
            "Polarity": polarity,
            "Force": force,
            "Honesty": honesty,
            "Visibility": visibility,
            "Evidence": evidence,
            "Authority": authority,
            "Time": time,
        },
    }


def choose_counterpart(
    specs: tuple[RoleSpec, ...] | list[RoleSpec],
    source: RoleSpec,
    preferred_relations: tuple[str, ...] = ("Hostile", "Friendly", "Neutral"),
) -> RoleSpec:
    for desired_relation in preferred_relations:
        for candidate in specs:
            if candidate.name == source.name:
                continue
            if expected_relation(source.mode, source, candidate) == desired_relation:
                return candidate

    for candidate in specs:
        if candidate.name != source.name:
            return candidate

    raise ValueError("At least two roles are required to choose a counterpart.")


def choose_seed_pair(specs: tuple[RoleSpec, ...] | list[RoleSpec]) -> tuple[RoleSpec, RoleSpec, str]:
    for desired_relation in ("Hostile", "Friendly", "Neutral"):
        for left in specs:
            for right in specs:
                if left.name == right.name:
                    continue
                relation = expected_relation(left.mode, left, right)
                if relation == desired_relation:
                    return left, right, relation

    raise ValueError("Unable to choose a seed pair for the simulation.")


def simulate_social_encounter(
    mode: str,
    source: RoleSpec,
    target: RoleSpec,
    source_actor: NGIN_Simulae_Actor,
    target_actor: NGIN_Simulae_Actor,
    *,
    history: list[dict[str, object]] | None = None,
    topic: str | None = None,
    ) -> tuple[str, str, dict[str, object], dict[str, object] | None]:
    relation = expected_relation(mode, source, target)
    prompt_type = lead_type_for(mode, source, target, relation)
    topic = topic or source.summary or source.name
    if history is None:
        history = []

    prompt = build_prompt(
        prompt_type,
        source.name,
        target.name,
        topic=topic,
        relation=relation,
        subject=f"{source.name} -> {target.name}",
    )

    record = target_actor.handle_social_interaction(prompt, [source_actor], history)
    return relation, prompt_type, prompt, record


@lru_cache(maxsize=None)
def load_ttt_role_specs() -> tuple[RoleSpec, ...]:
    specs: list[RoleSpec] = []

    for path in sorted(TTT_WIKI_ROOT.glob("*.md"), key=lambda candidate: candidate.name.lower()):
        text = path.read_text(encoding="utf-8")
        team = _extract_prefixed_value(text, ("- Team:",))
        if not team:
            continue

        name = _extract_title(text, path.stem)
        behavior = TTT_BEHAVIOR.get(name)
        if not behavior:
            continue

        summary = _extract_ttt_summary(text)
        goal = _extract_prefixed_value(text, ("- Goal:",))
        group = "Good" if team in {"Innocent", "Detective"} else "Evil"
        specs.append(
            _build_role_spec(
                mode="ttt",
                name=name,
                group=group,
                kind=behavior["kind"],
                summary=summary,
                source_path=path,
                plan=behavior["plan"],
                priorities=behavior["priorities"],
                details={"team": team, "goal": goal},
            )
        )

    return tuple(specs)


@lru_cache(maxsize=None)
def load_botc_role_specs() -> tuple[RoleSpec, ...]:
    specs: list[RoleSpec] = []

    for path in sorted(BOTC_WIKI_ROOT.rglob("*.md"), key=lambda candidate: candidate.as_posix().lower()):
        text = path.read_text(encoding="utf-8")
        role_type = _extract_prefixed_value(text, ("- Role Type:",))
        team = _extract_prefixed_value(text, ("- Team:",))
        if not role_type or not team:
            continue

        name = _extract_title(text, path.stem)
        summary = _extract_heading_summary(text, "## Ability Summary") or _extract_heading_summary(text, "## World Role")
        if not summary:
            summary = _extract_ttt_summary(text)

        kind = _botc_kind(role_type, summary)
        plan, priorities = _generic_plan_priorities(kind, role_type, summary)
        group = "Good" if role_type in {"Townsfolk", "Outsider"} else "Evil"
        specs.append(
            _build_role_spec(
                mode="botc",
                name=name,
                group=group,
                kind=kind,
                summary=summary,
                source_path=path,
                plan=plan,
                priorities=priorities,
                details={"team": team, "role_type": role_type, "script": _extract_prefixed_value(text, ("- Script:",))},
            )
        )

    return tuple(specs)


@lru_cache(maxsize=None)
def load_aiv_role_specs() -> tuple[RoleSpec, ...]:
    specs: list[RoleSpec] = []

    for path in sorted(AIV_WIKI_ROOT.rglob("*.md"), key=lambda candidate: candidate.as_posix().lower()):
        text = path.read_text(encoding="utf-8")
        alignment = _extract_prefixed_value(text, ("- Alignment:",))
        faction = _extract_prefixed_value(text, ("- Faction:",))
        status = _extract_prefixed_value(text, ("- Status:",))
        if not (alignment or faction or status):
            continue

        name = _extract_title(text, path.stem)
        behavior = AIV_BEHAVIOR.get(name)
        if not behavior:
            continue

        summary = _extract_aiv_summary(text)
        group = faction or alignment or (name if name in {"Spirit", "Vomit Coffin"} else "Neutral")
        if group.startswith("P.L.F."):
            group = "P.L.F."
        elif group.startswith("M.B."):
            group = "M.B."
        elif group.startswith("Cortex"):
            group = "Cortex"
        elif group.startswith("Scum"):
            group = "Scum"
        elif name == "Spirit":
            group = "Neutral"
        elif name == "Vomit Coffin":
            group = "Spoiler"

        specs.append(
            _build_role_spec(
                mode="aiv",
                name=name,
                group=group,
                kind=behavior["kind"],
                summary=summary,
                source_path=path,
                plan=behavior["plan"],
                priorities=behavior["priorities"],
                details={
                    "alignment": alignment,
                    "faction": faction,
                    "status": status,
                    "roles": _extract_prefixed_value(text, ("- Roles:",)),
                    "upgrades": _extract_prefixed_value(text, ("- Upgrades to:", "- Upgrade from:")),
                },
            )
        )

    return tuple(specs)


HITMAN_BEHAVIOR = {
    "Agent 47": {
        "kind": "infiltrative",
        "plan": (
            "study the venue",
            "borrow a disguise",
            "eliminate the target",
        ),
        "priorities": (
            "stay unseen",
            "keep escape options open",
            "leave no witnesses",
        ),
    },
    "Diana Burnwood": {
        "kind": "handler",
        "plan": (
            "brief the contract",
            "monitor the mission",
            "arrange extraction",
        ),
        "priorities": (
            "preserve deniability",
            "feed 47 the right intel",
            "keep the contract clean",
        ),
    },
    "Guard": {
        "kind": "security",
        "plan": (
            "patrol the venue",
            "question irregularities",
            "lock down exits",
        ),
        "priorities": (
            "protect the target",
            "control access",
            "escalate suspicion fast",
        ),
    },
    "Head of Security": {
        "kind": "security",
        "plan": (
            "coordinate patrols",
            "tighten lockdowns",
            "seal exits",
        ),
        "priorities": (
            "control the response",
            "find the intruder",
            "avoid an embarrassing breach",
        ),
    },
    "Staff Member": {
        "kind": "staff",
        "plan": (
            "serve the venue",
            "maintain routine",
            "spot anomalies",
        ),
        "priorities": (
            "keep the place believable",
            "avoid panic",
            "stay helpful",
        ),
    },
    "Civilian": {
        "kind": "civilian",
        "plan": (
            "move through the venue",
            "avoid danger",
            "flee if exposed",
        ),
        "priorities": (
            "stay alive",
            "avoid direct involvement",
            "notice suspicious activity",
        ),
    },
    "Mission Target": {
        "kind": "target",
        "plan": (
            "keep to routine",
            "call for protection",
            "escape suspicion",
        ),
        "priorities": (
            "survive the day",
            "spot intruders",
            "avoid exposure",
        ),
    },
}


@lru_cache(maxsize=None)
def load_hitman_role_specs() -> tuple[RoleSpec, ...]:
    specs: list[RoleSpec] = []

    for path in sorted(HITMAN_WIKI_ROOT.rglob("*.md"), key=lambda candidate: candidate.as_posix().lower()):
        text = path.read_text(encoding="utf-8")
        alignment = _extract_prefixed_value(text, ("- Alignment:",))
        faction = _extract_prefixed_value(text, ("- Faction:",))
        status = _extract_prefixed_value(text, ("- Status:",))
        if not (alignment or faction or status):
            continue

        name = _extract_title(text, path.stem)
        behavior = HITMAN_BEHAVIOR.get(name)
        if not behavior:
            continue

        summary = _extract_heading_summary(text, "## World Role") or _extract_heading_summary(text, "## Mission Role")
        if not summary:
            summary = _first_nonempty_line(text)

        group = alignment or faction or status or "Neutral"
        specs.append(
            _build_role_spec(
                mode="hitman",
                name=name,
                group=group,
                kind=behavior["kind"],
                summary=summary,
                source_path=path,
                plan=behavior["plan"],
                priorities=behavior["priorities"],
                details={
                    "alignment": alignment,
                    "faction": faction,
                    "status": status,
                    "roles": _extract_prefixed_value(text, ("- Roles:",)),
                    "tools": _extract_prefixed_value(text, ("- Tools:", "- Signature Gear:", "- Loadout:")),
                },
            )
        )

    return tuple(specs)


__all__ = [
    "AIV_BEHAVIOR",
    "AIV_WIKI_ROOT",
    "BOTC_WIKI_ROOT",
    "HITMAN_BEHAVIOR",
    "HITMAN_WIKI_ROOT",
    "KIND_PLANS",
    "KIND_PERSONALITY_OVERRIDES",
    "REPO_ROOT",
    "RoleSpec",
    "TTT_BEHAVIOR",
    "TTT_WIKI_ROOT",
    "build_prompt",
    "choose_counterpart",
    "choose_seed_pair",
    "expected_relation",
    "lead_type_for",
    "load_aiv_role_specs",
    "load_botc_role_specs",
    "load_hitman_role_specs",
    "load_ttt_role_specs",
    "make_actor",
    "make_actor_map",
    "policy_diff_value",
    "policy_disposition_label",
    "simulate_social_encounter",
    "strip_wiki_markup",
]
