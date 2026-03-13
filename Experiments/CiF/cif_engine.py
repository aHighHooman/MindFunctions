from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable


MetricMap = dict[str, float]
PairKey = tuple[str, str]
Condition = Callable[["SocialState", list[dict], "Situation", str, str], bool]
Effect = Callable[["SocialState", list[dict], "Situation", str, str], None]
TriggerCondition = Callable[["SocialState", list[dict], "Situation"], bool]
TriggerEffect = Callable[["SocialState", list[dict], "Situation"], list[str]]


@dataclass(frozen=True)
class Character:
    name: str
    traits: set[str] = field(default_factory=set)
    mood: MetricMap = field(default_factory=dict)


@dataclass(frozen=True)
class InfluenceRule:
    name: str
    weight: float
    condition: Condition


@dataclass(frozen=True)
class TriggerRule:
    name: str
    condition: TriggerCondition
    effect: TriggerEffect


@dataclass(frozen=True)
class SocialExchange:
    name: str
    intent: str
    preconditions: list[Condition]
    initiator_rules: list[InfluenceRule]
    responder_rules: list[InfluenceRule]
    accept_effects: list[Effect]
    reject_effects: list[Effect]
    instantiations: dict[str, list[str]]


@dataclass(frozen=True)
class Situation:
    id: str
    description: str
    characters: list[Character]
    initial_relationships: dict[PairKey, str]
    initial_numeric_state: dict[PairKey, MetricMap]
    initial_statuses: dict[PairKey, set[str]]
    context: dict[str, str]
    enabled_exchanges: list[SocialExchange]
    turn_limit: int
    seed: int
    trigger_rules: list[TriggerRule]


@dataclass
class SocialState:
    relationships: dict[PairKey, str]
    numeric: dict[PairKey, MetricMap]
    statuses: dict[PairKey, set[str]]
    moods: dict[str, MetricMap]

    def link(self, initiator: str, responder: str) -> MetricMap:
        return self.numeric[(initiator, responder)]

    def mood_for(self, character: str) -> MetricMap:
        return self.moods[character]

    def has_status(self, initiator: str, responder: str, status: str) -> bool:
        return status in self.statuses[(initiator, responder)]

    def add_status(self, initiator: str, responder: str, status: str) -> bool:
        before = len(self.statuses[(initiator, responder)])
        self.statuses[(initiator, responder)].add(status)
        return len(self.statuses[(initiator, responder)]) != before

    def remove_status(self, initiator: str, responder: str, status: str) -> bool:
        if status not in self.statuses[(initiator, responder)]:
            return False
        self.statuses[(initiator, responder)].remove(status)
        return True

    def set_relationship(self, initiator: str, responder: str, relationship: str) -> bool:
        key = (initiator, responder)
        if self.relationships[key] == relationship:
            return False
        self.relationships[key] = relationship
        return True

    def change_link(self, initiator: str, responder: str, **deltas: float) -> None:
        link = self.numeric[(initiator, responder)]
        for metric, delta in deltas.items():
            link[metric] = clamp(link[metric] + delta)

    def change_mood(self, character: str, **deltas: float) -> None:
        mood = self.moods[character]
        for metric, delta in deltas.items():
            mood[metric] = clamp(mood[metric] + delta)


@dataclass
class SimulationResult:
    situation_id: str
    transcript: list[dict]
    final_state: SocialState
    history: list[dict]
    exchange_counts: dict[str, int]


def clamp(value: float, low: float = -100.0, high: float = 100.0) -> float:
    return max(low, min(high, round(value, 1)))


def build_initial_state(situation: Situation) -> SocialState:
    names = [character.name for character in situation.characters]
    relationships: dict[PairKey, str] = {}
    numeric: dict[PairKey, MetricMap] = {}
    statuses: dict[PairKey, set[str]] = {}
    moods: dict[str, MetricMap] = {}

    for character in situation.characters:
        moods[character.name] = {"joy": 0.0, "wariness": 0.0, "envy": 0.0}
        moods[character.name].update({key: float(value) for key, value in character.mood.items()})

    for initiator in names:
        for responder in names:
            if initiator == responder:
                continue
            key = (initiator, responder)
            relationships[key] = "stranger"
            numeric[key] = {"like": 0.0, "trust": 0.0, "attraction": 0.0}
            statuses[key] = set()

    for key, relationship in situation.initial_relationships.items():
        relationships[key] = relationship

    for key, metrics in situation.initial_numeric_state.items():
        numeric[key].update({metric: float(value) for metric, value in metrics.items()})

    for key, values in situation.initial_statuses.items():
        statuses[key].update(values)

    return SocialState(relationships=relationships, numeric=numeric, statuses=statuses, moods=moods)


def score_rules(
    rules: list[InfluenceRule],
    state: SocialState,
    history: list[dict],
    situation: Situation,
    initiator: str,
    responder: str,
) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    for rule in rules:
        if rule.condition(state, history, situation, initiator, responder):
            score += rule.weight
            reasons.append(rule.name)
    return score, reasons


def score_exchange(
    exchange: SocialExchange,
    state: SocialState,
    history: list[dict],
    situation: Situation,
    initiator: str,
    responder: str,
) -> dict | None:
    for condition in exchange.preconditions:
        if not condition(state, history, situation, initiator, responder):
            return None

    volition, reasons = score_rules(exchange.initiator_rules, state, history, situation, initiator, responder)
    acceptance, acceptance_reasons = score_rules(
        exchange.responder_rules,
        state,
        history,
        situation,
        initiator,
        responder,
    )
    return {
        "exchange": exchange,
        "initiator": initiator,
        "responder": responder,
        "volition": volition,
        "volition_reasons": reasons,
        "acceptance": acceptance,
        "acceptance_reasons": acceptance_reasons,
    }


