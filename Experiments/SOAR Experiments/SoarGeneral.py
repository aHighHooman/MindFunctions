import random
def fmt(atom) -> str:
    if isinstance(atom, tuple):
        return "(" + ", ".join(map(str, atom)) + ")"
    return str(atom)

class NullItem:
    def __getattr__(self, name):
        return lambda *args, **kwargs: False


class World:
    def __init__(self):
        self.items = {}
        self.global_time = 0

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

    def remove_item(self, item_name):
        return self.items.pop(item_name, None)

    def tick(self):
        self.global_time += 1

    def get_tags(self):
        return getattr(self, "tags", [])


class GenericObject:
    def __init__(self, name="Object", tags=None, state=None):
        self.name = name
        self.tags = tags or []
        self.state = state or {}

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


class Rule:
    @staticmethod
    def parse_tag(ref):
        return ref[4:].strip() if isinstance(ref, str) and ref.startswith("tag:") else None

    @staticmethod
    def parse_not(p):
        neg = isinstance(p, str) and p.startswith("NOT_")
        return neg, (p[4:] if neg else p)

    @classmethod
    def iter_items(cls, items, ref):
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
        _, obj = cls.find_item(items, ref)
        return obj is not None

    @classmethod
    def iter_subjects(cls, agent, world, ref):
        assert isinstance(ref, str), "ref must be str (iter_subjects)"
        tag = cls.parse_tag(ref)

        if tag is None:
            if ref in agent.items:
                yield ref, agent.items[ref], "agent"
                return
            if ref in world.items:
                yield ref, world.items[ref], "world"
            return

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
        assert isinstance(atom, tuple), "Must be a tuple (holds_atom())"

        if atom[0] == "goal":
            return current_goal == atom[1]

        if len(atom) == 2:
            s, p = atom
            neg, p = cls.parse_not(p)
            it = cls.iter_subjects(agent, world, s)
            if neg:
                return any(not bool(obj.get_state(p)) for _, obj, _ in it)
            return any(bool(obj.get_state(p)) for _, obj, _ in it)

        if len(atom) == 3:
            s, p, o = atom
            neg, p = cls.parse_not(p)

            if s == "World" and p == "has":
                val = cls.has_item(world.items, o)
                return (not val) if neg else val

            if s == "Me" and p == "has":
                val = cls.has_item(agent.items, o)
                return (not val) if neg else val

            if s == "Me" and p == "satisfied":
                val = agent.is_utility_satisfied(o)
                return (not val) if neg else val

            if s == "Time" and p == "at_least":
                val = world.global_time >= float(o)
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

    def _default_apply_effect(self, obj, p, v):
        state = getattr(obj, "state", None)
        if state is None:
            return False

        before = state.get(p, None)
        if v is True:
            if bool(before):
                return False
            state[p] = True
            return True

        if before == v:
            return False

        state[p] = v
        return True

    def _try_apply_to_subject(self, agent, world, s, p, v):
        for name, obj, scope in self.iter_subjects(agent, world, s):
            if hasattr(obj, "apply_effect"):
                ok = bool(obj.apply_effect(p, v, agent, world, resolved_name=name, scope=scope))
            else:
                ok = self._default_apply_effect(obj, p, v)
            if ok:
                return name, True

        return None, False

    def apply(self, agent, world):
        applied = []

        for (s, p, v) in self.effects:
            if s == "Me" and p == "has":
                world_name, world_obj = self.find_item(world.items, v)
                if world_name is None:
                    applied.append(f"SKIP ({s},{p},{v}) (missing in World)")
                    continue

                agent.items[world_name] = world_obj
                world.remove_item(world_name)
                applied.append(f"Me picked up {world_name}")
                continue

            if s == "Me" and p == "consume":
                ok, detail = agent.consume_item(v)
                applied.append(detail if ok else f"SKIP consume {v}")
                continue

            if s == "Me" and p == "use_for_fun":
                ok, detail = agent.use_for_fun(v)
                applied.append(detail if ok else f"SKIP use_for_fun {v}")
                continue

            if s == "Me" and p == "adjust_utility":
                if isinstance(v, tuple) and len(v) == 2:
                    utility_name, delta = v
                    agent.adjust_utility(utility_name, float(delta))
                    applied.append(f"Me.utility[{utility_name}] += {delta}")
                    continue
                applied.append(f"SKIP ({s},{p},{v}) (invalid utility tuple)")
                continue

            if s == "Me" and p == "set_state":
                if isinstance(v, tuple) and len(v) == 2:
                    state_name, state_val = v
                    agent.state[state_name] = state_val
                    applied.append(f"Me.state[{state_name}] = {state_val}")
                    continue
                applied.append(f"SKIP ({s},{p},{v}) (invalid state tuple)")
                continue

            name, ok = self._try_apply_to_subject(agent, world, s, p, v)
            if not ok:
                applied.append(f"SKIP ({s},{p},{v}) (no applicable object)")
            else:
                applied.append(f"APPLY {name}.{p}={v}")

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
    def __init__(self, world, ruleset, name="Agent", verbose=True, log_fn=print):
        self.world = world
        self.ruleset = ruleset

        self.name = name
        self.goals = []
        self.items = {}
        self.knowledge = {}
        self.state = {}

        self.utilities = {"food": 50.0, "entertainment": 50.0}
        self.utility_decay = {"food": 1.0, "entertainment": 1.0}
        self.utility_targets = {"food": 65.0, "entertainment": 65.0}

        self.verbose = verbose
        self.log_fn = log_fn
        self.impasse_count = 0
        self.subgoal_add_count = 0

        self.action_history = []
        self.proposal_history = []
        self.subgoal_history = []

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

    def adjust_utility(self, key, delta):
        current = float(self.utilities.get(key, 0.0))
        self.utilities[key] = max(0.0, min(100.0, current + float(delta)))

    def is_utility_satisfied(self, key):
        return float(self.utilities.get(key, 0.0)) >= float(self.utility_targets.get(key, 65.0))

    def decay_utilities(self):
        for key, decay in self.utility_decay.items():
            self.adjust_utility(key, -float(decay))

    def choose_goal_from_utilities(self):
        if not self.utilities:
            return None
        need_name = min(self.utilities, key=lambda k: self.utilities[k])
        return ("Me", "satisfied", need_name)

    def refresh_base_goal(self):
        goal = self.choose_goal_from_utilities()
        if goal is None:
            return
        if not self.goals:
            self.goals = [goal]
            return
        self.goals[0] = goal

    def consume_item(self, ref):
        item_name, item = Rule.find_item(self.items, ref)
        if item is None:
            return False, f"SKIP consume {ref} (not in inventory)"

        if not hasattr(item, "consume"):
            return False, f"SKIP consume {item_name} (no consume method)"

        ok = bool(item.consume(self, self.world))
        if not ok:
            return False, f"SKIP consume {item_name} (cannot consume)"

        if hasattr(item, "is_depleted") and item.is_depleted():
            del self.items[item_name]
            return True, f"Me consumed {item_name} (depleted)"

        return True, f"Me consumed {item_name}"

    def use_for_fun(self, ref):
        item_name, item = Rule.find_item(self.items, ref)
        if item is None:
            return False, f"SKIP use_for_fun {ref} (not in inventory)"

        if not hasattr(item, "use_for_fun"):
            return False, f"SKIP use_for_fun {item_name} (no use_for_fun method)"

        ok = bool(item.use_for_fun(self, self.world))
        if not ok:
            return False, f"SKIP use_for_fun {item_name} (cannot use)"

        if hasattr(item, "is_depleted") and item.is_depleted():
            del self.items[item_name]
            return True, f"Me used {item_name} for fun (depleted)"

        return True, f"Me used {item_name} for fun"

    def executeAction(self, action_name):
        ar = self._find_action_rule(action_name)
        if ar is None:
            self.log(f"[{self.name}] [IMPASSE] No action rule named {action_name}")
            self.impasse_count += 1
            return False

        if ar.is_applicable(self, self.world):
            self.log(f"[{self.name}]   EXECUTE {action_name}")
            applied = ar.apply(self, self.world)
            self.action_history.append(action_name)
            for a in applied:
                self.log(f"[{self.name}]     -> {a}")
            return True

        missing = ar.missing_preconditions(self, self.world)
        self.impasse_count += 1
        self.log(f"[{self.name}]   IMPASSE on {action_name}. Missing:")
        for m in missing:
            self.log(f"[{self.name}]     - {fmt(m)}")

        if missing:
            sub = random.choice(missing)
            self.goals.append(sub)
            self.subgoal_add_count += 1
            self.subgoal_history.append((action_name, missing, sub))
            self.log(f"[{self.name}]   SUBGOAL added: {fmt(sub)}")
        return False

    def step(self):
        if not self.goals:
            return False

        popped_any = False
        while self.goals and self.goal_satisfied(self.goals[-1]):
            g = self.goals.pop()
            self.log(f"[{self.name}] POP satisfied goal: {fmt(g)}")
            popped_any = True

        if popped_any and not self.goals:
            self.refresh_base_goal()

        if not self.goals:
            return False

        g = self.current_goal()
        self.log(f"[{self.name}] Current goal: {fmt(g)}")
        self.log(f"[{self.name}] Goal stack: {[fmt(x) for x in self.goals]}")

        self.perceive(self.world)

        proposals = self.createProposals()
        self.log(f"[{self.name}] Proposals:")
        for act, rname in proposals:
            self.log(f"[{self.name}]   - {act}   (via {rname})")

        choice = self.SelectProposal(proposals)
        self.proposal_history.append((g, proposals, choice))

        if choice is None:
            self.log(f"[{self.name}] [IMPASSE] No proposals for goal: {fmt(g)}")
            self.impasse_count += 1
            return False

        action_name, via_rule = choice
        self.log(f"[{self.name}] Chosen: {action_name}   (via {via_rule})")

        self.executeAction(action_name)
        return True

    def run(self, max_steps=200):
        for _ in range(max_steps):
            if not self.step():
                break
        return True
