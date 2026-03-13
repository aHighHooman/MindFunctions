from __future__ import annotations

from cif_engine import Character, InfluenceRule, SocialExchange, TriggerRule


def relationship_is(*values: str):
    allowed = set(values)

    def check(state, history, situation, initiator, responder):
        return state.relationships[(initiator, responder)] in allowed

    return check


def relationship_not(*values: str):
    blocked = set(values)

    def check(state, history, situation, initiator, responder):
        return state.relationships[(initiator, responder)] not in blocked

    return check


def has_status(status: str, direction: str = "forward"):
    def check(state, history, situation, initiator, responder):
        if direction == "forward":
            return state.has_status(initiator, responder, status)
        if direction == "reverse":
            return state.has_status(responder, initiator, status)
        return state.has_status(initiator, responder, status) or state.has_status(responder, initiator, status)

    return check


def metric_at_least(metric: str, value: float, direction: str = "forward"):
    def check(state, history, situation, initiator, responder):
        if direction == "reverse":
            return state.link(responder, initiator)[metric] >= value
        return state.link(initiator, responder)[metric] >= value

    return check


def metric_at_most(metric: str, value: float, direction: str = "forward"):
    def check(state, history, situation, initiator, responder):
        if direction == "reverse":
            return state.link(responder, initiator)[metric] <= value
        return state.link(initiator, responder)[metric] <= value

    return check


def mood_at_least(metric: str, value: float, target: str = "initiator"):
    def check(state, history, situation, initiator, responder):
        name = initiator if target == "initiator" else responder
        return state.mood_for(name)[metric] >= value

    return check


def initiator_has_trait(trait: str):
    def check(state, history, situation, initiator, responder):
        return trait in next(character.traits for character in situation.characters if character.name == initiator)

    return check


def responder_has_trait(trait: str):
    def check(state, history, situation, initiator, responder):
        return trait in next(character.traits for character in situation.characters if character.name == responder)

    return check


def context_is(key: str, *values: str):
    allowed = set(values)

    def check(state, history, situation, initiator, responder):
        return situation.context.get(key) in allowed

    return check


def recent_count(history, *, exchange=None, outcome=None, pair=None, limit=4):
    count = 0
    for event in history[-limit:]:
        if exchange is not None and event["exchange"] != exchange:
            continue
        if outcome is not None and event["outcome"] != outcome:
            continue
        if pair is not None and {event["initiator"], event["responder"]} != set(pair):
            continue
        count += 1
    return count


def recent_exchange(exchange: str, outcome: str | None = None, limit: int = 4):
    def check(state, history, situation, initiator, responder):
        return recent_count(history, exchange=exchange, outcome=outcome, pair=(initiator, responder), limit=limit) > 0

    return check


def change_link(target: str, **deltas: float):
    def effect(state, history, situation, initiator, responder):
        if target == "forward":
            state.change_link(initiator, responder, **deltas)
        elif target == "reverse":
            state.change_link(responder, initiator, **deltas)
        else:
            state.change_link(initiator, responder, **deltas)
            state.change_link(responder, initiator, **deltas)

    return effect


def change_mood(target: str, **deltas: float):
    def effect(state, history, situation, initiator, responder):
        if target == "initiator":
            state.change_mood(initiator, **deltas)
        elif target == "responder":
            state.change_mood(responder, **deltas)
        else:
            state.change_mood(initiator, **deltas)
            state.change_mood(responder, **deltas)

    return effect


def add_status(status: str, direction: str = "forward"):
    def effect(state, history, situation, initiator, responder):
        if direction == "forward":
            state.add_status(initiator, responder, status)
        elif direction == "reverse":
            state.add_status(responder, initiator, status)
        else:
            state.add_status(initiator, responder, status)
            state.add_status(responder, initiator, status)

    return effect


def remove_status(status: str, direction: str = "forward"):
    def effect(state, history, situation, initiator, responder):
        if direction == "forward":
            state.remove_status(initiator, responder, status)
        elif direction == "reverse":
            state.remove_status(responder, initiator, status)
        else:
            state.remove_status(initiator, responder, status)
            state.remove_status(responder, initiator, status)

    return effect


def set_relationship(value: str, direction: str = "both"):
    def effect(state, history, situation, initiator, responder):
        if direction == "forward":
            state.set_relationship(initiator, responder, value)
        elif direction == "reverse":
            state.set_relationship(responder, initiator, value)
        else:
            state.set_relationship(initiator, responder, value)
            state.set_relationship(responder, initiator, value)

    return effect


