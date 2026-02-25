import random
from collections import Counter


'''
Kettle : No water
Coffee : Inside Cupboard
Mug : Inside Cupboard
Cupboard
Sink 
Floor

Agent Goal: Make coffee
'''

'''
- Fillable
- Portable
- Sippable
- Dispenses_{Fluid}
- Provides_{Fluid}
                  
Fluids   
    - Water
    - Hot_Water 
    - Coffee   
'''


# World Classes -------------------------------------------
class NullItem:
    def __getattr__(self, name):
        return lambda *args, **kwargs: False


class World: 
    def __init__(self):
        self.items = {}

    def add_item(self, item, name=None):
        base = name or item.name
        item_name = base
        count = 2
        # If a name is already used by a different instance, suffix it.
        while item_name in self.items and self.items[item_name] is not item:
            item_name = f"{base}_{count}"
            count += 1
        self.items[item_name] = item

    def get(self, item_name):
        return self.items.get(item_name, NullItem())

    def reveal_container_contents(self, container_name: str):
        c = self.get(container_name)
        if isinstance(c, Container):
            # Move everything into the world set
            for k, v in list(c.items.items()):
                self.add_item(v, k)
                del c.items[k]

    def find_by_tag(self, tag):
        for name, item in self.items.items():
            if tag in item.get_tags():
                return name, item
        return None, None

    def get_tags(self):
        return getattr(self, "tags", [])

class DrinkVessel:
    ID = 0
    def __init__(self, tags = None):
        self.ID = DrinkVessel.ID
        DrinkVessel.ID += 1

        self.name = "Mug"
        self.tags = tags or ["Drink_Vessel", "Portable", "Sippable" , "Fillable"]
        self.state = {"is_filled": False, 
                      "has": None}

    def get_state(self, condition):
        if condition == "all":
            return self.state
        return self.state.get(condition, False)
    
    def fill(self, content):
        self.state["is_filled"] = True
        self.state["has"] = content
        _add_tag_once(self, f"Provides_{content}")

    def get_tags(self):
        return getattr(self, "tags", [])

class FluidTransformer:
    ID = 0
    def __init__(self, tags=None, config=None):
        self.ID = FluidTransformer.ID
        FluidTransformer.ID += 1

        self.name = "Kettle"
        self.tags = tags or ["Fluid_Transformer", "Provides_Hot_Water" , "Fillable"]
        self.config = config or [("Water" , "Hot_Water")]
        self.state = {"is_filled": False, 
                      "has": None,
                      }

    def get_state(self, condition):
        if condition == "all":
            return self.state
        return self.state.get(condition, False)

    def get_tags(self):
        return getattr(self, "tags", [])

    def fill(self, content):
        self.state["is_filled"] = True
        self.state["has"] = content
        _add_tag_once(self, f"Provides_{content}")

    def transform(self):
        for IO in self.config:
            if self.state["is_filled"] and self.state["has"] == IO[0]:
                self.fill(IO[1])

class FluidSource:
    def __init__(self, tags=None):
        self.name = "Sink"
        self.tags = tags or ["Fluid_Source", "Dispenses_Water"]
        self.state = {}

    def get_state(self, condition):
        if condition == "all":
            return self.state
        return self.state.get(condition, False)

    def use(self):
        return True
    
    def get_tags(self):
        return getattr(self, "tags", [])

class DrinkMix:
    ID = 0
    def __init__(self):
        self.ID = DrinkMix.ID
        DrinkMix.ID += 1
        self.name = "CoffeeBox"
        self.state = {"amount": 100}        

    def get_state(self, condition):
        if condition == "all":
            return self.state
        return self.state.get(condition, False)
    
    def use(self):
        if self.state["amount"] > 0:
            self.state["amount"] -= 5
            return True
        return False
    
    def get_tags(self):
        return getattr(self, "tags", [])

class Container:
    def __init__(self):
        self.name = "Container"
        self.tags = ["Container"]
        self.state = {"is_open": False}
        self.items = {}

    def get_state(self, condition):
        if condition == "all":
            return self.state
        return self.state.get(condition, False)

    def add_item(self, item, name=None):
        base = name or item.name
        item_name = base
        count = 2
        while item_name in self.items and self.items[item_name] is not item:
            item_name = f"{base}_{count}"
            count += 1
        self.items[item_name] = item   

    def checkItems(self, item_name):
        return self.items.keys()
    
    def get(self, item_name):
        return self.items.get(item_name, NullItem())

    def get_tags(self):
        return getattr(self, "tags", [])    

