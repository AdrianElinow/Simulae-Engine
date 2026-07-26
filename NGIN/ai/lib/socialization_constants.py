
SOCIAL_INTERACTION_TYPES = [
    "Open",
    "Close",
    "Turn",
    "Topic",
    "Inform",
    "Inquire",
    "Stance",
    "Influence",
    "Affect",
    "Direct",
    "Negotiate",
    "Boundary",
    "Coordinate",
    "Deceive",
]

SOCIAL_INTERACTION_QUALIFIERS = {
    "Domain": [
        "Identity",
        "Fact",
        "Intent",
        "Policy",
        "Relationship",
        "Task",
        "Resource"
    ],
    "Polarity": [
        "Positive",
        "Negative",
        "Neutral"
    ],
    "Force": [
        "High",
        "Medium",
        "Low"
    ],
    "Honesty": [
        "Truthful",
        "Deceptive",
        "Neutral"
    ],
    "Visibility": [
        "Public",
        "Private",
        "Dyadic"
    ],
    "Evidence": [
        "None",
        "Weak",
        "Strong"
    ],
    "Authority": [
        "Peer",
        "Superior",
        "Subordinate",
        "None",
    ],
    "Time": [
        "Past",
        "Present",
        "Ongoing",
        "Future"
    ]
}


CRAFTING_RECIPES = {
    "stew": {
        "aliases": ["food", "meal", "rations"],
        "result_name": "food",
        "components": ["meat", "water", "herbs"],
        "placement": "inventory",
        "result_checks": {
            "edible": True,
            "drinkable": True,
            "consumable": True,
        },
        "result_attributes": {
            "nutrition": 18,
            "hydration": 12,
            "warmth": 4,
        },
    },
    "tea": {
        "aliases": ["drink", "beverage", "refreshment"],
        "result_name": "drink",
        "components": ["water", "herbs"],
        "placement": "inventory",
        "result_checks": {
            "drinkable": True,
            "consumable": True,
        },
        "result_attributes": {
            "hydration": 14,
            "warmth": 3,
        },
    },
    "medicine": {
        "aliases": ["medicine", "remedy", "medication"],
        "result_name": "medicine",
        "components": ["herbs", "water", "alcohol"],
        "placement": "inventory",
        "result_checks": {
            "consumable": True,
        },
        "result_attributes": {
            "healing": 20,
        },
    },
    "bandage": {
        "aliases": ["bandage", "first aid", "first_aid"],
        "result_name": "bandage",
        "components": ["cloth", "alcohol"],
        "placement": "inventory",
        "result_checks": {
            "consumable": True,
        },
        "result_attributes": {
            "healing": 8,
        },
    },
    "blanket": {
        "aliases": ["blanket", "cover", "cloak"],
        "result_name": "blanket",
        "components": ["cloth", "wool"],
        "placement": "attachments",
        "result_checks": {
            "wearable": True,
        },
        "result_attributes": {
            "warmth": 10,
            "comfort": 4,
        },
    },
    "bed": {
        "aliases": ["bed", "sleep", "shelter"],
        "result_name": "bed",
        "components": ["wood", "cloth", "straw"],
        "placement": "location",
        "result_checks": {
            "deployable": True,
        },
        "result_attributes": {
            "restfulness": 20,
            "comfort": 6,
        },
    },
}


# Social interactions are deliberately kept data-driven and deterministic so
# tests can exercise the prompt -> response -> follow-up loop without needing a
# language model. The canonical response families are still small, but the
# weighting logic can grow over time as more of the social model matures.
SOCIAL_RESPONSE_CANDIDATES = {
    "Open": ["Open", "Inquire", "Inform", "Affect", "Topic"],
    "Close": ["Close", "Affect", "Turn"],
    "Turn": ["Turn", "Affect", "Close"],
    "Topic": ["Topic", "Inform", "Inquire", "Stance"],
    "Inform": ["Inquire", "Inform", "Stance", "Topic", "Affect"],
    "Inquire": ["Inform", "Inquire", "Stance", "Deceive", "Turn", "Close"],
    "Stance": ["Stance", "Inform", "Inquire", "Affect", "Close"],
    "Influence": ["Stance", "Influence", "Negotiate", "Affect", "Close"],
    "Affect": ["Affect", "Stance", "Inform", "Close"],
    "Direct": ["Stance", "Direct", "Inquire", "Negotiate", "Close"],
    "Negotiate": ["Negotiate", "Stance", "Inform", "Inquire", "Close"],
    "Boundary": ["Boundary", "Stance", "Close", "Affect"],
    "Coordinate": ["Coordinate", "Stance", "Direct", "Inform", "Close"],
    "Deceive": ["Inquire", "Stance", "Deceive", "Close", "Affect"],
    # The wiki notes "Summary" as a social interaction family, so we support
    # it here even though it is not part of the current canonical list.
    "Summary": ["Inform", "Inquire", "Close"],
    "default": ["Inform", "Inquire", "Stance", "Close"],
}