def make_exchange_library() -> dict[str, SocialExchange]:
    return {
        "Converse": SocialExchange(
            name="Converse",
            intent="keep the interaction moving",
            preconditions=[],
            initiator_rules=[
                InfluenceRule("baseline", 2, lambda *args: True),
                InfluenceRule("friends_like_talking", 4, relationship_is("friend", "dating")),
                InfluenceRule("uncertain_but_trying", 2, relationship_is("stranger")),
                InfluenceRule("awkward_pushes_small_talk", 3, has_status("awkward", "either")),
                InfluenceRule("nervous_people_fill_space", 2, mood_at_least("wariness", 20)),
            ],
            responder_rules=[
                InfluenceRule("baseline", 1, lambda *args: True),
                InfluenceRule("friendly_response", 3, metric_at_least("like", 20, "reverse")),
                InfluenceRule("guarded_if_hostile", -5, relationship_is("enemy", "bad_acquaintance")),
            ],
            accept_effects=[
                change_link("both", like=2, trust=1),
                change_mood("both", joy=1, wariness=-1),
                remove_status("awkward", "either"),
            ],
            reject_effects=[
                change_link("forward", like=-1),
                change_mood("initiator", wariness=2),
            ],
            instantiations={
                "accept": [
                    "They settle into an easy back-and-forth.",
                    "The small talk lands well enough to keep things moving.",
                    "The conversation stays light but comfortable.",
                ],
                "reject": [
                    "The attempt at conversation dies quickly.",
                    "The opener hangs in the air without much response.",
                ],
            },
        ),
        "Compliment": SocialExchange(
            name="Compliment",
            intent="raise warmth through praise",
            preconditions=[relationship_not("enemy")],
            initiator_rules=[
                InfluenceRule("baseline", 1, lambda *args: True),
                InfluenceRule("likes_target", 4, metric_at_least("like", 15)),
                InfluenceRule("romantic_interest", 3, metric_at_least("attraction", 20)),
                InfluenceRule("supportive_trait", 2, initiator_has_trait("supportive")),
                InfluenceRule("awkward_repair", 3, has_status("awkward", "either")),
            ],
            responder_rules=[
                InfluenceRule("baseline", 1, lambda *args: True),
                InfluenceRule("already_likes_initiator", 3, metric_at_least("like", 10, "reverse")),
                InfluenceRule("suspicious_of_enemy", -6, relationship_is("enemy")),
                InfluenceRule("embarrassed_publicly", -3, context_is("tone", "public")),
            ],
            accept_effects=[
                change_link("forward", like=3, attraction=2),
                change_link("reverse", like=2),
                change_mood("responder", joy=4, wariness=-2),
            ],
            reject_effects=[
                change_link("forward", like=-1),
                change_mood("responder", wariness=3),
                add_status("awkward", "either"),
            ],
            instantiations={
                "accept": [
                    "The compliment lands and softens the mood.",
                    "The praise is received with a visible smile.",
                    "The kind words pull them a little closer.",
                ],
                "reject": [
                    "The compliment feels off and creates tension.",
                    "The praise is met with a skeptical look.",
                ],
            },
        ),
        "Joke": SocialExchange(
            name="Joke",
            intent="create shared amusement",
            preconditions=[relationship_not("enemy")],
            initiator_rules=[
                InfluenceRule("baseline", 1, lambda *args: True),
                InfluenceRule("friend_energy", 5, relationship_is("friend")),
                InfluenceRule("party_energy", 3, context_is("location", "party")),
                InfluenceRule("witty_trait", 3, initiator_has_trait("witty")),
                InfluenceRule("high_joy", 2, mood_at_least("joy", 20)),
            ],
            responder_rules=[
                InfluenceRule("baseline", 0, lambda *args: True),
                InfluenceRule("likes_initiator", 3, metric_at_least("like", 15, "reverse")),
                InfluenceRule("guarded", -3, mood_at_least("wariness", 35, "responder")),
                InfluenceRule("hostile_context", -4, relationship_is("bad_acquaintance", "enemy")),
            ],
            accept_effects=[
                change_link("both", like=2),
                change_mood("both", joy=4, wariness=-1),
            ],
            reject_effects=[
                change_link("forward", like=-1),
                change_mood("responder", wariness=2),
            ],
            instantiations={
                "accept": [
                    "The joke gets a genuine laugh.",
                    "They both crack a smile at the joke.",
                    "The joke lands and lightens the room.",
                ],
                "reject": [
                    "The joke falls flat.",
                    "The joke only makes things stiffer.",
                ],
            },
        ),
        "Flirt": SocialExchange(
            name="Flirt",
            intent="test romantic interest",
            preconditions=[relationship_not("enemy"), metric_at_least("attraction", 15)],
            initiator_rules=[
                InfluenceRule("baseline", -1, lambda *args: True),
                InfluenceRule("attraction", 6, metric_at_least("attraction", 30)),
                InfluenceRule("likes_target", 3, metric_at_least("like", 15)),
                InfluenceRule("party_boost", 2, context_is("location", "party")),
                InfluenceRule("romantic_tension", 4, has_status("romantic_tension", "either")),
            ],
            responder_rules=[
                InfluenceRule("baseline", -2, lambda *args: True),
                InfluenceRule("mutual_attraction", 6, metric_at_least("attraction", 25, "reverse")),
                InfluenceRule("mutual_like", 3, metric_at_least("like", 15, "reverse")),
                InfluenceRule("awkward", -5, has_status("awkward", "either")),
                InfluenceRule("guarded_trait", -3, responder_has_trait("guarded")),
            ],
            accept_effects=[
                change_link("both", like=2, attraction=4),
                change_mood("both", joy=3, wariness=-2),
            ],
            reject_effects=[
                change_link("forward", like=-2, attraction=-1),
                change_mood("initiator", wariness=4),
                change_mood("responder", wariness=2),
            ],
            instantiations={
                "accept": [
                    "The flirtation is returned instead of brushed off.",
                    "The moment turns playful and charged.",
                    "The flirt lands and the tension feels mutual.",
                ],
                "reject": [
                    "The flirt is politely but clearly shut down.",
                    "The romantic angle misses and leaves a pause behind.",
                ],
            },
        ),
        "Insult": SocialExchange(
            name="Insult",
            intent="wound or provoke",
            preconditions=[],
            initiator_rules=[
                InfluenceRule("baseline", -4, lambda *args: True),
                InfluenceRule("hostile_relationship", 8, relationship_is("bad_acquaintance", "enemy")),
                InfluenceRule("abrasive_trait", 4, initiator_has_trait("abrasive")),
                InfluenceRule("high_envy", 4, mood_at_least("envy", 20)),
                InfluenceRule("high_wariness", 2, mood_at_least("wariness", 25)),
            ],
            responder_rules=[
                InfluenceRule("baseline", -6, lambda *args: True),
                InfluenceRule("already_hostile", -3, relationship_is("bad_acquaintance", "enemy")),
            ],
            accept_effects=[
                change_link("both", like=-4, trust=-3),
                change_mood("responder", joy=-5, wariness=5, envy=2),
                change_mood("initiator", joy=1),
            ],
            reject_effects=[
                change_link("both", like=-3, trust=-2),
                change_mood("responder", wariness=4, envy=2),
            ],
            instantiations={
                "accept": [
                    "The insult lands hard and turns the exchange bitter.",
                    "The barb connects and the mood sours immediately.",
                ],
                "reject": [
                    "The insult is shrugged off, but it still does damage.",
                    "The jab is deflected without ending the hostility.",
                ],
            },
        ),
        "Apologize": SocialExchange(
            name="Apologize",
            intent="repair recent damage",
            preconditions=[has_status("awkward", "either")],
            initiator_rules=[
                InfluenceRule("baseline", 0, lambda *args: True),
                InfluenceRule("supportive_trait", 3, initiator_has_trait("supportive")),
                InfluenceRule("recent_insult", 4, recent_exchange("Insult")),
                InfluenceRule("recent_rejection", 3, recent_exchange("Flirt", "reject")),
            ],
            responder_rules=[
                InfluenceRule("baseline", -1, lambda *args: True),
                InfluenceRule("still_likes_them", 4, metric_at_least("like", 5, "reverse")),
                InfluenceRule("deeply_hurt", -4, mood_at_least("wariness", 40, "responder")),
            ],
            accept_effects=[
                change_link("both", trust=3, like=1),
                change_mood("both", wariness=-3),
                remove_status("awkward", "either"),
            ],
            reject_effects=[
                change_link("forward", trust=-1),
                change_mood("initiator", wariness=2),
            ],
            instantiations={
                "accept": [
                    "The apology is accepted and some tension leaves the room.",
                    "The apology lands as sincere enough to help.",
                ],
                "reject": [
                    "The apology is heard but not really accepted.",
                    "The attempt to smooth things over does not work.",
                ],
            },
        ),
        "Comfort": SocialExchange(
            name="Comfort",
            intent="soothe someone who is upset",
            preconditions=[mood_at_least("wariness", 15, "responder")],
            initiator_rules=[
                InfluenceRule("baseline", 0, lambda *args: True),
                InfluenceRule("supportive_trait", 5, initiator_has_trait("supportive")),
                InfluenceRule("friend_or_family", 4, relationship_is("friend", "family", "dating")),
                InfluenceRule("responder_is_upset", 4, mood_at_least("wariness", 25, "responder")),
            ],
            responder_rules=[
                InfluenceRule("baseline", 1, lambda *args: True),
                InfluenceRule("trusts_initiator", 4, metric_at_least("trust", 15, "reverse")),
                InfluenceRule("hostile_relationship", -6, relationship_is("bad_acquaintance", "enemy")),
            ],
            accept_effects=[
                change_link("both", trust=3, like=2),
                change_mood("responder", joy=4, wariness=-6),
                add_status("comfortable_with", "either"),
            ],
            reject_effects=[
                change_link("forward", trust=-1),
                change_mood("responder", wariness=2),
            ],
            instantiations={
                "accept": [
                    "The comfort is accepted and the tension visibly eases.",
                    "The reassurance lands and steadies them.",
                ],
                "reject": [
                    "The comfort attempt is brushed away.",
                    "They are not ready to be comforted.",
                ],
            },
        ),
        "AskOut": SocialExchange(
            name="AskOut",
            intent="push toward an explicit romantic step",
            preconditions=[metric_at_least("attraction", 35), metric_at_least("like", 20)],
            initiator_rules=[
                InfluenceRule("baseline", -4, lambda *args: True),
                InfluenceRule("romantic_tension", 6, has_status("romantic_tension", "either")),
                InfluenceRule("mutual_warmth", 4, metric_at_least("trust", 15)),
                InfluenceRule("party_or_date_energy", 2, context_is("location", "party", "date")),
            ],
            responder_rules=[
                InfluenceRule("baseline", -4, lambda *args: True),
                InfluenceRule("mutual_attraction", 6, metric_at_least("attraction", 30, "reverse")),
                InfluenceRule("mutual_trust", 3, metric_at_least("trust", 15, "reverse")),
                InfluenceRule("awkward", -5, has_status("awkward", "either")),
            ],
            accept_effects=[
                change_link("both", like=3, trust=3, attraction=3),
                change_mood("both", joy=5, wariness=-3),
                set_relationship("dating"),
                add_status("romantic_tension", "either"),
            ],
            reject_effects=[
                change_link("forward", trust=-2, attraction=-2),
                change_mood("initiator", joy=-3, wariness=6),
                add_status("awkward", "either"),
            ],
            instantiations={
                "accept": [
                    "The invitation is accepted and the tone shifts into something more explicit.",
                    "The ask lands, and now there is a clear romantic direction.",
                ],
                "reject": [
                    "The invitation is declined and things turn awkward fast.",
                    "The ask is turned down, leaving the moment hanging.",
                ],
            },
        ),
        "RejectAdvance": SocialExchange(
            name="RejectAdvance",
            intent="set a clear boundary",
            preconditions=[has_status("romantic_tension", "either")],
            initiator_rules=[
                InfluenceRule("baseline", -2, lambda *args: True),
                InfluenceRule("guarded_trait", 4, initiator_has_trait("guarded")),
                InfluenceRule("awkward_after_rejection", 4, has_status("awkward", "either")),
                InfluenceRule("low_reverse_like", 3, metric_at_most("like", 5, "reverse")),
            ],
            responder_rules=[
                InfluenceRule("baseline", 0, lambda *args: True),
                InfluenceRule("accept_boundary", 2, metric_at_least("trust", 5, "reverse")),
                InfluenceRule("hurt_by_boundary", -2, metric_at_least("attraction", 30, "reverse")),
            ],
            accept_effects=[
                change_link("forward", trust=1),
                change_link("reverse", attraction=-4, like=-1),
                add_status("awkward", "either"),
                remove_status("romantic_tension", "either"),
            ],
            reject_effects=[
                change_link("both", trust=-2, like=-1),
                change_mood("both", wariness=3),
                add_status("awkward", "either"),
            ],
            instantiations={
                "accept": [
                    "The boundary is accepted, though the air stays tense.",
                    "The rejection is handled cleanly, but it still stings.",
                ],
                "reject": [
                    "The attempt to draw a boundary sparks more friction.",
                    "The rejection turns into an argument instead of closure.",
                ],
            },
        ),
    }


