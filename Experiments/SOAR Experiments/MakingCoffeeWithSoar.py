import random
from collections import Counter
import soar_rule_library
from typed_rule_engine import Binding, Evaluator, Grounder, OperationExecutor, substitute_vars

# World Classes -------------------------------------------
class World: 
    def __init__(self):
        self.items = {}

    def add_item(self, item, name=None):
        if item in self.items.values():
            return
        
        base = name or item.name
        item_name = base
        count = 2
        while item_name in self.items:
            item_name = f"{base}_{count}"
            count += 1

        self.items[item_name] = item
        return item_name

    def get(self, item_name):
        return self.items.get(item_name, NullItem())

    def remove_item(self, item_name):
        return self.items.pop(item_name, None)

    def find_by_tag(self, tag):
        for name, item in self.items.items():
            if tag in item.get_tags():
                return name, item
        return None, None

# Object Classes -------------------------------------------
class NullItem:
    def __getattr__(self, name):
        return lambda *args, **kwargs: False

class baseModule:
    def __init__(self, name="Object", tags=None, state=None):
        self.name = name
        self.tags = tags or []
        self.state = state or {}
        self.items = {}

    def get_tags(self):
        return getattr(self, "tags", [])
    
    def get_state(self, condition):
        if condition == "all":
            return self.state
        return self.state.get(condition, False)

    def apply_effect(self, p, v):
        if p in self.state.keys() and self.state.get(p, None) != v:
            self.state[p] = v
            return True
        return False

class DrinkVessel(baseModule):
    ID = 0
    def __init__(self, tags = None):
        self.ID = DrinkVessel.ID
        DrinkVessel.ID += 1

        super().__init__("Mug", tags or ["Drink_Vessel", "Portable", "Sippable" , "Fillable"], {"has": None})

class FluidTransformer(baseModule):
    ID = 0
    def __init__(self, tags=None):
        self.ID = FluidTransformer.ID
        FluidTransformer.ID += 1

        super().__init__("Kettle", tags or ["Fluid_Transformer", "Heats_Water", "Provides_Hot_Water", "Fillable"], {"has": None})

class FluidSource(baseModule):
    def __init__(self, tags=None):
        super().__init__("Sink", tags or ["Fluid_Source", "Dispenses_Water"])

class DrinkMix(baseModule):
    ID = 0
    def __init__(self):
        self.ID = DrinkMix.ID
        DrinkMix.ID += 1
        super().__init__("CoffeeBox", state={"amount": 100})

class Container(baseModule):
    def __init__(self):
        super().__init__("Container", ["Container"])

    def add_item(self, item, name=None):
        base = name or item.name
        item_name = base
        count = 2
        while item_name in self.items and self.items[item_name] is not item:
            item_name = f"{base}_{count}"
            count += 1
        
        self.items[item_name] = item   

    def checkItems(self):
        return self.items.keys()
    
    def get(self, item_name):
        return self.items.get(item_name, NullItem())

    def remove_item(self, item_name):
        return self.items.pop(item_name, None)

class RuleSet:
    def __init__(self):
        self.action_rules = []
        self.proposal_rules = []

    def create_action_rule(self, schema):
        self.action_rules.append(schema)

    def create_proposal_rule(self, proposal):
        self.proposal_rules.append(proposal)

