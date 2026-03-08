import os
import random
from collections import Counter

from SoarGeneral import Agent, RuleSet, World, fmt


class FoodItem:
    ID = 0

    def __init__(self, name="Food", food_gain=32.0, servings=1, tags=None):
        self.ID = FoodItem.ID
        FoodItem.ID += 1

        self.name = name
        self.tags = tags or ["Food", "Consumable", "Portable"]
        self.state = {
            "servings": int(servings),
            "food_gain": float(food_gain),
        }

    def get_state(self, condition):
        if condition == "all":
            return self.state
        return self.state.get(condition, False)

    def get_tags(self):
        return getattr(self, "tags", [])

    def consume(self, agent, world):
        if self.state["servings"] <= 0:
            return False

        self.state["servings"] -= 1
        agent.adjust_utility("food", self.state["food_gain"])
        agent.state.setdefault("food_events", 0)
        agent.state["food_events"] += 1
        return True

    def is_depleted(self):
        return self.state["servings"] <= 0


class EntertainmentItem:
    ID = 0

    def __init__(self, name="Entertainment", fun_gain=20.0, uses=5, tags=None):
        self.ID = EntertainmentItem.ID
        EntertainmentItem.ID += 1

        self.name = name
        self.tags = tags or ["Entertainment", "Portable"]
        self.state = {
            "uses": int(uses),
            "fun_gain": float(fun_gain),
        }

    def get_state(self, condition):
        if condition == "all":
            return self.state
        return self.state.get(condition, False)

    def get_tags(self):
        return getattr(self, "tags", [])

    def use_for_fun(self, agent, world):
        if self.state["uses"] <= 0:
            return False

        self.state["uses"] -= 1
        agent.adjust_utility("entertainment", self.state["fun_gain"])
        agent.state.setdefault("fun_events", 0)
        agent.state["fun_events"] += 1
        return True

    def is_depleted(self):
        return self.state["uses"] <= 0


class UtilityDrivenAgent(Agent):
    def __init__(self, world, ruleset, name="Agent", rng=None, verbose=False, log_fn=print):
        super().__init__(world, ruleset, name=name, verbose=verbose, log_fn=log_fn)
        self.rng = rng or random.Random()

        self.utilities = {
            "food": self.rng.uniform(35.0, 90.0),
            "entertainment": self.rng.uniform(35.0, 90.0),
        }
        self.utility_decay = {
            "food": self.rng.uniform(2.1, 4.0),
            "entertainment": self.rng.uniform(1.4, 3.1),
        }
        self.utility_targets = {
            "food": 65.0,
            "entertainment": 62.0,
        }

        self.refresh_base_goal()

    def step(self):
        self.decay_utilities()
        self.refresh_base_goal()
        return super().step()


def build_life_world(seed=None):
    rng = random.Random(seed)
    stage = World()

    food_pool = [
        ("Apple", 20.0, 1),
        ("Sandwich", 34.0, 1),
        ("Granola", 16.0, 2),
        ("RiceBowl", 38.0, 1),
        ("Berries", 14.0, 2),
        ("SoupCup", 24.0, 2),
    ]

    entertainment_pool = [
        ("Book", 12.0, 9),
        ("Podcast", 9.0, 11),
        ("ChessSet", 16.0, 8),
        ("Guitar", 18.0, 7),
        ("VideoGame", 21.0, 10),
        ("SketchPad", 14.0, 9),
        ("Basketball", 15.0, 10),
    ]

    for _ in range(12):
        n, gain, servings = rng.choice(food_pool)
        stage.add_item(FoodItem(name=n, food_gain=gain, servings=servings), n)

    for _ in range(18):
        n, gain, uses = rng.choice(entertainment_pool)
        stage.add_item(EntertainmentItem(name=n, fun_gain=gain, uses=uses), n)

    return stage