def choose_turn(state: SocialState, history: list[dict], situation: Situation, turn_index: int, rng: random.Random) -> dict:
    names = [character.name for character in situation.characters]
    initiator = names[turn_index % len(names)]
    candidates: list[dict] = []

    for responder in names:
        if responder == initiator:
            continue
        for exchange in situation.enabled_exchanges:
            scored = score_exchange(exchange, state, history, situation, initiator, responder)
            if scored is not None:
                candidates.append(scored)

    if not candidates:
        raise ValueError(f"No eligible exchanges for {initiator} in {situation.id}")

    highest = max(candidate["volition"] for candidate in candidates)
    tied = [candidate for candidate in candidates if candidate["volition"] == highest]
    return rng.choice(tied)


def snapshot(state: SocialState, initiator: str, responder: str) -> dict:
    return {
        "initiator_link": dict(state.link(initiator, responder)),
        "responder_link": dict(state.link(responder, initiator)),
        initiator: dict(state.mood_for(initiator)),
        responder: dict(state.mood_for(responder)),
        "initiator_statuses": sorted(state.statuses[(initiator, responder)]),
        "responder_statuses": sorted(state.statuses[(responder, initiator)]),
        "initiator_relationship": state.relationships[(initiator, responder)],
        "responder_relationship": state.relationships[(responder, initiator)],
    }


def describe_changes(before: dict, after: dict, initiator: str, responder: str) -> list[str]:
    changes: list[str] = []

    for metric, value in after["initiator_link"].items():
        delta = round(value - before["initiator_link"][metric], 1)
        if delta:
            changes.append(f"{initiator}->{responder} {metric} {delta:+}")

    for metric, value in after["responder_link"].items():
        delta = round(value - before["responder_link"][metric], 1)
        if delta:
            changes.append(f"{responder}->{initiator} {metric} {delta:+}")

    for character in (initiator, responder):
        for metric, value in after[character].items():
            delta = round(value - before[character][metric], 1)
            if delta:
                changes.append(f"{character} {metric} {delta:+}")

    if before["initiator_relationship"] != after["initiator_relationship"]:
        changes.append(
            f"{initiator}->{responder} relationship {before['initiator_relationship']} -> {after['initiator_relationship']}"
        )

    if before["responder_relationship"] != after["responder_relationship"]:
        changes.append(
            f"{responder}->{initiator} relationship {before['responder_relationship']} -> {after['responder_relationship']}"
        )

    added_initiator = sorted(set(after["initiator_statuses"]) - set(before["initiator_statuses"]))
    added_responder = sorted(set(after["responder_statuses"]) - set(before["responder_statuses"]))
    removed_initiator = sorted(set(before["initiator_statuses"]) - set(after["initiator_statuses"]))
    removed_responder = sorted(set(before["responder_statuses"]) - set(after["responder_statuses"]))

    for status in added_initiator:
        changes.append(f"{initiator}->{responder} gained status {status}")
    for status in added_responder:
        changes.append(f"{responder}->{initiator} gained status {status}")
    for status in removed_initiator:
        changes.append(f"{initiator}->{responder} lost status {status}")
    for status in removed_responder:
        changes.append(f"{responder}->{initiator} lost status {status}")

    return changes


def run_situation(situation: Situation) -> SimulationResult:
    rng = random.Random(situation.seed)
    state = build_initial_state(situation)
    history: list[dict] = []
    transcript: list[dict] = []
    exchange_counts = {exchange.name: 0 for exchange in situation.enabled_exchanges}

    for turn_index in range(situation.turn_limit):
        chosen = choose_turn(state, history, situation, turn_index, rng)
        exchange = chosen["exchange"]
        initiator = chosen["initiator"]
        responder = chosen["responder"]
        outcome = "accept" if chosen["acceptance"] >= 0 else "reject"
        before = snapshot(state, initiator, responder)

        effects = exchange.accept_effects if outcome == "accept" else exchange.reject_effects
        for effect in effects:
            effect(state, history, situation, initiator, responder)

        line = rng.choice(exchange.instantiations[outcome])
        event = {
            "turn": turn_index + 1,
            "initiator": initiator,
            "responder": responder,
            "exchange": exchange.name,
            "intent": exchange.intent,
            "outcome": outcome,
            "line": line,
            "volition": chosen["volition"],
            "acceptance": chosen["acceptance"],
            "volition_reasons": chosen["volition_reasons"],
            "acceptance_reasons": chosen["acceptance_reasons"],
            "trigger_notes": [],
        }
        history.append(event)
        exchange_counts[exchange.name] += 1

        for trigger in situation.trigger_rules:
            if trigger.condition(state, history, situation):
                event["trigger_notes"].extend(trigger.effect(state, history, situation))

        after = snapshot(state, initiator, responder)
        transcript.append({**event, "changes": describe_changes(before, after, initiator, responder)})

    return SimulationResult(
        situation_id=situation.id,
        transcript=transcript,
        final_state=state,
        history=history,
        exchange_counts={name: count for name, count in exchange_counts.items() if count},
    )


def summarize_pair(state: SocialState, initiator: str, responder: str) -> str:
    link = state.link(initiator, responder)
    statuses = ", ".join(sorted(state.statuses[(initiator, responder)])) or "none"
    relationship = state.relationships[(initiator, responder)]
    return (
        f"{initiator}->{responder}: relationship={relationship}, "
        f"like={link['like']}, trust={link['trust']}, attraction={link['attraction']}, statuses={statuses}"
    )


def summarize_mood(state: SocialState, character: str) -> str:
    mood = state.mood_for(character)
    return f"{character}: joy={mood['joy']}, wariness={mood['wariness']}, envy={mood['envy']}"
