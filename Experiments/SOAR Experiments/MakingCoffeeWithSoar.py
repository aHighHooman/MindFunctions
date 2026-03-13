import importlib.util
import random
from collections import Counter
from pathlib import Path


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
class World:
    def __init__(self):
        self.locations = {}
        self.current_location_name = None

    @property
    def items(self):
        if self.current_location_name is None:
            return {}
        current = self.locations.get(self.current_location_name)
        if current is None:
            return {}
        return current.items

    def add_location(self, location, name=None, *, set_current=False):
        base = name or location.name
        location_name = base
        count = 2
        while location_name in self.locations and self.locations[location_name] is not location:
            location_name = f"{base}_{count}"
            count += 1
        self.locations[location_name] = location
        if set_current or self.current_location_name is None:
            self.current_location_name = location_name
        return location_name

    def set_current_location(self, location_name):
        if location_name not in self.locations:
            return False
        if self.current_location_name == location_name:
            return False
        self.current_location_name = location_name
        return True

    def add_item(self, item, name=None, location_name=None):
        if not self.locations:
            self.add_location(Location("Default"), set_current=True)

        target_location_name = location_name or self.current_location_name
        location = self.locations[target_location_name]
        return location.add_item(item, name)

    def get(self, item_name):
        return self.items.get(item_name, NullItem())

    def get_from_location(self, location_name, item_name):
        location = self.locations.get(location_name)
        if location is None:
            return NullItem()
        return location.get(item_name)

    def _remove_visible_refs_to(self, target):
        for name, item in list(self.items.items()):
            if item is target:
                del self.items[name]

    def remove_item(self, item_name):
        item = self.items.pop(item_name, None)
        if item is None:
            return None

        for maybe_container in list(self.items.values()):
            if not isinstance(maybe_container, Container):
                continue
            for contained_name, contained_item in list(maybe_container.items.items()):
                if contained_item is item:
                    del maybe_container.items[contained_name]
                    return item
        return item

    def _sync_container_contents_visibility(self, container_name: str):
        c = self.get(container_name)
        if not isinstance(c, Container):
            return

        if c.get_state("is_open"):
            for k, v in c.items.items():
                self.add_item(v, k)
            return

        for _, contained_item in c.items.items():
            self._remove_visible_refs_to(contained_item)

    def reveal_container_contents(self, container_name: str):
        self._sync_container_contents_visibility(container_name)

    def get_tags(self):
        return getattr(self, "tags", [])

# Object Classes -------------------------------------------
class NullItem:
    def __getattr__(self, name):
        return lambda *args, **kwargs: False


class Location:
    def __init__(self, name="Location", tags=None):
        self.name = name
        self.tags = ["Location"] + list(tags or [])
        self.state = {}
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
        return item_name

    def get(self, item_name):
        return self.items.get(item_name, NullItem())

    def get_tags(self):
        return getattr(self, "tags", [])


class Shop:
    def __init__(self, name="Shop", provided_items=None, tags=None):
        self.name = name
        self.tags = ["Shop"] + list(tags or [])
        self.state = {"is_open": True}
        for item_name in provided_items or []:
            _add_tag_once(self, f"Provides_{item_name}")

    def get_state(self, condition):
        if condition == "all":
            return self.state
        return self.state.get(condition, False)

    def get_tags(self):
        return getattr(self, "tags", [])


class SimpleItem:
    def __init__(self, name="Item", tags=None, state=None):
        self.name = name
        self.tags = list(tags or [])
        self.state = dict(state or {})

    def get_state(self, condition):
        if condition == "all":
            return self.state
        return self.state.get(condition, False)

    def get_tags(self):
        return getattr(self, "tags", [])

    def apply_effect(self, p, v, agent, world, *, resolved_name=None, scope=None):
        before = self.state.get(p, None)
        if before == v:
            return False
        self.state[p] = v
        return True


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
    
    def apply_effect(self, p, v, agent, world, *, resolved_name=None, scope=None):
        if p == "has":
            before = (self.state.get("has"), bool(self.state.get("is_filled")))
            self.fill(v)
            after = (self.state.get("has"), bool(self.state.get("is_filled")))
            return after != before

        before = self.state.get(p, None)
        if before == v:
            return False
        self.state[p] = v
        return True

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

    def apply_effect(self, p, v, agent, world, *, resolved_name=None, scope=None):
        if p == "has" and v == "Hot_Water":
            before = self.state.get("has")
            self.transform()
            return self.state.get("has") != before

        if p == "has":
            before = self.state.get("has")
            self.fill(v)
            return self.state.get("has") != before

        before = self.state.get(p, None)
        if before == v:
            return False
        self.state[p] = v
        return True

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

    def get(self, item_name):
        return self.items.get(item_name, NullItem())

    def get_tags(self):
        return getattr(self, "tags", [])    

    def apply_effect(self, p, v, agent, world, *, resolved_name=None, scope=None):
        if p == "is_open" and v is True:
            if self.state.get("is_open"):
                return False
            self.state["is_open"] = True
            # reveal only works if we know the world-visible name (Cupboard/Pantry/etc.)
            if resolved_name is not None:
                world.reveal_container_contents(resolved_name)
            return True

        before = self.state.get(p, None)
        if before == v:
            return False
        self.state[p] = v
        return True