def build_life_rules():
    rules = RuleSet()

    FOOD = "tag:Food"
    ENTERTAINMENT = "tag:Entertainment"

    FOOD_GOAL = ("Me", "satisfied", "food")
    ENTERTAINMENT_GOAL = ("Me", "satisfied", "entertainment")

    # top-level utility goals
    rules.create_proposal_rule(
        "Proposal_Satisfy_Food",
        conditions=[("goal", FOOD_GOAL)],
        proposed_action="Action_Satisfy_Food",
    )
    rules.create_proposal_rule(
        "Proposal_Satisfy_Entertainment",
        conditions=[("goal", ENTERTAINMENT_GOAL)],
        proposed_action="Action_Satisfy_Entertainment",
    )

    # subgoal handling
    rules.create_proposal_rule(
        "Proposal_Get_Food",
        conditions=[("goal", ("Me", "has", FOOD)), ("World", "has", FOOD)],
        proposed_action="Action_Get_Food",
    )
    rules.create_proposal_rule(
        "Proposal_Get_Entertainment",
        conditions=[("goal", ("Me", "has", ENTERTAINMENT)), ("World", "has", ENTERTAINMENT)],
        proposed_action="Action_Get_Entertainment",
    )

    rules.create_action_rule(
        "Action_Satisfy_Food",
        preconditions=[("Me", "has", FOOD)],
        effects=[("Me", "consume", FOOD)],
    )
    rules.create_action_rule(
        "Action_Get_Food",
        preconditions=[("World", "has", FOOD)],
        effects=[("Me", "has", FOOD)],
    )

    rules.create_action_rule(
        "Action_Satisfy_Entertainment",
        preconditions=[("Me", "has", ENTERTAINMENT)],
        effects=[("Me", "use_for_fun", ENTERTAINMENT)],
    )
    rules.create_action_rule(
        "Action_Get_Entertainment",
        preconditions=[("World", "has", ENTERTAINMENT)],
        effects=[("Me", "has", ENTERTAINMENT)],
    )

    return rules


def _count_world_resources(world):
    counts = Counter()
    for _, obj in world.items.items():
        tags = obj.get_tags() if hasattr(obj, "get_tags") else []
        if "Food" in tags:
            counts["Food"] += 1
        if "Entertainment" in tags:
            counts["Entertainment"] += 1
    return counts


def _default_log_file_path():
    return os.path.join(os.path.dirname(__file__), "life_simulation.log")


def _agent_success(agent):
    return all(agent.is_utility_satisfied(k) for k in agent.utility_targets.keys())


def _write_log_line(log_handle, line):
    if log_handle is None:
        return
    log_handle.write(line + "\n")


def run_life_simulation(
    num_agents=5,
    ticks=45,
    seed=0,
    verbose_agents=False,
    print_output=True,
    log_file_path=None,
    append_log=False,
):
    random.seed(seed)
    stage = build_life_world(seed=seed)
    rules = build_life_rules()

    if log_file_path is None:
        log_file_path = _default_log_file_path()

    log_mode = "a" if append_log else "w"
    log_handle = open(log_file_path, log_mode, encoding="utf-8")

    rng = random.Random(seed)
    agents = []
    for i in range(num_agents):
        arng = random.Random(rng.randint(0, 10_000_000))
        agents.append(
            UtilityDrivenAgent(
                stage,
                rules,
                name=f"Agent_{i+1}",
                rng=arng,
                verbose=verbose_agents,
            )
        )

    _write_log_line(log_handle, f"=== RUN seed={seed} ticks={ticks} agents={num_agents} ===")

    for _ in range(ticks):
        stock = _count_world_resources(stage)
        if print_output:
            print(f"\n=== Global Time {stage.global_time} ===")
            print(f"World stock -> Food: {stock['Food']} | Entertainment: {stock['Entertainment']}")

        _write_log_line(
            log_handle,
            f"TIME {stage.global_time} WORLD Food={stock['Food']} Entertainment={stock['Entertainment']}",
        )

        for ag in agents:
            before = len(ag.action_history)
            progressed = ag.step()
            action = ag.action_history[-1] if len(ag.action_history) > before else "NoAction"

            line = (
                f"{ag.name:>8} | food={ag.utilities['food']:.1f} "
                f"ent={ag.utilities['entertainment']:.1f} "
                f"goal={fmt(ag.current_goal())} "
                f"action={action} "
                f"inv={len(ag.items)}"
            )

            if print_output:
                print(line)
            _write_log_line(log_handle, line)

            if not progressed and ag.current_goal() is None:
                ag.refresh_base_goal()

        stage.tick()

    total_actions = sum(len(a.action_history) for a in agents)
    success_count = sum(1 for a in agents if _agent_success(a))
    trial_success = success_count == len(agents)

    if print_output:
        print("\n===================")
        print("LIFE SIM SUMMARY")
        print("===================")
        print(f"Ticks: {ticks}")
        print(f"Agents: {len(agents)}")
        print(f"Global time end: {stage.global_time}")
        print(f"Agent success: {success_count}/{len(agents)}")
        print(f"Trial success (all agents): {trial_success}")
        print(f"Total actions executed: {total_actions}")

    _write_log_line(log_handle, "--- RUN SUMMARY ---")
    _write_log_line(log_handle, f"Ticks={ticks}")
    _write_log_line(log_handle, f"GlobalTimeEnd={stage.global_time}")
    _write_log_line(log_handle, f"AgentSuccess={success_count}/{len(agents)}")
    _write_log_line(log_handle, f"TrialSuccess={trial_success}")
    _write_log_line(log_handle, f"TotalActions={total_actions}")

    for ag in agents:
        summary_line = (
            f"{ag.name}: actions={len(ag.action_history)}, "
            f"impasses={ag.impasse_count}, subgoals={ag.subgoal_add_count}, "
            f"food={ag.utilities['food']:.1f}, entertainment={ag.utilities['entertainment']:.1f}, "
            f"inventory={list(ag.items.keys())}"
        )
        if print_output:
            print(summary_line)
        _write_log_line(log_handle, summary_line)

    _write_log_line(log_handle, "")
    log_handle.close()

    return {
        "agents": agents,
        "ticks": ticks,
        "seed": seed,
        "global_time_end": stage.global_time,
        "success_count": success_count,
        "trial_success": trial_success,
        "total_actions": total_actions,
        "log_file_path": log_file_path,
    }


