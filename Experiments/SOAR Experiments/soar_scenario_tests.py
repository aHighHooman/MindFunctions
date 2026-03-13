import argparse
import importlib.util
import random
import sys
import unittest
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


def load_soar_module():
    module_path = Path(__file__).with_name("MakingCoffeeWithSoar.py")
    spec = importlib.util.spec_from_file_location("making_coffee_soar", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None, f"Unable to load SOAR module from {module_path}"
    spec.loader.exec_module(module)
    return module


SOAR = load_soar_module()


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    group: str
    seed: int
    goal: tuple
    build_world: callable
    rules: dict
    item_factories: dict = field(default_factory=dict)
    must_have: tuple = ()
    must_not_have: tuple = ()
    action_order: tuple = ()
    forbidden_actions: tuple = ()
    forbidden_prefixes: tuple = ()


@dataclass
class ScenarioRun:
    scenario_id: str
    group: str
    goal: tuple
    success: bool
    errors: list
    action_history: list
    inventory: list
    impasses: int
    subgoals: int
    final_location: str


def make_item_factory(name, tags=None, state=None):
    return lambda: SOAR.SimpleItem(name=name, tags=tags, state=state)


def build_two_location_world(*, house_items=None, village_items=None, house_container_items=None, village_container_items=None):
    world = SOAR.World()
    world.add_location(SOAR.Location("House", tags=["Home"]), set_current=True)
    world.add_location(SOAR.Location("Village", tags=["Settlement"]))

    for location_name, items in (("House", house_items), ("Village", village_items)):
        for item_name, item in items or []:
            world.add_item(item, item_name, location_name=location_name)

    for location_name, container_name, items in (
        ("House", "Cupboard", house_container_items),
        ("Village", "Crate", village_container_items),
    ):
        if not items:
            continue
        container = SOAR.Container()
        world.add_item(container, container_name, location_name=location_name)
        for item_name, item in items:
            container.add_item(item, item_name)

    return world


def run_scenario(scenario):
    random.seed(scenario.seed)
    world = scenario.build_world()
    rules = SOAR.build_rules(**scenario.rules)
    agent = SOAR.Agent(
        world,
        rules,
        verbose=False,
        goals=[scenario.goal],
        proposal_selector=lambda proposals: proposals[0],
        item_factories=scenario.item_factories,
    )
    return world, agent, agent.run(max_steps=200)


def validate_scenario(scenario_id):
    scenario = SCENARIOS[scenario_id]
    _, agent, ok = run_scenario(scenario)
    errors = []

    if not ok:
        errors.append(f"run failed with actions {agent.action_history}")

    for item_name in scenario.must_have:
        if item_name not in agent.items:
            errors.append(f"expected {item_name} in inventory, got {list(agent.items)}")

    for item_name in scenario.must_not_have:
        if item_name in agent.items:
            errors.append(f"expected {item_name} to be absent, got {list(agent.items)}")

    for action_name in scenario.forbidden_actions:
        if action_name in agent.action_history:
            errors.append(f"unexpected action {action_name} in {agent.action_history}")

    for prefix in scenario.forbidden_prefixes:
        if any(action.startswith(prefix) for action in agent.action_history):
            errors.append(f"unexpected action prefix {prefix} in {agent.action_history}")

    for first, second in scenario.action_order:
        if first not in agent.action_history:
            errors.append(f"missing action {first} in {agent.action_history}")
            continue
        if second not in agent.action_history:
            errors.append(f"missing action {second} in {agent.action_history}")
            continue
        if agent.action_history.index(first) >= agent.action_history.index(second):
            errors.append(f"expected {first} before {second} in {agent.action_history}")

    return ScenarioRun(
        scenario_id=scenario_id,
        group=scenario.group,
        goal=scenario.goal,
        success=not errors,
        errors=errors,
        action_history=list(agent.action_history),
        inventory=sorted(agent.items),
        impasses=agent.impasse_count,
        subgoals=agent.subgoal_add_count,
        final_location=agent.state.get("location"),
    )


SEARCH_RULE_BUNDLE = "search_retrieval"
CRAFTING_RULE_BUNDLE = "crafting"


SCENARIOS = {
    "search_local_visible": Scenario(
        scenario_id="search_local_visible",
        group="search",
        seed=0,
        goal=("Me", "has", "Lantern"),
        build_world=lambda: build_two_location_world(
            house_items=[("Lantern", SOAR.SimpleItem(name="Lantern", tags=["SearchTarget"]))],
        ),
        rules={"bundle_name": SEARCH_RULE_BUNDLE, "target_name": "Lantern", "target_location": "House"},
        must_have=("Lantern",),
        forbidden_actions=("Action_Check_Container",),
        forbidden_prefixes=("Action_Go_To_",),
    ),
    "search_local_hidden": Scenario(
        scenario_id="search_local_hidden",
        group="search",
        seed=1,
        goal=("Me", "has", "Map"),
        build_world=lambda: build_two_location_world(
            house_container_items=[("Map", SOAR.SimpleItem(name="Map", tags=["SearchTarget"]))],
        ),
        rules={"bundle_name": SEARCH_RULE_BUNDLE, "target_name": "Map", "target_location": "House"},
        must_have=("Map",),
        action_order=(("Action_Check_Container", "Action_Grab_Map"),),
    ),
    "search_remote_location": Scenario(
        scenario_id="search_remote_location",
        group="search",
        seed=2,
        goal=("Me", "has", "Rope"),
        build_world=lambda: build_two_location_world(
            village_items=[("Rope", SOAR.SimpleItem(name="Rope", tags=["SearchTarget"]))],
        ),
        rules={"bundle_name": SEARCH_RULE_BUNDLE, "target_name": "Rope", "target_location": "Village"},
        must_have=("Rope",),
        action_order=(("Action_Go_To_Village", "Action_Grab_Rope"),),
    ),
    "craft_one_stage_two_inputs": Scenario(
        scenario_id="craft_one_stage_two_inputs",
        group="crafting",
        seed=3,
        goal=("Me", "has", "Torch"),
        build_world=lambda: build_two_location_world(
            house_items=[("Stick", SOAR.SimpleItem(name="Stick", tags=["Input"]))],
            village_items=[("Cloth", SOAR.SimpleItem(name="Cloth", tags=["Input"]))],
        ),
        rules={
            "bundle_name": CRAFTING_RULE_BUNDLE,
            "steps": [{"output": "Torch", "inputs": ["Stick", "Cloth"]}],
            "resource_locations": {"Stick": "House", "Cloth": "Village"},
        },
        item_factories={"Torch": make_item_factory("Torch", tags=["Crafted"])},
        must_have=("Torch",),
        must_not_have=("Stick", "Cloth"),
        forbidden_actions=(),
    ),
    "craft_two_stage_three_inputs": Scenario(
        scenario_id="craft_two_stage_three_inputs",
        group="crafting",
        seed=4,
        goal=("Me", "has", "StoneAxe"),
        build_world=lambda: build_two_location_world(
            house_items=[("Stick", SOAR.SimpleItem(name="Stick", tags=["Input"]))],
            village_items=[
                ("Cord", SOAR.SimpleItem(name="Cord", tags=["Input"])),
                ("Stone", SOAR.SimpleItem(name="Stone", tags=["Input"])),
            ],
        ),
        rules={
            "bundle_name": CRAFTING_RULE_BUNDLE,
            "steps": [
                {"output": "Handle", "inputs": ["Stick", "Cord"]},
                {"output": "StoneAxe", "inputs": ["Handle", "Stone"]},
            ],
            "resource_locations": {"Stick": "House", "Cord": "Village", "Stone": "Village"},
        },
        item_factories={
            "Handle": make_item_factory("Handle", tags=["Crafted"]),
            "StoneAxe": make_item_factory("StoneAxe", tags=["Crafted"]),
        },
        must_have=("StoneAxe",),
        must_not_have=("Stick", "Cord", "Stone"),
        action_order=(("Action_Craft_Handle", "Action_Craft_StoneAxe"),),
    ),
    "craft_three_stage_four_inputs": Scenario(
        scenario_id="craft_three_stage_four_inputs",
        group="crafting",
        seed=5,
        goal=("Me", "has", "SignalFire"),
        build_world=lambda: build_two_location_world(
            house_items=[
                ("Tinder", SOAR.SimpleItem(name="Tinder", tags=["Input"])),
                ("Coal", SOAR.SimpleItem(name="Coal", tags=["Input"])),
            ],
            village_items=[
                ("Fiber", SOAR.SimpleItem(name="Fiber", tags=["Input"])),
                ("Logs", SOAR.SimpleItem(name="Logs", tags=["Input"])),
            ],
        ),
        rules={
            "bundle_name": CRAFTING_RULE_BUNDLE,
            "steps": [
                {"output": "TinderBundle", "inputs": ["Tinder", "Fiber"]},
                {"output": "EmberBundle", "inputs": ["TinderBundle", "Coal"]},
                {"output": "SignalFire", "inputs": ["EmberBundle", "Logs"]},
            ],
            "resource_locations": {"Tinder": "House", "Fiber": "Village", "Coal": "House", "Logs": "Village"},
        },
        item_factories={
            "TinderBundle": make_item_factory("TinderBundle", tags=["Crafted"]),
            "EmberBundle": make_item_factory("EmberBundle", tags=["Crafted"]),
            "SignalFire": make_item_factory("SignalFire", tags=["Crafted"]),
        },
        must_have=("SignalFire",),
        must_not_have=("Tinder", "Fiber", "Coal", "Logs"),
        action_order=(
            ("Action_Craft_TinderBundle", "Action_Craft_EmberBundle"),
            ("Action_Craft_EmberBundle", "Action_Craft_SignalFire"),
        ),
    ),
}


class SoarScenarioTests(unittest.TestCase):
    def run_scenario_case(self, scenario_id):
        result = validate_scenario(scenario_id)
        self.assertTrue(result.success, msg=f"{scenario_id}: " + " | ".join(result.errors))

    def test_search_local_visible(self):
        self.run_scenario_case("search_local_visible")

    def test_search_local_hidden(self):
        self.run_scenario_case("search_local_hidden")

    def test_search_remote_location(self):
        self.run_scenario_case("search_remote_location")

    def test_craft_one_stage_two_inputs(self):
        self.run_scenario_case("craft_one_stage_two_inputs")

    def test_craft_two_stage_three_inputs(self):
        self.run_scenario_case("craft_two_stage_three_inputs")

    def test_craft_three_stage_four_inputs(self):
        self.run_scenario_case("craft_three_stage_four_inputs")


def list_scenarios():
    for scenario_id, scenario in SCENARIOS.items():
        print(f"{scenario_id} [{scenario.group}]")


def select_scenarios(group_filters=None, scenario_filters=None):
    selected = []
    for scenario_id, scenario in SCENARIOS.items():
        if group_filters and scenario.group not in group_filters:
            continue
        if scenario_filters and scenario_id not in scenario_filters:
            continue
        selected.append(scenario_id)
    return selected


def build_suite(selected_ids):
    suite = unittest.TestSuite()
    for scenario_id in selected_ids:
        suite.addTest(SoarScenarioTests(f"test_{scenario_id}"))
    return suite


def print_run_details(result):
    print(f"\n--- {result.scenario_id} [{result.group}] ---")
    print(f"Goal: {result.goal}")
    print(f"Success: {result.success}")
    print(f"Final location: {result.final_location}")
    print(f"Inventory: {result.inventory}")
    print(f"Action count: {len(result.action_history)}")
    print(f"Actions: {result.action_history}")
    print(f"Impasses: {result.impasses}  Subgoals: {result.subgoals}")
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")


def print_run_summary(results):
    total = len(results)
    successes = sum(1 for result in results if result.success)
    by_group = Counter(result.group for result in results)
    action_lengths = [len(result.action_history) for result in results]
    impasses = [result.impasses for result in results]
    subgoals = [result.subgoals for result in results]
    action_sequences = Counter(tuple(result.action_history) for result in results)

    print("\n===================")
    print("SCENARIO SUMMARY")
    print("===================")
    print(f"Scenarios run: {total}")
    print(f"Success: {successes}/{total}")
    print(f"Groups: {dict(by_group)}")
    print(f"Avg action count: {sum(action_lengths)/total:.2f}")
    print(f"Avg impasses: {sum(impasses)/total:.2f}")
    print(f"Avg subgoals: {sum(subgoals)/total:.2f}")

    print("\nTop action sequences:")
    for actions, count in action_sequences.most_common(10):
        print(f"  {count:>3}x  {list(actions)}")

    failures = [result for result in results if not result.success]
    if failures:
        print("\nFailures:")
        for result in failures:
            print(f"  {result.scenario_id}: {' | '.join(result.errors)}")


def maybe_write_plot(results, plot_path):
    if plot_path is None:
        return 0

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Plot requested, but matplotlib is not installed.", file=sys.stderr)
        return 1

    labels = [result.scenario_id for result in results]
    action_counts = [len(result.action_history) for result in results]
    impasses = [result.impasses for result in results]
    subgoals = [result.subgoals for result in results]

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle("SOAR Scenario Metrics")

    axes[0].bar(labels, action_counts, color="#3b82f6")
    axes[0].set_ylabel("Actions")

    axes[1].bar(labels, impasses, color="#f59e0b")
    axes[1].set_ylabel("Impasses")

    axes[2].bar(labels, subgoals, color="#10b981")
    axes[2].set_ylabel("Subgoals")
    axes[2].tick_params(axis="x", rotation=30)

    fig.tight_layout()
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved plot to {plot_path}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run SOAR scenario tests.")
    parser.add_argument("--list", action="store_true", help="List all scenario ids.")
    parser.add_argument("--group", action="append", choices=["search", "crafting"], help="Run only one scenario group.")
    parser.add_argument("--scenario", action="append", help="Run only a specific scenario id.")
    parser.add_argument("--verbosity", type=int, default=2, choices=[1, 2], help="unittest runner verbosity.")
    parser.add_argument("--show-summary", action="store_true", help="Print a richer summary after running scenarios.")
    parser.add_argument("--show-details", action="store_true", help="Print per-scenario action logs and metrics.")
    parser.add_argument("--plot", help="Optional path for a summary plot image, for example scenario_metrics.png")
    args = parser.parse_args(argv)

    if args.list:
        list_scenarios()
        return 0

    selected = select_scenarios(group_filters=args.group, scenario_filters=args.scenario)
    if not selected:
        print("No scenarios matched the requested filters.", file=sys.stderr)
        return 1

    if args.show_summary or args.show_details or args.plot:
        results = [validate_scenario(scenario_id) for scenario_id in selected]

        if args.show_details:
            for result in results:
                print_run_details(result)

        if args.show_summary:
            print_run_summary(results)

        plot_status = maybe_write_plot(results, args.plot)
        return 0 if all(result.success for result in results) and plot_status == 0 else 1

    result = unittest.TextTestRunner(verbosity=args.verbosity).run(build_suite(selected))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
