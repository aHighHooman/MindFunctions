from __future__ import annotations

from cif_content import character, make_exchange_library, make_trigger_rules
from cif_engine import Situation


EXCHANGE_LIBRARY = make_exchange_library()
TRIGGER_RULES = make_trigger_rules()


def exchanges(*names: str):
    return [EXCHANGE_LIBRARY[name] for name in names]


SITUATIONS: dict[str, Situation] = {
    "awkward_first_meeting": Situation(
        id="awkward_first_meeting",
        description="Two strangers try to get through an uncertain first meeting at a cafe.",
        characters=[
            character("Avery", "guarded", wariness=15),
            character("Jordan", "witty", joy=5),
        ],
        initial_relationships={
            ("Avery", "Jordan"): "stranger",
            ("Jordan", "Avery"): "stranger",
        },
        initial_numeric_state={
            ("Avery", "Jordan"): {"like": 2, "trust": 0, "attraction": 8},
            ("Jordan", "Avery"): {"like": 4, "trust": 0, "attraction": 12},
        },
        initial_statuses={},
        context={"location": "cafe", "tone": "casual"},
        enabled_exchanges=exchanges("Converse", "Compliment", "Joke", "Flirt", "Apologize"),
        turn_limit=8,
        seed=11,
        trigger_rules=TRIGGER_RULES,
    ),
    "friendly_hangout": Situation(
        id="friendly_hangout",
        description="Two friends relax together and naturally drift toward jokes and support.",
        characters=[
            character("Maya", "supportive", joy=20),
            character("Rin", "witty", joy=18),
        ],
        initial_relationships={
            ("Maya", "Rin"): "friend",
            ("Rin", "Maya"): "friend",
        },
        initial_numeric_state={
            ("Maya", "Rin"): {"like": 35, "trust": 28, "attraction": 12},
            ("Rin", "Maya"): {"like": 38, "trust": 30, "attraction": 10},
        },
        initial_statuses={},
        context={"location": "park", "tone": "casual"},
        enabled_exchanges=exchanges("Converse", "Compliment", "Joke", "Comfort"),
        turn_limit=8,
        seed=22,
        trigger_rules=TRIGGER_RULES,
    ),
    "tense_reunion": Situation(
        id="tense_reunion",
        description="A strained reunion can either spiral into insults or inch toward repair.",
        characters=[
            character("Nadia", "abrasive", wariness=24, envy=14),
            character("Theo", "guarded", wariness=22),
        ],
        initial_relationships={
            ("Nadia", "Theo"): "bad_acquaintance",
            ("Theo", "Nadia"): "bad_acquaintance",
        },
        initial_numeric_state={
            ("Nadia", "Theo"): {"like": -18, "trust": -12, "attraction": 0},
            ("Theo", "Nadia"): {"like": -10, "trust": -14, "attraction": 0},
        },
        initial_statuses={
            ("Nadia", "Theo"): {"awkward"},
            ("Theo", "Nadia"): {"awkward"},
        },
        context={"location": "station", "tone": "tense"},
        enabled_exchanges=exchanges("Converse", "Insult", "Apologize", "Comfort"),
        turn_limit=8,
        seed=33,
        trigger_rules=TRIGGER_RULES,
    ),
    "crush_at_a_party": Situation(
        id="crush_at_a_party",
        description="A party brings asymmetrical attraction and enough energy for risky romantic moves.",
        characters=[
            character("Lena", "romantic", joy=16),
            character("Kai", "guarded", joy=8),
        ],
        initial_relationships={
            ("Lena", "Kai"): "stranger",
            ("Kai", "Lena"): "stranger",
        },
        initial_numeric_state={
            ("Lena", "Kai"): {"like": 18, "trust": 6, "attraction": 42},
            ("Kai", "Lena"): {"like": 12, "trust": 4, "attraction": 24},
        },
        initial_statuses={},
        context={"location": "party", "tone": "public"},
        enabled_exchanges=exchanges("Converse", "Compliment", "Joke", "Flirt", "AskOut", "RejectAdvance", "Apologize"),
        turn_limit=10,
        seed=44,
        trigger_rules=TRIGGER_RULES,
    ),
    "comfort_after_failure": Situation(
        id="comfort_after_failure",
        description="One person is struggling after a bad day while a supportive friend tries to help.",
        characters=[
            character("Sana", "supportive", joy=6),
            character("Eli", "guarded", wariness=34, joy=-12),
        ],
        initial_relationships={
            ("Sana", "Eli"): "friend",
            ("Eli", "Sana"): "friend",
        },
        initial_numeric_state={
            ("Sana", "Eli"): {"like": 26, "trust": 24, "attraction": 4},
            ("Eli", "Sana"): {"like": 20, "trust": 18, "attraction": 2},
        },
        initial_statuses={},
        context={"location": "home", "tone": "private"},
        enabled_exchanges=exchanges("Converse", "Comfort", "Compliment", "Apologize"),
        turn_limit=8,
        seed=55,
        trigger_rules=TRIGGER_RULES,
    ),
    "public_embarrassment": Situation(
        id="public_embarrassment",
        description="An awkward public stumble makes repair and rejection dynamics visible in the same scene.",
        characters=[
            character("Iris", "romantic", wariness=10),
            character("Noah", "guarded", wariness=18),
        ],
        initial_relationships={
            ("Iris", "Noah"): "stranger",
            ("Noah", "Iris"): "stranger",
        },
        initial_numeric_state={
            ("Iris", "Noah"): {"like": 16, "trust": 4, "attraction": 38},
            ("Noah", "Iris"): {"like": 8, "trust": 2, "attraction": 14},
        },
        initial_statuses={
            ("Iris", "Noah"): {"awkward"},
            ("Noah", "Iris"): {"awkward"},
        },
        context={"location": "event", "tone": "public"},
        enabled_exchanges=exchanges("Converse", "Compliment", "Flirt", "AskOut", "RejectAdvance", "Apologize"),
        turn_limit=10,
        seed=66,
        trigger_rules=TRIGGER_RULES,
    ),
    "jealous_triangle": Situation(
        id="jealous_triangle",
        description="A three-person party scene where visible chemistry can spill into jealousy.",
        characters=[
            character("Piper", "romantic", joy=14),
            character("Rowan", joy=12),
            character("Quinn", "jealous", "guarded", wariness=12),
        ],
        initial_relationships={
            ("Piper", "Rowan"): "friend",
            ("Rowan", "Piper"): "friend",
            ("Piper", "Quinn"): "friend",
            ("Quinn", "Piper"): "friend",
            ("Rowan", "Quinn"): "friend",
            ("Quinn", "Rowan"): "friend",
        },
        initial_numeric_state={
            ("Piper", "Rowan"): {"like": 28, "trust": 18, "attraction": 44},
            ("Rowan", "Piper"): {"like": 22, "trust": 16, "attraction": 30},
            ("Quinn", "Rowan"): {"like": 20, "trust": 12, "attraction": 34},
            ("Rowan", "Quinn"): {"like": 18, "trust": 12, "attraction": 8},
            ("Piper", "Quinn"): {"like": 16, "trust": 10, "attraction": 6},
            ("Quinn", "Piper"): {"like": 14, "trust": 10, "attraction": 4},
        },
        initial_statuses={},
        context={"location": "party", "tone": "public"},
        enabled_exchanges=exchanges("Converse", "Compliment", "Joke", "Flirt", "AskOut", "RejectAdvance", "Insult"),
        turn_limit=12,
        seed=77,
        trigger_rules=TRIGGER_RULES,
    ),
}