def run_life_trials(
    n=50,
    verbose_first=0,
    *,
    num_agents=6,
    ticks=35,
    seed_start=0,
    log_file_path=None,
    append_log=False,
):
    seq_counter = Counter()
    trial_success_count = 0
    total_agent_success = 0
    impasses = []
    subgoals = []

    if log_file_path is None:
        log_file_path = _default_log_file_path()

    for i in range(n):
        seed = seed_start + i
        result = run_life_simulation(
            num_agents=num_agents,
            ticks=ticks,
            seed=seed,
            verbose_agents=(i < verbose_first),
            print_output=(i < verbose_first),
            log_file_path=log_file_path,
            append_log=(append_log or i > 0),
        )

        trial_success_count += 1 if result["trial_success"] else 0
        total_agent_success += int(result["success_count"])

        for ag in result["agents"]:
            impasses.append(ag.impasse_count)
            subgoals.append(ag.subgoal_add_count)
            seq_counter[tuple(ag.action_history)] += 1

        if i < verbose_first:
            print("\n--- RUN SUMMARY (verbose run) ---")
            print(f"Trial seed: {seed}")
            print(f"Trial success: {result['trial_success']}")
            print(f"Agent success: {result['success_count']}/{num_agents}")

    print("\n===================")
    print("TRIALS SUMMARY")
    print("===================")
    print(f"Trials: {n}")
    print(f"Trial success (all agents): {trial_success_count}/{n}")
    print(f"Agent success total: {total_agent_success}/{n * num_agents}")
    print(f"Unique action orders: {len(seq_counter)}")

    avg_impasses = (sum(impasses) / len(impasses)) if impasses else 0.0
    avg_subgoals = (sum(subgoals) / len(subgoals)) if subgoals else 0.0
    print(f"Avg impasses: {avg_impasses:.2f}")
    print(f"Avg subgoals: {avg_subgoals:.2f}")

    print("\nTop action orders:")
    for seq, cnt in seq_counter.most_common(10):
        print(f"  {cnt:>3}x  {list(seq)}")

    print(f"\nAction log file: {log_file_path}")


if __name__ == "__main__":
    log_path = _default_log_file_path()

    run_life_simulation(
        num_agents=6,
        ticks=35,
        seed=5,
        verbose_agents=False,
        print_output=True,
        log_file_path=log_path,
        append_log=False,
    )

    run_life_trials(
        n=50,
        verbose_first=0,
        num_agents=6,
        ticks=35,
        seed_start=0,
        log_file_path=log_path,
        append_log=True,
    )