SOCIAL_RESPONSE_SUBTYPES = {
    "Open": ["greet", "acknowledge", "initiate"],
    "Close": ["farewell", "withdraw"],
    "Turn": ["interrupt", "cede", "stall"],
    "Topic": ["stay-topic", "change-topic"],
    "Inform": ["answer", "clarify", "reveal", "share"],
    "Inquire": ["ask", "probe", "clarify", "challenge"],
    "Stance": ["agree", "deny", "accept", "refuse", "validate", "invalidate"],
    "Influence": ["persuade", "dissuade", "reassure", "pressure", "threaten"],
    "Affect": ["comfort", "commiserate", "praise", "criticize", "insult", "apologize", "joke", "complain"],
    "Direct": ["request", "demand", "command", "task", "delegate"],
    "Negotiate": ["offer", "counteroffer", "volunteer"],
    "Boundary": ["set-boundary", "violate-boundary"],
    "Coordinate": ["rally", "organize", "promote", "demote", "resign"],
    "Deceive": ["mislead", "conceal", "feign", "impersonate", "entrap", "cover"],
    "Summary": ["reflect", "summarize"],
    "default": ["acknowledge", "share", "clarify"],
}


SOCIAL_INTERACTION_ALIASES = {
    "greet": "Open",
    "greeting": "Open",
    "initiate": "Open",
    "open": "Open",
    "farewell": "Close",
    "withdraw": "Close",
    "withdrawal": "Close",
    "sever ties": "Close",
    "interrupt": "Turn",
    "cede": "Turn",
    "stall": "Turn",
    "phatic": "Turn",
    "change topic": "Topic",
    "stay topic": "Topic",
    "topic": "Topic",
    "claim": "Inform",
    "disclose": "Inform",
    "reveal": "Inform",
    "confess": "Inform",
    "observe": "Inform",
    "clarify": "Inform",
    "retract": "Inform",
    "inform": "Inform",
    "ask": "Inquire",
    "probe": "Inquire",
    "challenge": "Inquire",
    "inquire": "Inquire",
    "confirm": "Stance",
    "deny": "Stance",
    "agree": "Stance",
    "disagree": "Stance",
    "accept": "Stance",
    "refuse": "Stance",
    "validate": "Stance",
    "invalidate": "Stance",
    "stance": "Stance",
    "persuade": "Influence",
    "dissuade": "Influence",
    "reassure": "Influence",
    "pressure": "Influence",
    "threaten": "Influence",
    "influence": "Influence",
    "comfort": "Affect",
    "commiserate": "Affect",
    "praise": "Affect",
    "criticize": "Affect",
    "insult": "Affect",
    "apologize": "Affect",
    "joke": "Affect",
    "complain": "Affect",
    "affect": "Affect",
    "request": "Direct",
    "demand": "Direct",
    "command": "Direct",
    "task": "Direct",
    "delegate": "Direct",
    "direct": "Direct",
    "offer": "Negotiate",
    "counteroffer": "Negotiate",
    "volunteer": "Negotiate",
    "negotiate": "Negotiate",
    "set boundary": "Boundary",
    "violate boundary": "Boundary",
    "boundary": "Boundary",
    "rally": "Coordinate",
    "organize": "Coordinate",
    "promote": "Coordinate",
    "demote": "Coordinate",
    "resign": "Coordinate",
    "coordinate": "Coordinate",
    "mislead": "Deceive",
    "conceal": "Deceive",
    "feign": "Deceive",
    "impersonate": "Deceive",
    "entrap": "Deceive",
    "cover": "Deceive",
    "deceive": "Deceive",
    "summary": "Summary",
    "reflect": "Summary",
    "summarize": "Summary",
}

EVENT_CLASSES = ("physical", "social", "internal", "system")
EVENT_VISIBILITIES = ("public", "private", "dyadic")

RESPONSE_WEIGHTS = { interaction_type: { qualifier: { factor: 1.0 for factor in qualifying_factors } for qualifier, qualifying_factors in SOCIAL_INTERACTION_QUALIFIERS.items() } for interaction_type in SOCIAL_INTERACTION_TYPES }