# Agent Class -------------------------------------------
def _add_tag_once(obj, tag):
    if not hasattr(obj, "tags"):
        obj.tags = []
    if not tag in obj.get_tags():
        obj.tags.append(tag)

def fmt(atom) -> str:
    if isinstance(atom, tuple):
        return "(" + ", ".join(map(str, atom)) + ")"
    return str(atom)

class Rule:
    @staticmethod
    def parse_tag(ref):
        return ref[4:].strip() if isinstance(ref, str) and ref.startswith("tag:") else None
    
    @staticmethod
    def parse_not(p: str):
        neg = isinstance(p, str) and p.startswith("NOT_")
        return neg, (p[4:] if neg else p)

    @classmethod
    def iter_items(cls, items, ref):
        """Yield (name,obj) from ONE dict, where ref is either exact key or tag:..."""
        assert isinstance(ref, str), "ref must be str (iter_items)"
        tag = cls.parse_tag(ref)

        if tag is None:
            if ref in items:
                yield ref, items[ref]
            return

        for name, obj in items.items():
            if tag in obj.get_tags():
                yield name, obj

    @classmethod
    def find_item(cls, items, ref):
        return next(cls.iter_items(items, ref), (None, None))

    @classmethod
    def has_item(cls, items, ref):
        # boolean membership that supports tag: refs too
        name, obj = cls.find_item(items, ref)
        return obj is not None

    @classmethod
    def iter_subjects(cls, agent, world, ref):
        assert isinstance(ref, str), "ref must be str (iter_subjects)"

        tag = cls.parse_tag(ref)

        # Name reference: resolve agent first, then world (no dedupe needed)
        if tag is None:
            if ref in agent.items:
                yield ref, agent.items[ref], "agent"
                return
            if ref in world.items:
                yield ref, world.items[ref], "world"
            return

        # Tag reference: search both scopes + dedupe shared instances
        seen = set()

        for name, obj in agent.items.items():
            if tag in obj.get_tags():
                oid = id(obj)
                if oid not in seen:
                    seen.add(oid)
                    yield name, obj, "agent"

        for name, obj in world.items.items():
            if tag in obj.get_tags():
                oid = id(obj)
                if oid not in seen:
                    seen.add(oid)
                    yield name, obj, "world"
    
    @classmethod
    def holds_atom(cls, agent, world, atom, current_goal=None) -> bool:
        assert isinstance(atom, tuple), "Must be a tuple (RuleReferenceMixin.holds_atom())"

        if atom[0] == "goal":
            return current_goal == atom[1]

        if len(atom) == 2:
            # inside holds_atom, for len(atom)==2
            s, p = atom
            neg, p = cls.parse_not(p)  # if you adopted the (neg, pred) version

            it = cls.iter_subjects(agent, world, s)
            if neg:
                return any(not bool(obj.get_state(p)) for _, obj, _ in it)
            return any(bool(obj.get_state(p)) for _, obj, _ in it)

        if len(atom) == 3:
            s, p, o = atom
            neg,p = cls.parse_not(p)

            if s == "Me" and p == "at":
                val = (agent.state.get("location") == o)
                return (not val) if neg else val

            if s == "World" and p == "has":
                val = cls.has_item(world.items, o)
                return (not val) if neg else val

            if s == "Me" and p == "has":
                val = cls.has_item(agent.items, o)
                return (not val) if neg else val

            if s == "Me" and p == "drank":
                val = (o in agent.state.get("drank", set()))
                return (not val) if neg else val

            if s in world.locations and p == "has":
                val = cls.has_item(world.locations[s].items, o)
                return (not val) if neg else val

            matches = cls.iter_subjects(agent, world, s)
            if neg:
                return any(obj.get_state(p) != o for _, obj, _ in matches)
            return any(obj.get_state(p) == o for _, obj, _ in matches)

        return False