class Agent:
    def __init__(self, world, ruleset, verbose=True, log_fn=print):
        self.world = world
        self.ruleset = ruleset

        self.name = "Agent"
        self.goals = [soar_rule_library.build_coffee_goal()]
        self.items = {}
        self.knowledge = {}
        self.state = {"drank": set()}
        self.evaluator = Evaluator()
        self.grounder = Grounder(evaluator=self.evaluator)
        self.executor = OperationExecutor(self.grounder.resolver)

        # logging / stats
        self.verbose = verbose
        self.log_fn = log_fn
        self.impasse_count = 0
        self.subgoal_add_count = 0

        self.action_history = []          # executed action names in order
        self.proposal_history = []        # (goal, proposals_list, chosen)
        self.subgoal_history = []         # (action, missing_list, chosen_subgoal)

    def log(self, msg):
        if self.verbose:
            self.log_fn(msg)

    def current_goal(self):
        return self.goals[-1] if self.goals else None

    def perceive(self, world):
        self.knowledge = {}
        for item_name, item in world.items.items():
            self.knowledge[item_name] = item.get_state("all") if hasattr(item, "get_state") else {}

    def goal_satisfied(self, goal_atom):
        return self.evaluator.holds(goal_atom, self, self.world, Binding(), self.current_goal())

    def createProposals(self):
        # return list of (action_name, proposal_rule_name)
        out = []
        for pr in self.ruleset.proposal_rules:
            if not self.evaluator.unmet(pr.when, self, self.world, Binding(), self.current_goal()):
                out.append((pr.propose, pr.name))
        return out

    def SelectProposal(self, proposals):
        if not proposals:
            return None
        return random.choice(proposals)

    def _find_action_rule(self, action_name):
        for ar in self.ruleset.action_rules:
            if ar.name == action_name:
                return ar
        return None

    def executeAction(self, action_name):
        ar = self._find_action_rule(action_name)
        if ar is None:
            self.log(f"[IMPASSE] No action rule named {action_name}")
            self.impasse_count += 1
            return False

        candidates = self.grounder.applicable_actions(ar, self, self.world, self.current_goal())
        if candidates:
            grounded = random.choice(candidates)
            self.log(f"  EXECUTE {action_name}")
            applied = self.executor.apply_all(ar.effects, self, self.world, grounded.binding)
            self.action_history.append(action_name)
            for a in applied:
                self.log(f"    -> {a}")
            return True

        missing = self._missing_for_schema(ar)
        self.impasse_count += 1
        self.log(f"  IMPASSE on {action_name}. Missing:")
        for m in missing:
            self.log(f"    - {m}")

        if missing:
            sub = random.choice(missing)
            self.goals.append(sub)
            self.subgoal_add_count += 1
            self.subgoal_history.append((action_name, missing, sub))
            self.log(f"  SUBGOAL added: {sub}")
        return False

    def _missing_for_schema(self, schema):
        grounded = self.grounder.ground_action(schema, self, self.world)
        if grounded:
            missing = self.evaluator.unmet(grounded[0].schema.preconditions, self, self.world, grounded[0].binding, self.current_goal())
        else:
            missing = schema.preconditions
        return [substitute_vars(pred, schema.params) for pred in missing]

    def step(self):
        if not self.goals:
            return False

        # Pop satisfied goals (log it)
        popped_any = False
        while self.goals and self.goal_satisfied(self.goals[-1]):
            g = self.goals.pop()
            self.log(f"POP satisfied goal: {g}")
            popped_any = True

        if not self.goals:
            self.log("All goals satisfied.")
            return False

        g = self.current_goal()
        self.log(f"Current goal: {g}")
        self.log(f"Goal stack: {[str(x) for x in self.goals]}")

        self.perceive(self.world)

        proposals = self.createProposals()
        self.log("Proposals:")
        for act, rname in proposals:
            self.log(f"  - {act}   (via {rname})")

        choice = self.SelectProposal(proposals)
        self.proposal_history.append((g, proposals, choice))

        if choice is None:
            self.log(f"[IMPASSE] No proposals for goal: {g}")
            self.impasse_count += 1
            return False

        action_name, via_rule = choice
        self.log(f"Chosen: {action_name}   (via {via_rule})")

        self.executeAction(action_name)
        return True

    def run(self, max_steps=200):
        for _ in range(max_steps):
            if not self.step():
                break
        return self.goals == []


# Testing Functions ----------------------------------
def build_world():
    stage = World()
    stage.add_item(Container(), "Cupboard")
    stage.add_item(FluidTransformer(), "Kettle")
    stage.add_item(FluidSource(), "Sink")
    stage.get("Cupboard").add_item(DrinkMix(), "CoffeeBox")
    stage.get("Cupboard").add_item(DrinkVessel(), "Mug")
    return stage

def build_multi_world(
    num_containers=3,
    num_kettles=2,
    num_sinks=1,
    num_drink_vessels=2,
    num_drink_mixes=1,
    visible_probability=0.35,
    water_kettle_probability=0.25,
    hot_kettle_probability=0.20,
    seed=None,
):
    rng = random.Random(seed)

    stage = World()

    base_container_names = ["Cupboard", "Pantry", "Drawer", "Cabinet", "Shelf", "Box"]
    container_names = []
    for i in range(num_containers):
        name = base_container_names[i] if i < len(base_container_names) else f"Container_{i+1}"
        container_names.append(name)
        stage.add_item(Container(), name)

    for _ in range(num_kettles):
        k = FluidTransformer()
        r = rng.random()
        if r < hot_kettle_probability:
            k.apply_effect("has", "Hot_Water")
        elif r < hot_kettle_probability + water_kettle_probability:
            k.apply_effect("has", "Water")
        stage.add_item(k, "Kettle")

    for _ in range(num_sinks):
        stage.add_item(FluidSource(), "Sink")

    objects = [DrinkVessel() for _ in range(num_drink_vessels)] + [DrinkMix() for _ in range(num_drink_mixes)]
    for obj in objects:
        if num_containers == 0 or rng.random() < visible_probability:
            stage.add_item(obj, obj.name)
        else:
            cname = rng.choice(container_names)
            stage.get(cname).add_item(obj, obj.name)

    return stage