def flirt_trigger_condition(state, history, situation):
    if len(history) < 2:
        return False
    last_two = history[-2:]
    pair = {last_two[0]["initiator"], last_two[0]["responder"]}
    return (
        all(event["exchange"] == "Flirt" and event["outcome"] == "accept" for event in last_two)
        and {last_two[1]["initiator"], last_two[1]["responder"]} == pair
        and not state.has_status(last_two[0]["initiator"], last_two[0]["responder"], "romantic_tension")
    )


def flirt_trigger_effect(state, history, situation):
    last = history[-1]
    initiator = last["initiator"]
    responder = last["responder"]
    state.add_status(initiator, responder, "romantic_tension")
    state.add_status(responder, initiator, "romantic_tension")
    return [f"{initiator} and {responder} now have romantic_tension"]


def rejection_trigger_condition(state, history, situation):
    if len(history) < 2:
        return False
    recent = history[-2:]
    if not all(event["outcome"] == "reject" for event in recent):
        return False
    if not all(event["exchange"] in {"Flirt", "AskOut", "RejectAdvance"} for event in recent):
        return False
    pair = {recent[0]["initiator"], recent[0]["responder"]}
    return {recent[1]["initiator"], recent[1]["responder"]} == pair


def rejection_trigger_effect(state, history, situation):
    last = history[-1]
    initiator = last["initiator"]
    responder = last["responder"]
    state.add_status(initiator, responder, "awkward")
    state.add_status(responder, initiator, "awkward")
    return [f"{initiator} and {responder} now have awkward status"]