class ActionRule(Rule):
    def __init__(self, name, preconditions, effects):
        self.name = name
        self.preconditions = list(preconditions)
        self.effects = [self._coerce_effect(e) for e in effects]

    @staticmethod
    def _coerce_effect(eff):
        # Allow old (S,P) shorthand => (S,P,True)
        if not isinstance(eff, tuple):
            raise TypeError(f"Effect must be tuple, got {type(eff)}: {eff}")
        if len(eff) == 2:
            s, p = eff
            return (s, p, True)
        if len(eff) == 3:
            return eff
        raise ValueError(f"Effect must be len 2 or 3, got len {len(eff)}: {eff}")

    def missing_preconditions(self, agent, world):
        g = agent.current_goal()
        return [p for p in self.preconditions if not self.holds_atom(agent, world, p, g)]

    def is_applicable(self, agent, world):
        return not self.missing_preconditions(agent, world)

    def apply(self, agent, world):
        applied = []

        for (s, p, v) in self.effects:
            # Agent-level semantics
            if s == "Me" and p == "at":
                moved = world.set_current_location(v)
                agent.state["location"] = world.current_location_name
                if moved:
                    applied.append(f"Me moved to {v}")
                else:
                    applied.append(f"SKIP ({s},{p},{v}) (already there or missing location)")
                continue

            if s == "Me" and p == "has":
                world_name, world_obj = self.find_item(world.items, v)  # v can be name or tag:...
                if world_name is None:
                    applied.append(f"SKIP ({s},{p},{v}) (missing in World)")
                    continue

                agent.items[world_name] = world_obj
                world.remove_item(world_name)
                applied.append(f"Me picked up {world_name}")
                continue

            if s == "Me" and p == "drank":
                agent.state.setdefault("drank", set()).add(v)
                applied.append(f"Me.drank += {v}")
                continue

            if s == "Me" and p == "consume":
                item_name, _ = self.find_item(agent.items, v)
                if item_name is None:
                    applied.append(f"SKIP consume {v} (missing in inventory)")
                    continue

                del agent.items[item_name]
                applied.append(f"Me consumed {item_name}")
                continue

            if s == "Me" and p == "create":
                item_name = agent.create_item(v)
                if item_name is None:
                    applied.append(f"SKIP create {v} (no item factory)")
                    continue

                applied.append(f"Me created {item_name}")
                continue

            applied_name = None
            for name, obj, scope in self.iter_subjects(agent, world, s):
                if hasattr(obj, "apply_effect"):
                    ok = bool(obj.apply_effect(p, v, agent, world, resolved_name=name, scope=scope))
                else:
                    state = getattr(obj, "state", None)
                    if state is None:
                        ok = False
                    elif p == "has" and hasattr(obj, "fill"):
                        before = (state.get("has"), bool(state.get("is_filled", False)))
                        obj.fill(v)
                        after = (state.get("has"), bool(state.get("is_filled", False)))
                        ok = after != before
                    elif v is True:
                        if bool(state.get(p, None)):
                            ok = False
                        else:
                            state[p] = True
                            ok = True
                    else:
                        before = state.get(p, None)
                        if before == v:
                            ok = False
                        else:
                            state[p] = v
                            if p == "has" and "is_filled" in state:
                                state["is_filled"] = True
                            ok = True

                if ok:
                    applied_name = name
                    break

            if applied_name is None:
                applied.append(f"SKIP ({s},{p},{v}) (no applicable object)")
            else:
                applied.append(f"APPLY {applied_name}.{p}={v}")

        return applied

class ProposalRule(Rule):
    def __init__(self, name, conditions, proposed_action):
        self.name = name
        self.conditions = conditions
        self.proposed_action = proposed_action

    def is_triggered(self, agent, world):
        g = agent.current_goal()
        for cond in self.conditions:
            if not self.holds_atom(agent, world, cond, g):
                return False
        return True

class RuleSet:
    def __init__(self):
        self.action_rules = []
        self.proposal_rules = []

    def create_action_rule(self, name, preconditions, effects):
        self.action_rules.append(ActionRule(name, preconditions, effects))

    def create_proposal_rule(self, name, conditions, proposed_action):
        self.proposal_rules.append(ProposalRule(name, conditions, proposed_action))