# Agent Class -------------------------------------------
def _is_tag_ref(value):
    return isinstance(value, str) and value.startswith("tag:")

def _tag_name(value):
    return value.split(":", 1)[1].strip()

def _add_tag_once(obj, tag):
    if not hasattr(obj, "tags"):
        obj.tags = []
    if not tag in obj.get_tags():
        obj.tags.append(tag)

def _iter_tagged_objects(agent, world, tag):
    seen = set()
    for _, item in agent.inventory.items():
        if tag in item.get_tags() and id(item) not in seen:
            seen.add(id(item))
            yield item
    for _, item in world.items.items():
        if tag in item.get_tags() and id(item) not in seen:
            seen.add(id(item))
            yield item



def _is_not(pred: str) -> bool:
    return isinstance(pred, str) and pred.startswith("NOT_")

def _strip_not(pred: str) -> str:
    return pred[4:] if _is_not(pred) else pred

def _resolve_obj(agent, world, name: str):
    if _is_tag_ref(name):
        tag = _tag_name(name)
        for _, item in agent.inventory.items():
            if tag in item.get_tags():
                return item
        _, item = world.find_by_tag(tag)
        return item
    # Prefer inventory (Me holds it), else world
    if name in agent.inventory:
        return agent.inventory[name]
    if name in world.items:
        return world.items[name]
    return None

def _find_item_in_map_by_tag(items, tag):
    for name, item in items.items():
        if tag in item.get_tags():
            return name, item
    return None, None

def holds(agent, world, atom, current_goal=None) -> bool:
    """
    atom formats supported:
      ("goal", goal_atom)
      (S, P)                 e.g. ("Cupboard","NOT_is_open")
      (S, P, O)              e.g. ("World","has","Mug"), ("Mug","has","Hot_Water")
    """
    if not isinstance(atom, tuple):
        return False

    # goal check
    if len(atom) == 2 and atom[0] == "goal":
        return current_goal == atom[1]

    # Unary: (S, P)
    if len(atom) == 2:
        s, p = atom
        neg = _is_not(p)
        p = _strip_not(p)

        if _is_tag_ref(s):
            tag = _tag_name(s)
            matches = list(_iter_tagged_objects(agent, world, tag))
            if not matches:
                return False
            # For tag refs, interpret NOT_P as "there exists a tagged object where not P"
            if neg:
                val = any(not bool(obj.get_state(p)) for obj in matches)
            else:
                val =  any(bool(obj.get_state(p)) for obj in matches)
        else:
            obj = _resolve_obj(agent, world, s)
            if obj is None:
                val = False
            elif p == "is_open":
                val = bool(obj.get_state("is_open"))
            else:
                val = bool(obj.get_state(p))

            val = not val if neg else val

        return val

    # Binary: (S, P, O)
    if len(atom) == 3:
        s, p, o = atom
        neg = _is_not(p)
        p = _strip_not(p)

        if s == "World" and p == "has":
            if _is_tag_ref(o):
                _, found = world.find_by_tag(_tag_name(o))
                val = found is not None
            else:
                val = (o in world.items)
            return (not val) if neg else val

        if s == "Me" and p == "has":
            if _is_tag_ref(o):
                _, found = _find_item_in_map_by_tag(agent.inventory, _tag_name(o))
                val = found is not None
            else:
                val = (o in agent.inventory)
            return (not val) if neg else val

        if s == "Me" and p == "drank":
            val = (o in agent.state.get("drank", set()))
            return (not val) if neg else val

        if _is_tag_ref(s):
            tag = _tag_name(s)
            matches = list(_iter_tagged_objects(agent, world, tag))
            if not matches:
                return False

            def _pred(obj):
                if p == "has":
                    return obj.get_state("has") == o
                return obj.get_state(p) == o

            # For tag refs, interpret NOT_P similarly as existential mismatch.
            if neg:
                return any(not _pred(obj) for obj in matches)
            return any(_pred(obj) for obj in matches)

        # Object state: (Item, has, X) etc.
        obj = _resolve_obj(agent, world, s)
        if obj is None:
            val = False
            return (not val) if neg else val

        if p == "has":
            if o == "Hot_Water":
                val = (obj.get_state("has") == "Hot_Water")
            else:
                val = (obj.get_state("has") == o)
        else:
            # fallback
            val = (obj.get_state(p) == o)

        return (not val) if neg else val

    return False