def hostility_trigger_condition(state, history, situation):
    last = history[-1]
    return (
        recent_count(history, exchange="Insult", pair=(last["initiator"], last["responder"]), limit=3) >= 2
        and state.relationships[(last["initiator"], last["responder"])] != "enemy"
    )


def hostility_trigger_effect(state, history, situation):
    last = history[-1]
    initiator = last["initiator"]
    responder = last["responder"]
    current = state.relationships[(initiator, responder)]
    next_value = "enemy" if current == "bad_acquaintance" else "bad_acquaintance"
    state.set_relationship(initiator, responder, next_value)
    state.set_relationship(responder, initiator, next_value)
    return [f"{initiator} and {responder} relationship shifts to {next_value}"]


def comfort_trigger_condition(state, history, situation):
    if not history:
        return False
    last = history[-1]
    return (
        last["exchange"] == "Comfort"
        and last["outcome"] == "accept"
        and recent_count(history, exchange="Comfort", outcome="accept", pair=(last["initiator"], last["responder"]), limit=5) >= 2
    )


def comfort_trigger_effect(state, history, situation):
    last = history[-1]
    initiator = last["initiator"]
    responder = last["responder"]
    state.add_status(initiator, responder, "comfortable_with")
    state.add_status(responder, initiator, "comfortable_with")
    state.change_link(initiator, responder, trust=2)
    state.change_link(responder, initiator, trust=2)
    return [f"{initiator} and {responder} become more comfortable with each other"]


