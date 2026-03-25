import unittest

from NGIN.NGIN_AI import NGIN_Simulae_Actor, generate_person
from NGIN.NGIN_Socialization import (
    SOCIAL_INTERACTION_QUALIFIERS,
    SOCIAL_INTERACTION_TYPES,
)
from NGIN.SimulaeNode import PERSONALITY, POLICY
from NGIN.SimulaeConstants import (
    EXHAUSTION,
    HUNGER,
    LONELINESS,
    NAME,
    SICK,
    TEMPERATURE,
    THIRST,
)


class TestNGINSocialization(unittest.TestCase):
    """Exercise the social appraisal and response loop end to end."""

    def setUp(self):
        self.asker = self._build_actor("Asker")
        self.respondent = self._build_actor("Responder")

    def _build_actor(self, name):
        actor = NGIN_Simulae_Actor(generate_person())
        actor.set_reference(NAME, name)
        actor.Scales[PERSONALITY] = {
            "Loyalty": (3, 4),
            "Ambition": (3, 4),
            "Empathy": (5, 6),
            "Emotionality": (4, 4),
            "Risk": (3, 3),
            "Conscience": (4, 5),
            "Conscientiousness": (5, 6),
            "Curiosity": (5, 7),
            "Trust": (4, 5),
            "Resilience": (4, 4),
            "Assertiveness": (3, 4),
            "Conflict-Style": (3, 3),
            "Humor": (4, 4),
            "Adaptability": (4, 4),
            "Attachment": (4, 5),
            "Cognitive-Style": (4, 5),
            "Cooperativeness": (5, 6),
            "Social-Energy": (5, 6),
        }
        actor.Scales[POLICY] = {
            "Economy": (3, 4),
            "Liberty": (4, 4),
            "Class": (4, 4),
            "Culture": (4, 4),
            "Diplomacy": (5, 6),
            "Militancy": (3, 3),
            "Diversity": (4, 4),
            "Secularity": (4, 4),
            "Technology": (4, 4),
            "Legality": (4, 4),
            "Justice": (4, 4),
            "Natural-Balance": (4, 4),
            "Government": (4, 4),
        }

        # Keep the social tests focused on conversation behavior rather than
        # survival needs.
        actor.set_attribute(HUNGER, 0)
        actor.set_attribute(THIRST, 0)
        actor.set_attribute(EXHAUSTION, 0)
        actor.set_attribute(SICK, 0)
        actor.set_attribute(TEMPERATURE, 50)
        actor.set_attribute(LONELINESS, 0)

        return actor

    def _build_prompt(self, event_type, event_subtype=None, **fields):
        qualifiers = fields.pop("qualifiers", None) or {
            "Domain": "Fact",
            "Polarity": "Neutral",
            "Force": "Low",
            "Honesty": "Truthful",
            "Visibility": "Dyadic",
            "Evidence": "Strong",
            "Authority": "Peer",
            "Time": "Present",
        }

        event = {
            "eventtype": event_type,
            "event_subtype": event_subtype,
            "qualifiers": qualifiers,
        }
        event.update(fields)
        return event

    def test_appraise_social_event_covers_core_event_types(self):
        """Every core interaction family should appraise without crashing."""

        subtype_by_type = {
            "Open": "greet",
            "Close": "farewell",
            "Turn": "interrupt",
            "Topic": "change-topic",
            "Inform": "claim",
            "Inquire": "ask",
            "Stance": "agree",
            "Influence": "persuade",
            "Affect": "praise",
            "Direct": "request",
            "Negotiate": "offer",
            "Boundary": "set-boundary",
            "Coordinate": "organize",
            "Deceive": "mislead",
        }

        for event_type in SOCIAL_INTERACTION_TYPES:
            with self.subTest(event_type=event_type):
                qualifiers = {
                    "Domain": "Fact",
                    "Polarity": "Negative" if event_type == "Deceive" else "Neutral",
                    "Force": "High" if event_type == "Deceive" else "Low",
                    "Honesty": "Deceptive" if event_type == "Deceive" else "Truthful",
                    "Visibility": "Dyadic",
                    "Evidence": "None" if event_type == "Deceive" else "Strong",
                    "Authority": "Peer",
                    "Time": "Present",
                }
                appraisal = self.respondent.appraise_social_event(
                    self._build_prompt(
                        event_type,
                        subtype_by_type[event_type],
                        domain="Fact",
                        subject="topic",
                        qualifiers=qualifiers,
                    )
                )

                self.assertIsNotNone(appraisal)
                self.assertEqual(appraisal["event_type"], event_type)
                self.assertIn("threat", appraisal)
                self.assertGreaterEqual(appraisal["salience"], 0)

                if event_type == "Open":
                    self.assertGreater(appraisal["valence"], 0)
                elif event_type == "Inquire":
                    self.assertGreaterEqual(appraisal["urgency"], 1)
                elif event_type == "Deceive":
                    self.assertLess(appraisal["credibility"], 0)

    def test_first_order_social_prompt_and_response(self):
        """An initial question should produce a direct answer."""

        history = []
        prompt = self._build_prompt(
            "Inquire",
            "ask",
            domain="Identity",
            subject="origin",
            topic="origin",
            question="Where are you from?",
            evidence="Weak",
        )

        interaction = self.respondent.handle_social_interaction(prompt, [self.asker], history)

        self.assertIsNotNone(interaction)

        if interaction == None:
            self.fail("Interaction was 'None'")

        self.assertEqual(interaction["prompt_event_type"], "Inquire")
        self.assertEqual(interaction["response_type"], "Inform")
        self.assertEqual(interaction["response"]["response_type"], "Inform")
        self.assertEqual(interaction["response"]["response_subtype"], "answer")
        self.assertEqual(interaction["response"]["content"]["intent"], "answer_or_share")
        self.assertEqual(
            interaction["response"]["content"]["information_target"]["question"],
            "Where are you from?",
        )
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["response_type"], "Inform")

    def test_second_order_social_follow_up(self):
        """The original prompting NPC should be able to respond to the answer."""

        history = []
        prompt = self._build_prompt(
            "Inquire",
            "ask",
            domain="Identity",
            subject="origin",
            topic="origin",
            question="Where are you from?",
            evidence="Weak",
        )

        first_interaction = self.respondent.handle_social_interaction(prompt, [self.asker], history)
        self.assertIsNotNone(first_interaction)

        follow_up = self.asker.handle_social_interaction(first_interaction["response"], [self.respondent], history)

        self.assertIsNotNone(follow_up)

        if follow_up == None:
            self.fail("follow_up was 'None'")

        self.assertEqual(follow_up["prompt_event_type"], "Inform")
        self.assertEqual(follow_up["response_type"], "Inquire")
        self.assertEqual(follow_up["response"]["response_subtype"], "probe")
        self.assertEqual(follow_up["response"]["content"]["intent"], "ask_for_evidence")
        self.assertEqual(follow_up["response"]["content"]["inquiry_target"]["topic"], "origin")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1]["prompt_event_type"], "Inform")
        self.assertEqual(history[1]["response_type"], "Inquire")

    def test_social_edge_cases(self):
        """Malformed or impossible interactions should fail closed."""

        history = []

        neutral_appraisal = self.respondent.appraise_social_event(None)
        self.assertEqual(neutral_appraisal["valence"], 0)
        self.assertEqual(neutral_appraisal["threat"]["social"], 0)

        self.assertIsNone(self.respondent.handle_social_interaction(None, [self.asker], history))
        self.assertEqual(history, [])

        malformed_prompt = {"qualifiers": {"Domain": "Fact"}}
        self.assertIsNone(self.respondent.handle_social_interaction(malformed_prompt, [self.asker], history))
        self.assertEqual(history, [])

        no_party_prompt = self._build_prompt("Open", "greet", domain="Fact", subject="hello")
        self.assertIsNone(self.respondent.handle_social_interaction(no_party_prompt, [], history))
        self.assertEqual(history, [])

        appraisal = self.respondent.appraise_social_event(no_party_prompt)
        self.assertTrue(self.respondent.hard_gate([self.asker], appraisal, "Close", no_party_prompt, []))


if __name__ == "__main__":
    unittest.main()