def fmt(atom) -> str:
    if isinstance(atom, tuple):
        return "(" + ", ".join(map(str, atom)) + ")"
    return str(atom)


# Agent Class -------------------------------------------

class ActionRules:
    def __init__(self, name, preconditions, effects):
        self.name = name
        self.preconditions = preconditions
        self.effects = effects

    def missing_preconditions(self, agent, world):
        return [p for p in self.preconditions if not holds(agent, world, p, agent.current_goal())]

    def is_applicable(self, agent, world):
        return len(self.missing_preconditions(agent, world)) == 0

    def apply(self, agent, world):
        applied = []  # list[str] for logging

        for eff in self.effects:
            # Unary effects: (S, P)
            if isinstance(eff, tuple) and len(eff) == 2:
                s, p = eff
                resolved_name = s

                # World procedural hook
                if eff == ("World", "Update"):
                    applied.append("World.Update (no-op placeholder)")
                    continue

                if _is_tag_ref(s) and p == "is_open":
                    tag = _tag_name(s)
                    obj = None
                    for world_name, cand in world.items.items():
                        if tag in cand.get_tags() and not cand.get_state("is_open"):
                            obj = cand
                            resolved_name = world_name
                            break
                    if obj is None:
                        obj = _resolve_obj(agent, world, s)
                else:
                    obj = _resolve_obj(agent, world, s)
                if obj is None:
                    applied.append(f"SKIP {fmt(eff)} (no object)")
                    continue

                if p == "is_open":
                    obj.state["is_open"] = True
                    applied.append(f"SET {resolved_name}.is_open=True")
                    # Reveal container contents immediately when it becomes open
                    world.reveal_container_contents(resolved_name)
                    applied.append(f"REVEAL contents of {resolved_name} into World")

                else:
                    # generic boolean-ish set
                    if hasattr(obj, "state"):
                        obj.state[p] = True
                        applied.append(f"SET {s}.{p}=True")

            # Binary effects: (S, P, O)
            elif isinstance(eff, tuple) and len(eff) == 3:
                s, p, o = eff

                if s == "Me" and p == "has":
                    # Move from world -> inventory if present
                    if _is_tag_ref(o):
                        tag = _tag_name(o)
                        world_name, world_obj = world.find_by_tag(tag)
                        inv_name, _ = _find_item_in_map_by_tag(agent.inventory, tag)
                        if world_obj is not None:
                            agent.inventory[world_name] = world_obj
                            del world.items[world_name]
                            applied.append(f"Me picked up {world_name} via tag:{tag} (World → Inventory)")
                        elif inv_name is not None:
                            applied.append(f"Me already has {inv_name} via tag:{tag}")
                        else:
                            applied.append(f"SKIP {fmt(eff)} (no tagged object)")
                    elif o in world.items:
                        agent.inventory[o] = world.items[o]
                        del world.items[o]
                        applied.append(f"Me picked up {o} (World → Inventory)")
                    elif o in agent.inventory:
                        applied.append(f"Me already has {o}")
                    else:
                        agent.inventory[o] = o
                        applied.append(f"Me got {o} (toy acquire)")
                    continue
                if s == "Me" and p == "drank":
                    agent.state.setdefault("drank", set()).add(o)
                    applied.append(f"Me.drank += {o}")
                    continue

                if _is_tag_ref(s) and p == "has":
                    tag = _tag_name(s)
                    obj = None
                    for cand in _iter_tagged_objects(agent, world, tag):
                        if o == "Hot_Water" and hasattr(cand, "transform") and cand.get_state("has") == "Water":
                            obj = cand
                            break
                    if obj is None:
                        obj = _resolve_obj(agent, world, s)
                else:
                    obj = _resolve_obj(agent, world, s)
                if obj is None:
                    applied.append(f"SKIP {fmt(eff)} (no object)")
                    continue

                if p == "has":
                    if o == "Hot_Water":
                        if hasattr(obj, "transform"):
                            obj.transform()
                            applied.append(f"CALL {s}.transform()")
                            continue

                        # Symbolic hot water model
                        if hasattr(obj, "fill"):
                            obj.fill("Hot_Water")
                            applied.append(f"{s}.fill(Hot_Water)")
                        else:
                            obj.state["is_filled"] = True
                            obj.state["has"] = "Hot_Water"
                            applied.append(f"SET {s}.has=Hot_Water (filled)")

                    else:
                        if hasattr(obj, "fill") and o in ("Water", "Coffee", "Hot_Water"):
                            obj.fill(o)
                            applied.append(f"{s}.fill({o})")
                        else:
                            obj.state["has"] = o
                            if "is_filled" in getattr(obj, "state", {}):
                                obj.state["is_filled"] = True
                            applied.append(f"SET {s}.has={o}")

        return applied
       