def build_rules():
    rules = RuleSet()
    coffeeRules = soar_rule_library.build_coffee_rule_bundle()
    proposalRules = coffeeRules["proposal_rules"]
    actionRules = coffeeRules["action_rules"]

    # proposals
    for proposal in proposalRules:
        rules.create_proposal_rule(proposal)

    # actions
    for action in actionRules:
        rules.create_action_rule(action)

    return rules

def run_trials(n=50, verbose_first=1):
    seq_counter = Counter()
    success = 0
    steps = []
    impasses = []
    subgoals = []

    for i in range(n):
        random.seed(i)

        stage = build_world()
        rules = build_rules()

        agent = Agent(stage, rules, verbose=(i < verbose_first))
        ok = agent.run(max_steps=200)

        success += 1 if ok else 0
        impasses.append(agent.impasse_count)
        subgoals.append(agent.subgoal_add_count)

        seq_counter[tuple(agent.action_history)] += 1

        if i < verbose_first:
            print("\n--- RUN SUMMARY (verbose run) ---")
            print("Action sequence:", agent.action_history)
            print("Success:", ok)
            print("Impasse:", agent.impasse_count, "Subgoals:", agent.subgoal_add_count)

    print("\n===================")
    print("TRIALS SUMMARY")
    print("===================")
    print(f"Trials: {n}")
    print(f"Success: {success}/{n}")
    print(f"Unique action orders: {len(seq_counter)}")
    print(f"Avg impasses: {sum(impasses)/len(impasses):.2f}")
    print(f"Avg subgoals: {sum(subgoals)/len(subgoals):.2f}")

    print("\nTop action orders:")
    for seq, cnt in seq_counter.most_common(10):
        print(f"  {cnt:>3}x  {list(seq)}")

def run_multi_everything_trials(
    n=50,
    verbose_first=0,
    *,
    num_containers=3,
    num_kettles=2,
    num_sinks=1,
    num_drink_vessels=3,
    num_drink_mixes=2,
    visible_probability=0.35,
    water_kettle_probability=0.25,
    hot_kettle_probability=0.20,
    max_steps=300,
):
    seq_counter = Counter()
    success = 0
    impasses = []
    subgoals = []

    for i in range(n):
        random.seed(i)

        stage = build_multi_world(
            num_containers=num_containers,
            num_kettles=num_kettles,
            num_sinks=num_sinks,
            num_drink_vessels=num_drink_vessels,
            num_drink_mixes=num_drink_mixes,
            visible_probability=visible_probability,
            water_kettle_probability=water_kettle_probability,
            hot_kettle_probability=hot_kettle_probability,
            seed=i,
        )
        rules = build_rules()

        agent = Agent(stage, rules, verbose=(i < verbose_first))
        ok = agent.run(max_steps=max_steps)

        success += 1 if ok else 0
        impasses.append(agent.impasse_count)
        subgoals.append(agent.subgoal_add_count)
        seq_counter[tuple(agent.action_history)] += 1

        if i < verbose_first:
            print("\n--- MULTI RUN SUMMARY (verbose run) ---")
            print("Action sequence:", agent.action_history)
            print("Success:", ok)
            print("Impasse:", agent.impasse_count, "Subgoals:", agent.subgoal_add_count)

    print("\n===================")
    print("MULTI-EVERYTHING SUMMARY")
    print("===================")
    print(f"Trials: {n}")
    print(f"Success: {success}/{n}")
    print(f"Config: containers={num_containers}, kettles={num_kettles}, sinks={num_sinks}, vessels={num_drink_vessels}, mixes={num_drink_mixes}")
    print(f"Placement/State: visible_p={visible_probability}, water_kettle_p={water_kettle_probability}, hot_kettle_p={hot_kettle_probability}")
    print(f"Unique action orders: {len(seq_counter)}")
    print(f"Avg impasses: {sum(impasses)/len(impasses):.2f}")
    print(f"Avg subgoals: {sum(subgoals)/len(subgoals):.2f}")

    print("\nTop action orders:")
    for seq, cnt in seq_counter.most_common(10):
        print(f"  {cnt:>3}x  {list(seq)}")

if __name__ == "__main__":
    # 1) single run with logs
    random.seed(0)
    stage = build_world()
    rules = build_rules()
    agent = Agent(stage, rules, verbose=True)
    ok = agent.run(max_steps=20000)
    print("\nSingle-run success:", ok)
    print("Action sequence:", agent.action_history)

    # 2) stats across runs (prints only first run verbosely)
    run_multi_everything_trials(n=200)
    #run_trials(n=200, verbose_first=1)
    output = soar_rule_library.build_coffee_rule_bundle()
    
