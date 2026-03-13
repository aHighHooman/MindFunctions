from __future__ import annotations

import argparse
import random
from collections import Counter
from dataclasses import dataclass, field


UTILITY_KEYS = ("food", "energy", "fun")
UTILITY_WEIGHTS = {"food": 1.35, "energy": 1.15, "fun": 1.0}
DEFAULT_DECAY = {"food": 6.0, "energy": 4.5, "fun": 3.0}
CRITICAL_THRESHOLD = 25.0
UNLOCK_THRESHOLD = 45.0
UNLOCK_BONUS_SCALE = 4.0


@dataclass
class Action:
    name: str
    effects: dict[str, float]
    noise: dict[str, tuple[float, float]] = field(default_factory=dict)


@dataclass
class Agent:
    food: float = 68.0
    energy: float = 62.0
    fun: float = 55.0
    money: float = 24.0


ACTIONS = [
    Action("eat", {"food": 34.0, "money": -12.0}, {"food": (-4.0, 4.0)}),
    Action("sleep", {"energy": 36.0, "fun": -7.0}, {"energy": (-3.0, 3.0)}),
    Action("play", {"fun": 28.0, "energy": -10.0, "money": -4.0}, {"fun": (-5.0, 5.0)}),
    Action("work", {"money": 18.0, "energy": -16.0, "fun": -8.0, "food": -5.0}, {"money": (-3.0, 3.0)}),
    Action("idle", {"energy": 4.0, "fun": 2.0, "food": -2.0}),
]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def score_action(agent: Agent, action: Action, decay: dict[str, float]) -> tuple[float, dict[str, float]]:
    if agent.money + action.effects.get("money", 0.0) < 0:
        return float("-inf"), {}

    predicted = {}
    for key in UTILITY_KEYS:
        current = getattr(agent, key)
        predicted[key] = clamp(current - decay[key] + action.effects.get(key, 0.0), 0.0, 100.0)

    predicted["money"] = max(0.0, agent.money + action.effects.get("money", 0.0))

    pressure = 0.0
    for key in UTILITY_KEYS:
        deficit = 100.0 - predicted[key]
        pressure += UTILITY_WEIGHTS[key] * deficit * deficit

    money_delta = action.effects.get("money", 0.0)
    unlock_bonus = 0.0
    # Money is not a need by itself, but it matters when it unlocks restorative actions for a low utility.
    for future_action in ACTIONS:
        future_cost = max(0.0, -future_action.effects.get("money", 0.0))
        if future_cost == 0 or agent.money >= future_cost or predicted["money"] < future_cost:
            continue

        improvement = 0.0
        for key in UTILITY_KEYS:
            gain = future_action.effects.get(key, 0.0)
            if predicted[key] < UNLOCK_THRESHOLD and gain > 0:
                improvement += (UNLOCK_THRESHOLD - predicted[key]) * gain * UTILITY_WEIGHTS[key]
        unlock_bonus = max(unlock_bonus, improvement)

    score = -pressure + 0.25 * money_delta + UNLOCK_BONUS_SCALE * unlock_bonus
    return score, predicted


def apply_step(agent: Agent, action: Action, decay: dict[str, float], rng: random.Random) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    before = {key: getattr(agent, key) for key in (*UTILITY_KEYS, "money")}
    realized = {}

    for key in UTILITY_KEYS:
        low, high = action.noise.get(key, (0.0, 0.0))
        realized[key] = action.effects.get(key, 0.0) + rng.uniform(low, high)
        updated = getattr(agent, key) - decay[key] + realized[key]
        setattr(agent, key, clamp(updated, 0.0, 100.0))

    money_noise = action.noise.get("money")
    money_delta = action.effects.get("money", 0.0)
    if money_noise is not None:
        money_delta += rng.uniform(*money_noise)
    agent.money = max(0.0, agent.money + money_delta)
    realized["money"] = money_delta

    after = {key: getattr(agent, key) for key in (*UTILITY_KEYS, "money")}
    return before, after, realized


def run_simulation(steps: int, seed: int, verbose: bool) -> None:
    rng = random.Random(seed)
    agent = Agent()
    action_counts = Counter()
    totals = Counter()
    critical_counts = Counter()

    if verbose:
        print(
            f"seed={seed} start "
            f"food={agent.food:.1f} energy={agent.energy:.1f} fun={agent.fun:.1f} money={agent.money:.1f}"
        )

    for step in range(1, steps + 1):
        scored_actions = []
        for action in ACTIONS:
            score, predicted = score_action(agent, action, DEFAULT_DECAY)
            scored_actions.append((score, action, predicted))

        best_score, chosen_action, predicted = max(scored_actions, key=lambda item: item[0])
        before, after, realized = apply_step(agent, chosen_action, DEFAULT_DECAY, rng)
        action_counts[chosen_action.name] += 1

        for key in UTILITY_KEYS:
            totals[key] += after[key]
            if after[key] < CRITICAL_THRESHOLD:
                critical_counts[key] += 1

        if verbose:
            score_text = " ".join(
                f"{action.name}={score:.1f}"
                for score, action, _ in sorted(scored_actions, key=lambda item: item[0], reverse=True)
            )
            print(
                f"step={step:02d} choose={chosen_action.name} score={best_score:.1f} "
                f"pred(food={predicted['food']:.1f}, energy={predicted['energy']:.1f}, fun={predicted['fun']:.1f}, money={predicted['money']:.1f})"
            )
            print(
                f"    before(food={before['food']:.1f}, energy={before['energy']:.1f}, fun={before['fun']:.1f}, money={before['money']:.1f}) "
                f"delta(food={realized['food']:+.1f}, energy={realized['energy']:+.1f}, fun={realized['fun']:+.1f}, money={realized['money']:+.1f}) "
                f"after(food={after['food']:.1f}, energy={after['energy']:.1f}, fun={after['fun']:.1f}, money={after['money']:.1f})"
            )
            print(f"    scores {score_text}")

    average_levels = {key: totals[key] / steps for key in UTILITY_KEYS}

    print("\nPURE UTILITY EXPERIMENT")
    print(f"Seed: {seed}")
    print(f"Steps: {steps}")
    print(
        "Final state: "
        f"food={agent.food:.1f}, energy={agent.energy:.1f}, fun={agent.fun:.1f}, money={agent.money:.1f}"
    )
    print(
        "Average utilities: "
        f"food={average_levels['food']:.1f}, energy={average_levels['energy']:.1f}, fun={average_levels['fun']:.1f}"
    )
    print(
        "Critical counts (<25): "
        f"food={critical_counts['food']}, energy={critical_counts['energy']}, fun={critical_counts['fun']}"
    )
    print("Action counts:")
    for action in ACTIONS:
        print(f"  {action.name}: {action_counts[action.name]}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Pure utility-based decision experiment.")
    parser.add_argument("--steps", type=int, default=30, help="Number of simulation steps.")
    parser.add_argument("--seed", type=int, default=7, help="Seed for reproducible randomness.")
    parser.add_argument("--verbose", action="store_true", help="Print per-step scoring and state updates.")
    args = parser.parse_args()

    run_simulation(steps=args.steps, seed=args.seed, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