class Agent:
    def __init__(
        self,
        world,
        ruleset,
        verbose=True,
        log_fn=print,
        goals=None,
        proposal_selector=None,
        item_factories=None,
    ):
        self.world = world
        self.ruleset = ruleset

        self.name = "Agent"
        self.goals = list(goals) if goals is not None else [("Me", "drank", "Coffee")]
        self.items = {}
        self.knowledge = {}
        self.state = {"drank": set(), "location": world.current_location_name}
        self.proposal_selector = proposal_selector
        self.item_factories = dict(item_factories or {})

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
        return ProposalRule.holds_atom(self, self.world, goal_atom, self.current_goal())

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
        if self.proposal_selector is not None:
            return self.proposal_selector(proposals)
        return random.choice(proposals)

    def create_item(self, item_key):
        factory = self.item_factories.get(item_key)
        if factory is None:
            return None

        item = factory() if callable(factory) else factory
        if item is None:
            return None

        base_name = getattr(item, "name", item_key)
        item_name = base_name
        count = 2
        while item_name in self.items and self.items[item_name] is not item:
            item_name = f"{base_name}_{count}"
            count += 1

        self.items[item_name] = item
        return item_name

    def executeAction(self, action_name):
        ar = next((rule for rule in self.ruleset.action_rules if rule.name == action_name), None)
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


# Testing Functions ----------------------------------
def build_world():
    stage = World()
    stage.add_location(Location("House", tags=["Home"]), set_current=True)
    stage.add_location(Location("Village", tags=["Settlement"]))

    stage.add_item(Container(), "Cupboard", location_name="House")
    stage.add_item(FluidTransformer(), "Kettle", location_name="House")
    stage.add_item(FluidSource(), "Sink", location_name="House")
    stage.get_from_location("House", "Cupboard").add_item(DrinkVessel(), "Mug")

    stage.add_item(Shop("GeneralStore", provided_items=["CoffeeBox", "Mug"]), "GeneralStore", location_name="Village")
    stage.add_item(Shop("ApplianceShop", provided_items=["Kettle"]), "ApplianceShop", location_name="Village")
    stage.add_item(DrinkMix(), "CoffeeBox", location_name="Village")
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
    stage.add_location(Location("House", tags=["Home"]), set_current=True)
    stage.add_location(Location("Village", tags=["Settlement"]))

    base_container_names = ["Cupboard", "Pantry", "Drawer", "Cabinet", "Shelf", "Box"]
    container_names = []
    for i in range(num_containers):
        name = base_container_names[i] if i < len(base_container_names) else f"Container_{i+1}"
        container_names.append(name)
        stage.add_item(Container(), name, location_name="House")

    for _ in range(num_kettles):
        k = FluidTransformer()
        r = rng.random()
        if r < hot_kettle_probability:
            k.fill("Water")
            k.transform()
        elif r < hot_kettle_probability + water_kettle_probability:
            k.fill("Water")
        stage.add_item(k, "Kettle", location_name="House")

    for _ in range(num_sinks):
        stage.add_item(FluidSource(), "Sink", location_name="House")

    stage.add_item(Shop("GeneralStore", provided_items=["CoffeeBox", "Mug"]), "GeneralStore", location_name="Village")
    stage.add_item(Shop("ApplianceShop", provided_items=["Kettle"]), "ApplianceShop", location_name="Village")

    objects = [DrinkVessel() for _ in range(num_drink_vessels)] + [DrinkMix() for _ in range(num_drink_mixes)]
    for obj in objects:
        if isinstance(obj, DrinkMix) and rng.random() < 0.7:
            stage.add_item(obj, obj.name, location_name="Village")
        elif num_containers == 0 or rng.random() < visible_probability:
            stage.add_item(obj, obj.name, location_name="House")
        else:
            cname = rng.choice(container_names)
            stage.get_from_location("House", cname).add_item(obj, obj.name)

    return stage

def build_rules(bundle_name="coffee", **bundle_kwargs):
    rule_library_path = Path(__file__).with_name("soar_rule_library.py")
    spec = importlib.util.spec_from_file_location("soar_rule_library", rule_library_path)
    rule_library = importlib.util.module_from_spec(spec)
    assert spec.loader is not None, f"Unable to load rule library from {rule_library_path}"
    spec.loader.exec_module(rule_library)

    bundle = rule_library.get_rule_bundle(bundle_name, **bundle_kwargs)
    rules = RuleSet()
    rules.proposal_rules = [
        ProposalRule(spec["name"], spec["conditions"], spec["proposed_action"])
        for spec in bundle["proposal_rules"]
    ]
    rules.action_rules = [
        ActionRule(spec["name"], spec["preconditions"], spec["effects"])
        for spec in bundle["action_rules"]
    ]
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
    run_multi_everything_trials(n=20000)
    #run_trials(n=200, verbose_first=1)