class ProposalRules:
    def __init__(self, name, conditions, proposed_action):
        self.name = name
        self.conditions = conditions
        self.proposed_action = proposed_action

    def is_triggered(self, agent, world):
        g = agent.current_goal()
        for cond in self.conditions:
            if not holds(agent, world, cond, g):
                return False
        return True

class RuleSet:
    def __init__(self):
        self.action_rules = []
        self.proposal_rules = []

    def create_action_rule(self, name, preconditions, effects):
        self.action_rules.append(ActionRules(name, preconditions, effects))

    def create_proposal_rule(self, name, conditions, proposed_action):
        self.proposal_rules.append(ProposalRules(name, conditions, proposed_action))

class Agent:
    def __init__(self, world, ruleset, verbose=True, log_fn=print):
        self.world = world
        self.ruleset = ruleset

        self.name = "Agent"
        self.goals = [("Me", "drank", "Coffee")]  # default top goal
        self.inventory = {}
        self.knowledge = {}
        self.state = {"drank": set()}

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
        return holds(self, self.world, goal_atom, self.current_goal())

    def createProposals(self):
        # return list of (action_name, proposal_rule_name)
        out = []
        for pr in self.ruleset.proposal_rules:
            if pr.is_triggered(self, self.world):
                out.append((pr.proposed_action, pr.name))
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

        if ar.is_applicable(self, self.world):
            self.log(f"  EXECUTE {action_name}")
            applied = ar.apply(self, self.world)
            self.action_history.append(action_name)
            for a in applied:
                self.log(f"    -> {a}")
            return True

        missing = ar.missing_preconditions(self, self.world)
        self.impasse_count += 1
        self.log(f"  IMPASSE on {action_name}. Missing:")
        for m in missing:
            self.log(f"    - {fmt(m)}")

        if missing:
            sub = random.choice(missing)
            self.goals.append(sub)
            self.subgoal_add_count += 1
            self.subgoal_history.append((action_name, missing, sub))
            self.log(f"  SUBGOAL added: {fmt(sub)}")
        return False

    def step(self):
        if not self.goals:
            return False

        # Pop satisfied goals (log it)
        popped_any = False
        while self.goals and self.goal_satisfied(self.goals[-1]):
            g = self.goals.pop()
            self.log(f"POP satisfied goal: {fmt(g)}")
            popped_any = True

        if not self.goals:
            self.log("All goals satisfied.")
            return False

        g = self.current_goal()
        self.log(f"Current goal: {fmt(g)}")
        self.log(f"Goal stack: {[fmt(x) for x in self.goals]}")

        self.perceive(self.world)

        proposals = self.createProposals()
        self.log("Proposals:")
        for act, rname in proposals:
            self.log(f"  - {act}   (via {rname})")

        choice = self.SelectProposal(proposals)
        self.proposal_history.append((g, proposals, choice))

        if choice is None:
            self.log(f"[IMPASSE] No proposals for goal: {fmt(g)}")
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
            k.fill("Water")
            k.transform()
        elif r < hot_kettle_probability + water_kettle_probability:
            k.fill("Water")
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
    DRINK_VESSEL = "tag:Drink_Vessel"
    FLUID_TRANSFORMER = "tag:Fluid_Transformer"
    HOT_WATER_PROVIDER = "tag:Provides_Hot_Water"
    WATER_DISPENSER = "tag:Dispenses_Water"
    CONTAINER = "tag:Container"

    # proposals
    rules.create_proposal_rule("Proposal_Drink_Coffee",
        conditions=[("goal", ("Me", "drank", "Coffee"))],
        proposed_action="Action_Drink_Coffee"
    )
    rules.create_proposal_rule("Proposal_Mix_Coffee_And_Water",
        conditions=[("goal", (DRINK_VESSEL, "has", "Coffee"))],
        proposed_action="Action_Mix_Coffee_And_Water"
    )
    rules.create_proposal_rule("Proposal_Grab_CoffeeBox",
        conditions=[("goal", ("Me", "has", "CoffeeBox"))],
        proposed_action="Action_Grab_CoffeeBox"
    )
    rules.create_proposal_rule("Proposal_Grab_Drink_Vessel",
        conditions=[("goal", ("Me", "has", DRINK_VESSEL))],
        proposed_action="Action_Grab_Drink_Vessel"
    )
    rules.create_proposal_rule("Proposal_Check_Cupboard_1",
        conditions=[("goal", ("World", "has", "CoffeeBox")), ("World", "has", CONTAINER), (CONTAINER, "NOT_is_open")],
        proposed_action="Action_Check_Cupboard_1"
    )
    rules.create_proposal_rule("Proposal_Check_Cupboard_2",
        conditions=[("goal", ("World", "has", DRINK_VESSEL)), ("World", "has", CONTAINER), (CONTAINER, "NOT_is_open")],
        proposed_action="Action_Check_Cupboard_2"
    )
    rules.create_proposal_rule("Proposal_Fill_Mug_Hot_Water",
        conditions=[("goal", (DRINK_VESSEL, "has", "Hot_Water")), ("World", "has", HOT_WATER_PROVIDER)],
        proposed_action="Action_Fill_Mug_Hot_Water"
    )
    rules.create_proposal_rule("Proposal_Boil_Water",
        conditions=[("goal", (FLUID_TRANSFORMER, "has", "Hot_Water")), ("World", "has", FLUID_TRANSFORMER)],
        proposed_action="Action_Boil_Water"
    )
    rules.create_proposal_rule("Proposal_Boil_Water_From_Hot_Water_Provider_Goal",
        conditions=[("goal", (HOT_WATER_PROVIDER, "has", "Hot_Water")), ("World", "has", FLUID_TRANSFORMER)],
        proposed_action="Action_Boil_Water"
    )
    rules.create_proposal_rule("Proposal_Fill_Kettle_Water",
        conditions=[("goal", (FLUID_TRANSFORMER, "has", "Water")), ("World", "has", WATER_DISPENSER)],
        proposed_action="Action_Fill_Kettle_Water"
    )

    # actions
    rules.create_action_rule("Action_Drink_Coffee",
        preconditions=[("Me","has",DRINK_VESSEL), (DRINK_VESSEL,"has","Coffee")],
        effects=[("Me","drank","Coffee")]
    )
    rules.create_action_rule("Action_Mix_Coffee_And_Water",
        preconditions=[("Me","has","CoffeeBox"), ("Me","has",DRINK_VESSEL), (DRINK_VESSEL,"has","Hot_Water")],
        effects=[(DRINK_VESSEL,"has","Coffee")]
    )
    rules.create_action_rule("Action_Grab_CoffeeBox",
        preconditions=[("World","has","CoffeeBox")],
        effects=[("Me","has","CoffeeBox")]
    )
    rules.create_action_rule("Action_Grab_Drink_Vessel",
        preconditions=[("World","has",DRINK_VESSEL)],
        effects=[("Me","has",DRINK_VESSEL)]
    )
    rules.create_action_rule("Action_Check_Cupboard_1",
        preconditions=[("World","has",CONTAINER), (CONTAINER, "NOT_is_open")],
        effects=[(CONTAINER,"is_open"), ("World","Update")]
    )
    rules.create_action_rule("Action_Check_Cupboard_2",
        preconditions=[("World","has",CONTAINER), (CONTAINER, "NOT_is_open")],
        effects=[(CONTAINER,"is_open"), ("World","Update")]
    )
    rules.create_action_rule("Action_Fill_Mug_Hot_Water",
        preconditions=[("World","has",HOT_WATER_PROVIDER), (HOT_WATER_PROVIDER,"has","Hot_Water"), ("Me","has",DRINK_VESSEL)],
        effects=[(DRINK_VESSEL,"has","Hot_Water")]
    )
    rules.create_action_rule("Action_Boil_Water",
        preconditions=[("World","has",FLUID_TRANSFORMER), (FLUID_TRANSFORMER,"has","Water")],
        effects=[(FLUID_TRANSFORMER,"has", "Hot_Water")]
    )
    rules.create_action_rule("Action_Fill_Kettle_Water",
        preconditions=[("World","has",WATER_DISPENSER), ("World","has",FLUID_TRANSFORMER)],
        effects=[(FLUID_TRANSFORMER,"has","Water")]
    )

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
    ok = agent.run(max_steps=200)
    print("\nSingle-run success:", ok)
    print("Action sequence:", agent.action_history)

    # 2) stats across runs (prints only first run verbosely)
    run_multi_everything_trials(n=20000)
    #run_trials(n=200, verbose_first=1)
