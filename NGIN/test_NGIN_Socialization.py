import json
import textwrap
import unittest

from NGIN.NGIN_AI import NGIN_Simulae_Actor, generate_person
from NGIN.NGIN_Socialization import (
    SOCIAL_INTERACTION_TYPES,
)
from NGIN.SimulaeNode import PERSONALITY, POLICY
from NGIN.SimulaeConstants import (
    EXHAUSTION,
    HUNGER,
    LONELINESS,
    NAME,
    SOCIAL,
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

    def _trait_strength(self, actor, trait_name):
        """Project a personality factor into a small numeric score."""

        personality = actor.get_personality()
        self.assertIsNotNone(personality)
        assert personality is not None

        factor = personality.get(trait_name)
        if not factor or not isinstance(factor, (tuple, list)) or len(factor) < 2:
            return 0.0

        try:
            index, strength = factor
            return (float(index) - 3.0) * float(strength)
        except (TypeError, ValueError):
            return 0.0

    def _choose_initiated_prompt_type(self, actor, social_context, candidate_types):
        """Let an actor pick a conversation starter from its own appraisal.

        The helper keeps initiative selection inside the actor's evaluation
        space instead of hard-coding the starter in the test body. That makes
        the test read more like a social exchange and less like a scripted
        prompt/response fixture.
        """

        if not candidate_types:
            return None

        appraisal = actor.appraise_social_event(social_context)
        self.assertIsNotNone(appraisal)
        assert appraisal is not None

        scores = {}
        evidence = appraisal.get("evidence")
        topic = appraisal.get("topic")
        source = appraisal.get("source")
        question = appraisal.get("question")

        # Strong, sourced facts should be relayed directly. By contrast,
        # weak or uncertain material should push the actor toward asking
        # instead of pretending certainty it does not have.
        if "Inform" in candidate_types and source and topic and evidence in {"Strong", "strong"}:
            return "Inform"

        if "Inquire" in candidate_types and (question or evidence in {"Weak", "weak", "None", "none"}) and not source:
            return "Inquire"

        for candidate in candidate_types:
            score = 0.0

            if candidate == "Open":
                score += float(appraisal.get("valence", 0)) * 2.0
                score += self._trait_strength(actor, "Empathy") * 0.9
                score += self._trait_strength(actor, "Cooperativeness") * 0.7
                score += self._trait_strength(actor, "Social-Energy") * 0.4
            elif candidate == "Inquire":
                score += max(0.0, 3.0 - float(appraisal.get("credibility", 0))) * 2.0
                score += float(appraisal.get("urgency", 0))
                score += self._trait_strength(actor, "Curiosity") * 1.0
                score += self._trait_strength(actor, "Trust") * 0.2
                if evidence in {"Weak", "weak", "None", "none"}:
                    score += 2.5
                if not topic:
                    score += 1.5
                if question:
                    score += 0.5
            elif candidate == "Inform":
                score += float(appraisal.get("credibility", 0)) * 2.0
                score += self._trait_strength(actor, "Conscientiousness") * 1.0
                score += self._trait_strength(actor, "Trust") * 0.4
                if topic:
                    score += 1.5
                if source:
                    score += 1.0
                if evidence in {"Strong", "strong"}:
                    score += 1.5
            else:
                score += float(appraisal.get("salience", 0))

            scores[candidate] = score

        best_score = max(scores.values())
        for candidate in candidate_types:
            if scores[candidate] == best_score:
                return candidate

        return candidate_types[0]

    def _pretty_json(self, payload):
        """Return a stable, human-readable JSON string for debug output."""

        return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True, default=str)

    def _describe_social_prompt(self, payload):
        """Summarize a prompt as plain language."""

        if not isinstance(payload, dict):
            return str(payload)

        event_type = payload.get("event_type") or payload.get("prompt_event_type")
        subtype = payload.get("event_subtype") or payload.get("prompt_event_subtype")
        topic = payload.get("topic") or payload.get("subject") or payload.get("claim")
        source = payload.get("source")
        question = payload.get("question")
        domain = payload.get("domain")

        parts = []
        if event_type == "Inquire":
            if question:
                parts.append(f"asks: {question}")
            elif topic:
                parts.append(f"asks about {topic}")
            else:
                parts.append("asks a question")
        elif event_type == "Inform":
            if topic and source:
                parts.append(f"relays {topic} from {source}")
            elif topic:
                parts.append(f"shares {topic}")
            elif source:
                parts.append(f"shares information from {source}")
            else:
                parts.append("shares information")
        elif event_type == "Open":
            parts.append("opens the conversation")
        elif event_type == "Close":
            parts.append("ends the conversation")
        elif event_type == "Stance":
            parts.append("takes a stance")
        elif event_type == "Affect":
            parts.append("expresses emotion")
        elif event_type == "Direct":
            parts.append("issues a direct request")
        elif event_type == "Coordinate":
            parts.append("coordinates action")
        elif event_type == "Negotiate":
            parts.append("negotiates terms")
        else:
            parts.append("makes a social move")

        if subtype:
            parts.append(f"subtype={subtype}")
        if domain:
            parts.append(f"domain={domain}")
        if topic:
            parts.append(f"topic={topic}")

        return "; ".join(parts)

    def _describe_social_response(self, payload):
        """Summarize a response as plain language."""

        if not isinstance(payload, dict):
            return str(payload)

        response_type = payload.get("response_type") or payload.get("event_type")
        subtype = payload.get("response_subtype") or payload.get("event_subtype")
        content = payload.get("content") if isinstance(payload.get("content"), dict) else {}
        topic = content.get("topic")
        intent = content.get("intent")
        question = content.get("question")
        source = content.get("source")
        claim = content.get("claim")

        parts = []
        if response_type == "Inform":
            if claim:
                parts.append(f"shares: {claim}")
            elif topic and source:
                parts.append(f"shares {topic} from {source}")
            elif topic:
                parts.append(f"shares {topic}")
            else:
                parts.append("provides information")
        elif response_type == "Inquire":
            if question:
                parts.append(f"asks: {question}")
            elif topic:
                parts.append(f"asks about {topic}")
            else:
                parts.append("asks for clarification")
        elif response_type == "Open":
            parts.append("opens or acknowledges")
        elif response_type == "Close":
            parts.append("closes the exchange")
        elif response_type == "Stance":
            parts.append("takes a stance")
        else:
            parts.append("responds")

        if subtype:
            parts.append(f"subtype={subtype}")
        if intent:
            parts.append(f"intent={intent}")

        return "; ".join(parts)

    def _debug_print_social_interaction(self, label, speaker, listener, interaction):
        """Print a human-readable transcript line for a social exchange."""

        speaker_name = speaker.get_reference(NAME) if speaker else None
        listener_name = listener.get_reference(NAME) if listener else None

        print(f"[{label}] {speaker_name} -> {listener_name}", flush=True)

        if isinstance(interaction, dict):
            prompt = interaction.get("prompt_event")
            response = interaction.get("response")
            print("  prompt:", flush=True)
            print(f"    meaning: {self._describe_social_prompt(prompt)}", flush=True)
            print("    json:", flush=True)
            print(textwrap.indent(self._pretty_json(prompt), "      "), flush=True)
            print("  response:", flush=True)
            print(f"    meaning: {self._describe_social_response(response)}", flush=True)
            print("    json:", flush=True)
            print(textwrap.indent(self._pretty_json(response), "      "), flush=True)
            print(
                f"  meta: id={interaction.get('id')} "
                f"prompt_type={interaction.get('prompt_event_type')} "
                f"response_type={interaction.get('response_type')} "
                f"party_count={len(interaction.get('parties')) if isinstance(interaction.get('parties'), list) else 0}",
                flush=True,
            )
        else:
            print(f"  interaction: {interaction}", flush=True)

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
                assert appraisal is not None
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
        assert interaction is not None

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
        assert first_interaction is not None

        follow_up = self.asker.handle_social_interaction(first_interaction["response"], [self.respondent], history)

        self.assertIsNotNone(follow_up)
        assert follow_up is not None

        self.assertEqual(follow_up["prompt_event_type"], "Inform")
        self.assertEqual(follow_up["response_type"], "Inquire")
        self.assertEqual(follow_up["response"]["response_subtype"], "probe")
        self.assertEqual(follow_up["response"]["content"]["intent"], "ask_for_evidence")
        self.assertEqual(follow_up["response"]["content"]["inquiry_target"]["topic"], "origin")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1]["prompt_event_type"], "Inform")
        self.assertEqual(history[1]["response_type"], "Inquire")

    def test_three_npc_information_relay_across_conversations(self):
        """A learned fact should be carried into a later conversation with a third NPC."""

        sender = self._build_actor("Sender")
        relay = self._build_actor("Relay")
        recipient = self._build_actor("Recipient")

        print("\n=== Guided 3-NPC relay: conversation 1 ===", flush=True)

        first_history = []
        first_prompt = self._build_prompt(
            "Inquire",
            "ask",
            domain="Identity",
            subject="origin",
            topic="origin",
            question="Where are you from?",
            evidence="Weak",
        )

        first_interaction = relay.handle_social_interaction(first_prompt, [sender], first_history)
        self.assertIsNotNone(first_interaction)
        assert first_interaction is not None
        self.assertEqual(len(first_history), 1)
        self._debug_print_social_interaction("guided-1", relay, sender, first_interaction)

        first_response_type = first_interaction.get("response_type")
        self.assertIsNotNone(first_response_type)
        self.assertIsInstance(first_response_type, str)
        self.assertEqual(first_response_type, "Inform")

        first_response = first_interaction.get("response")
        self.assertIsInstance(first_response, dict)
        first_content = first_response.get("content")
        self.assertIsInstance(first_content, dict)
        first_information_target = first_content.get("information_target")
        self.assertIsInstance(first_information_target, dict)

        first_topic = first_information_target.get("topic")
        self.assertIsInstance(first_topic, str)
        self.assertEqual(first_topic, "origin")

        first_question = first_information_target.get("question")
        self.assertIsInstance(first_question, str)
        self.assertEqual(first_question, "Where are you from?")

        sender_name = sender.get_reference(NAME)
        self.assertIsInstance(sender_name, str)

        second_history = []
        second_prompt = self._build_prompt(
            "Inquire",
            "ask",
            domain="Identity",
            subject=first_topic,
            topic=first_topic,
            question="Can you repeat what you learned about that origin?",
            evidence="Weak",
            source=sender_name,
        )

        print("\n=== Guided 3-NPC relay: conversation 2 ===", flush=True)
        second_interaction = relay.handle_social_interaction(second_prompt, [recipient], second_history)
        self.assertIsNotNone(second_interaction)
        assert second_interaction is not None
        self.assertEqual(len(second_history), 1)
        self._debug_print_social_interaction("guided-2", relay, recipient, second_interaction)

        second_prompt_type = second_interaction.get("prompt_event_type")
        self.assertIsNotNone(second_prompt_type)
        self.assertIsInstance(second_prompt_type, str)
        self.assertEqual(second_prompt_type, "Inquire")

        second_response_type = second_interaction.get("response_type")
        self.assertIsNotNone(second_response_type)
        self.assertIsInstance(second_response_type, str)
        self.assertEqual(second_response_type, "Inform")

        second_response = second_interaction.get("response")
        self.assertIsInstance(second_response, dict)
        second_content = second_response.get("content")
        self.assertIsInstance(second_content, dict)
        second_information_target = second_content.get("information_target")
        self.assertIsInstance(second_information_target, dict)

        second_topic = second_information_target.get("topic")
        self.assertIsInstance(second_topic, str)
        self.assertEqual(second_topic, "origin")

        second_source = second_information_target.get("source")
        self.assertIsInstance(second_source, str)
        self.assertEqual(second_source, sender_name)

        second_question = second_information_target.get("question")
        self.assertIsInstance(second_question, str)
        self.assertEqual(second_question, "Can you repeat what you learned about that origin?")

    def test_self_directed_three_npc_information_relay(self):
        """NPCs should choose their own opener and relay from appraisal, not scripting."""

        sender = self._build_actor("Sender")
        relay = self._build_actor("Relay")
        recipient = self._build_actor("Recipient")

        print("\n=== Self-directed 3-NPC relay: setup ===", flush=True)

        # Make the relay more likely to ask when it lacks a fact, but more
        # likely to relay once it has a concrete claim to pass on.
        relay_personality = relay.get_personality()
        self.assertIsNotNone(relay_personality)
        assert relay_personality is not None
        relay_personality["Curiosity"] = (6, 8)
        relay_personality["Conscientiousness"] = (7, 8)
        relay_personality["Empathy"] = (2, 2)
        relay_personality["Social-Energy"] = (3, 2)

        recipient_personality = recipient.get_personality()
        self.assertIsNotNone(recipient_personality)
        assert recipient_personality is not None
        recipient_personality["Curiosity"] = (6, 8)
        recipient_personality["Trust"] = (5, 6)

        first_history = []
        first_context = {
            "domain": "Identity",
            "subject": "origin",
            "topic": "origin",
            "question": "Where are you from?",
            "evidence": "Weak",
            "qualifiers": {
                "Domain": "Identity",
                "Polarity": "Neutral",
                "Force": "Low",
                "Honesty": "Truthful",
                "Visibility": "Dyadic",
                "Evidence": "Weak",
                "Authority": "Peer",
                "Time": "Present",
            },
        }

        first_prompt_type = self._choose_initiated_prompt_type(relay, first_context, ("Open", "Inquire", "Inform"))
        self.assertEqual(first_prompt_type, "Inquire")
        print(f"Chosen first prompt type: {first_prompt_type}", flush=True)

        first_prompt_subtype = {
            "Open": "initiate",
            "Inquire": "ask",
            "Inform": "share",
        }[first_prompt_type]
        first_prompt = self._build_prompt(first_prompt_type, first_prompt_subtype, **first_context)

        first_interaction = relay.handle_social_interaction(first_prompt, [sender], first_history)
        self.assertIsNotNone(first_interaction)
        assert first_interaction is not None
        self.assertEqual(len(first_history), 1)
        self._debug_print_social_interaction("self-directed-1", relay, sender, first_interaction)
        self.assertEqual(first_interaction["prompt_event_type"], first_prompt_type)
        self.assertEqual(first_interaction["response_type"], "Inform")

        first_response = first_interaction["response"]
        self.assertIsInstance(first_response, dict)
        first_content = first_response.get("content")
        self.assertIsInstance(first_content, dict)
        first_information_target = first_content.get("information_target")
        self.assertIsInstance(first_information_target, dict)

        first_topic = first_information_target.get("topic")
        self.assertIsInstance(first_topic, str)
        self.assertEqual(first_topic, "origin")

        first_question = first_information_target.get("question")
        self.assertIsInstance(first_question, str)
        self.assertEqual(first_question, "Where are you from?")

        sender_name = sender.get_reference(NAME)
        self.assertIsInstance(sender_name, str)

        second_history = []
        second_context = {
            "domain": "Identity",
            "subject": first_topic,
            "topic": first_topic,
            "claim": f"{sender_name} is from {first_topic}.",
            "source": sender_name,
            "evidence": "Strong",
            "qualifiers": {
                "Domain": "Identity",
                "Polarity": "Neutral",
                "Force": "Low",
                "Honesty": "Truthful",
                "Visibility": "Dyadic",
                "Evidence": "Strong",
                "Authority": "Peer",
                "Time": "Present",
            },
        }

        second_prompt_type = self._choose_initiated_prompt_type(relay, second_context, ("Open", "Inquire", "Inform"))
        self.assertEqual(second_prompt_type, "Inform")
        print(f"Chosen second prompt type: {second_prompt_type}", flush=True)

        second_prompt_subtype = {
            "Open": "initiate",
            "Inquire": "ask",
            "Inform": "share",
        }[second_prompt_type]
        second_prompt = self._build_prompt(second_prompt_type, second_prompt_subtype, **second_context)

        second_interaction = relay.handle_social_interaction(second_prompt, [recipient], second_history)
        self.assertIsNotNone(second_interaction)
        assert second_interaction is not None
        self.assertEqual(len(second_history), 1)
        self._debug_print_social_interaction("self-directed-2", relay, recipient, second_interaction)
        self.assertEqual(second_interaction["prompt_event_type"], "Inform")

        second_response_type = second_interaction["response_type"]
        self.assertIn(second_response_type, {"Inform", "Inquire"})

        second_response = second_interaction["response"]
        self.assertIsInstance(second_response, dict)
        second_content = second_response.get("content")
        self.assertIsInstance(second_content, dict)
        self.assertEqual(second_content.get("topic"), "origin")

        if second_response_type == "Inform":
            second_information_target = second_content.get("information_target")
            self.assertIsInstance(second_information_target, dict)
            self.assertEqual(second_information_target.get("topic"), "origin")
        else:
            second_inquiry_target = second_content.get("inquiry_target")
            self.assertIsInstance(second_inquiry_target, dict)
            self.assertEqual(second_inquiry_target.get("topic"), "origin")

    def test_long_conversational_exchange_between_npcs(self):
        """NPCs should sustain a longer alternating exchange without losing context."""

        history = []
        current_actor = self.respondent
        current_partner = self.asker
        current_event = self._build_prompt(
            "Inquire",
            "ask",
            domain="Identity",
            subject="origin",
            topic="origin",
            question="Where are you from, and what brought you here?",
            evidence="Weak",
        )

        seen_response_types = set()
        seen_topics = set()

        print("\n=== Long alternating exchange ===", flush=True)
        print(
            f"start: {current_actor.get_reference(NAME)} -> {current_partner.get_reference(NAME)}",
            flush=True,
        )

        for turn_index in range(10):
            with self.subTest(turn=turn_index):
                interaction = current_actor.handle_social_interaction(current_event, [current_partner], history)
                self.assertIsNotNone(interaction)
                assert interaction is not None
                self._debug_print_social_interaction(f"turn-{turn_index}", current_actor, current_partner, interaction)

                self.assertEqual(len(history), turn_index + 1)

                prompt_type = interaction.get("prompt_event_type")
                self.assertIsNotNone(prompt_type)
                self.assertIsInstance(prompt_type, str)

                response_type = interaction.get("response_type")
                self.assertIsNotNone(response_type)
                self.assertIsInstance(response_type, str)
                self.assertIn(prompt_type, SOCIAL_INTERACTION_TYPES)
                self.assertIn(response_type, SOCIAL_INTERACTION_TYPES)
                seen_response_types.add(response_type)

                response = interaction.get("response")
                self.assertIsInstance(response, dict)

                response_prompt_type = response.get("prompt_event_type")
                self.assertIsNotNone(response_prompt_type)
                self.assertIsInstance(response_prompt_type, str)
                self.assertEqual(response_prompt_type, prompt_type)

                response_response_type = response.get("response_type")
                self.assertIsNotNone(response_response_type)
                self.assertIsInstance(response_response_type, str)
                self.assertEqual(response_response_type, response_type)

                content = response.get("content")
                self.assertIsInstance(content, dict)
                topic = content.get("topic")
                self.assertIsInstance(topic, str)
                self.assertEqual(topic, "origin")
                seen_topics.add(topic)

                if response_type == "Inform":
                    information_target = content.get("information_target")
                    self.assertIsInstance(information_target, dict)
                    information_topic = information_target.get("topic")
                    self.assertIsInstance(information_topic, str)
                    self.assertEqual(information_topic, "origin")
                elif response_type == "Inquire":
                    inquiry_target = content.get("inquiry_target")
                    self.assertIsInstance(inquiry_target, dict)
                    inquiry_topic = inquiry_target.get("topic")
                    self.assertIsInstance(inquiry_topic, str)
                    self.assertEqual(inquiry_topic, "origin")

                current_event = response
                current_actor, current_partner = current_partner, current_actor

        self.assertEqual(len(history), 10)
        self.assertEqual(seen_topics, {"origin"})
        self.assertIn("Inform", seen_response_types)
        self.assertIn("Inquire", seen_response_types)
        self.assertGreaterEqual(len(seen_response_types), 2)
        print(f"completed turns: {len(history)}", flush=True)

    def test_policy_opinion_exchange_updates_memories_and_converges(self):
        """NPCs should exchange policy opinions, remember each other, and converge."""

        actor_a = self._build_actor("Citizen A")
        actor_b = self._build_actor("Citizen B")
        history = []

        actor_a_policy = actor_a.get_political_beliefs()
        actor_b_policy = actor_b.get_political_beliefs()
        self.assertIsNotNone(actor_a_policy)
        self.assertIsNotNone(actor_b_policy)
        assert actor_a_policy is not None
        assert actor_b_policy is not None

        actor_a_policy.update(
            {
                "Government": (1, 6),
                "Economy": (0, 6),
                "Culture": (0, 6),
                "Secularity": (0, 6),
            }
        )
        actor_b_policy.update(
            {
                "Government": (6, 6),
                "Economy": (6, 6),
                "Culture": (6, 6),
                "Secularity": (6, 6),
            }
        )

        topic_keys = ("Government", "Economy", "Culture", "Secularity")

        def opinion_value(policy, key):
            index, strength = policy[key]
            return (index - 3) * strength

        def opinion_gap(key):
            return abs(opinion_value(actor_a_policy, key) - opinion_value(actor_b_policy, key))

        def build_opinion_prompt(topic_key, subject, claim, speaker_name, listener_name):
            return self._build_prompt(
                "Inform",
                "share",
                domain="Policy",
                subject=subject,
                topic=topic_key,
                claim=claim,
                source=speaker_name,
                target=listener_name,
                evidence="Strong",
                polarity="Positive",
                qualifiers={
                    "Domain": "Policy",
                    "Polarity": "Positive",
                    "Force": "Medium",
                    "Honesty": "Truthful",
                    "Visibility": "Dyadic",
                    "Evidence": "Strong",
                    "Authority": "Peer",
                    "Time": "Present",
                },
            )

        before_diff = actor_a.policy_diff(actor_b_policy, warn=False)
        self.assertIsNotNone(before_diff)
        assert before_diff is not None
        before_total, before_summary = before_diff
        self.assertGreater(before_total, 0)
        for key in topic_keys:
            self.assertIn(key, before_summary)
            self.assertGreater(opinion_gap(key), 0)

        topic_cases = [
            (
                "Government",
                "political authority",
                "Government should be democratic and shared.",
                "Government should be centralized and strict.",
            ),
            (
                "Economy",
                "economic policy",
                "The economy should be cooperative and redistributive.",
                "The economy should stay free and competitive.",
            ),
            (
                "Culture",
                "social norms",
                "New customs should be welcomed into public life.",
                "Inherited norms should be protected from rapid change.",
            ),
            (
                "Secularity",
                "religious life",
                "Public institutions should stay secular.",
                "Public institutions should follow sacred law.",
            ),
        ]

        for index, (topic_key, subject, claim_a, claim_b) in enumerate(topic_cases, start=1):
            with self.subTest(topic=topic_key):
                a_prompt = build_opinion_prompt(
                    topic_key,
                    subject,
                    claim_a,
                    actor_a.get_reference(NAME),
                    actor_b.get_reference(NAME),
                )
                a_interaction = actor_a.handle_social_interaction(a_prompt, [actor_b], history)
                self.assertIsNotNone(a_interaction)
                assert a_interaction is not None

                self.assertEqual(a_interaction["prompt_event_type"], "Inform")
                self.assertEqual(a_interaction["prompt_event"]["topic"], topic_key)
                self.assertEqual(a_interaction["prompt_event"]["claim"], claim_a)
                self.assertEqual(a_interaction["response"]["content"]["topic"], topic_key)
                self.assertIn(a_interaction["response_type"], SOCIAL_INTERACTION_TYPES)
                self.assertEqual(len(history), (index * 2) - 1)
                self.assertTrue(
                    any(
                        party.get("name") == actor_b.get_reference(NAME)
                        for party in a_interaction["parties"]
                    )
                )

                b_prompt = build_opinion_prompt(
                    topic_key,
                    subject,
                    claim_b,
                    actor_b.get_reference(NAME),
                    actor_a.get_reference(NAME),
                )
                b_interaction = actor_b.handle_social_interaction(b_prompt, [actor_a], history)
                self.assertIsNotNone(b_interaction)
                assert b_interaction is not None

                self.assertEqual(b_interaction["prompt_event_type"], "Inform")
                self.assertEqual(b_interaction["prompt_event"]["topic"], topic_key)
                self.assertEqual(b_interaction["prompt_event"]["claim"], claim_b)
                self.assertEqual(b_interaction["response"]["content"]["topic"], topic_key)
                self.assertIn(b_interaction["response_type"], SOCIAL_INTERACTION_TYPES)
                self.assertEqual(len(history), index * 2)
                self.assertTrue(
                    any(
                        party.get("name") == actor_a.get_reference(NAME)
                        for party in b_interaction["parties"]
                    )
                )

                self.assertGreater(opinion_gap(topic_key), 0)

                blended_value = (
                    round((actor_a_policy[topic_key][0] + actor_b_policy[topic_key][0]) / 2),
                    round((actor_a_policy[topic_key][1] + actor_b_policy[topic_key][1]) / 2),
                )
                actor_a_policy[topic_key] = blended_value
                actor_b_policy[topic_key] = blended_value

                self.assertEqual(opinion_gap(topic_key), 0)

        left_memory = actor_a.Memory.get(SOCIAL, {})
        right_memory = actor_b.Memory.get(SOCIAL, {})
        self.assertEqual(len(left_memory), len(topic_cases))
        self.assertEqual(len(right_memory), len(topic_cases))

        for record in left_memory.values():
            self.assertTrue(
                any(party.get("name") == actor_b.get_reference(NAME) for party in record["parties"])
            )

        for record in right_memory.values():
            self.assertTrue(
                any(party.get("name") == actor_a.get_reference(NAME) for party in record["parties"])
            )

        after_diff = actor_a.policy_diff(actor_b_policy, warn=False)
        self.assertIsNotNone(after_diff)
        assert after_diff is not None
        after_total, after_summary = after_diff
        self.assertEqual(after_total, 0)
        for key in topic_keys:
            self.assertIn(key, after_summary)

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