def jealousy_trigger_condition(state, history, situation):
    if not history or history[-1]["outcome"] != "accept" or history[-1]["exchange"] not in {"Flirt", "AskOut"}:
        return False

    last = history[-1]
    for character in situation.characters:
        if character.name in {last["initiator"], last["responder"]}:
            continue
        if "jealous" not in character.traits:
            continue
        if state.link(character.name, last["responder"])["attraction"] >= 25:
            return True
    return False


def jealousy_trigger_effect(state, history, situation):
    last = history[-1]
    notes = []
    for character in situation.characters:
        if character.name in {last["initiator"], last["responder"]}:
            continue
        if "jealous" not in character.traits:
            continue
        if state.link(character.name, last["responder"])["attraction"] < 25:
            continue
        state.change_mood(character.name, envy=5, wariness=2)
        state.add_status(character.name, last["initiator"], "jealous")
        notes.append(f"{character.name} grows jealous watching {last['initiator']} and {last['responder']}")
    return notes


def make_trigger_rules() -> list[TriggerRule]:
    return [
        TriggerRule("romantic_tension", flirt_trigger_condition, flirt_trigger_effect),
        TriggerRule("awkward_after_rejection", rejection_trigger_condition, rejection_trigger_effect),
        TriggerRule("hostility_spiral", hostility_trigger_condition, hostility_trigger_effect),
        TriggerRule("comfort_pattern", comfort_trigger_condition, comfort_trigger_effect),
        TriggerRule("jealous_observer", jealousy_trigger_condition, jealousy_trigger_effect),
    ]


def character(name: str, *traits: str, **mood: float) -> Character:
    return Character(name=name, traits=set(traits), mood={key: float(value) for key, value in mood.items()})
