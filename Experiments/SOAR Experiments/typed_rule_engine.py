from dataclasses import dataclass, field
from itertools import product
from typing import Any


@dataclass(frozen=True)
class Name:
    value: str


@dataclass(frozen=True)
class Tag:
    value: str


@dataclass(frozen=True)
class Var:
    name: str


ME = Name("Me")
WORLD = Name("World")


@dataclass(frozen=True)
class Binding:
    values: dict[str, tuple[str, str, Any]] = field(default_factory=dict)

    def with_value(self, name, resolved):
        next_values = dict(self.values)
        next_values[name] = resolved
        return Binding(next_values)


@dataclass(frozen=True)
class GoalIs:
    pred: object


@dataclass(frozen=True)
class Has:
    holder: object
    item: object


@dataclass(frozen=True)
class StateIs:
    subject: object
    key: str
    value: object


@dataclass(frozen=True)
class StateContains:
    subject: object
    key: str
    value: object


@dataclass(frozen=True)
class Transfer:
    item: object
    source: object
    target: object


@dataclass(frozen=True)
class SetState:
    subject: object
    key: str
    value: object


@dataclass(frozen=True)
class RevealFromContainer:
    item: object
    container: object | None = None
    target: object = WORLD


@dataclass(frozen=True)
class AddToSet:
    subject: object
    key: str
    value: object


@dataclass(frozen=True)
class ProposalRule:
    name: str
    when: list[object]
    propose: str
    priority: int = 0


@dataclass
class ActionSchema:
    name: str
    params: dict[str, object]
    preconditions: list[object]
    effects: list[object]


@dataclass(frozen=True)
class GroundedAction:
    schema: ActionSchema
    binding: Binding


class Resolver:
    def iter_visible(self, agent, world):
        for name, obj in agent.items.items():
            yield "agent", name, obj
        for name, obj in world.items.items():
            yield "world", name, obj

    def resolve(self, agent, world, selector, binding=None, *, include_containers=False):
        binding = binding or Binding()

        if isinstance(selector, Var):
            if selector.name not in binding.values:
                return []
            return [binding.values[selector.name]]

        if isinstance(selector, Name):
            if selector.value == "Me":
                return [("agent_state", "Me", agent)]
            if selector.value == "World":
                return [("world_state", "World", world)]
            out = []
            if selector.value in agent.items:
                out.append(("agent", selector.value, agent.items[selector.value]))
            if selector.value in world.items:
                out.append(("world", selector.value, world.items[selector.value]))
            if include_containers:
                for cname, container in world.items.items():
                    for iname, obj in container.items.items():
                        if iname == selector.value:
                            out.append((f"container:{cname}", iname, obj))
            return out

        if isinstance(selector, Tag):
            out = []
            seen = set()
            for scope, name, obj in self.iter_visible(agent, world):
                if selector.value in getattr(obj, "get_tags", lambda: [])():
                    oid = id(obj)
                    if oid not in seen:
                        seen.add(oid)
                        out.append((scope, name, obj))
            if include_containers:
                for cname, container in world.items.items():
                    for iname, obj in container.items.items():
                        if selector.value in getattr(obj, "get_tags", lambda: [])():
                            oid = id(obj)
                            if oid not in seen:
                                seen.add(oid)
                                out.append((f"container:{cname}", iname, obj))
            return out

        raise TypeError(f"Unknown selector: {selector!r}")


class Evaluator:
    def __init__(self, resolver=None):
        self.resolver = resolver or Resolver()
        self.predicate_handlers = {
            GoalIs: self._goal_is,
            Has: self._has,
            StateIs: self._state_is,
            StateContains: self._state_contains,
        }

    def holds(self, predicate, agent, world, binding=None, current_goal=None):
        binding = binding or Binding()
        return self.predicate_handlers[type(predicate)](predicate, agent, world, binding, current_goal)

    def _goal_is(self, predicate, _1, _2, _3, current_goal):
        return current_goal == predicate.pred

    def _state_is(self, predicate, agent, world, binding, _):
        return any(self._state_value(obj, predicate.key) == predicate.value for _, _, obj in self.resolver.resolve(agent, world, predicate.subject, binding))

    def _state_contains(self, predicate, agent, world, binding, _):
        for _, _, obj in self.resolver.resolve(agent, world, predicate.subject, binding):
            value = self._state_value(obj, predicate.key)
            if isinstance(value, set) and predicate.value in value:
                return True
        return False

    def _state_value(self, obj, key):
        if hasattr(obj, "get_state"):
            return obj.get_state(key)
        return getattr(obj, "state", {}).get(key, False)

    def _has(self, predicate, agent, world, binding, _):
        holders = self.resolver.resolve(agent, world, predicate.holder, binding)
        items = self.resolver.resolve(agent, world, predicate.item, binding)
        for _, _, holder in holders:
            for _, item_name, item in items:
                if item_name in holder.items and holder.items[item_name] is item:
                    return True
        return False

    def unmet(self, predicates, agent, world, binding=None, current_goal=None):
        return [p for p in predicates if not self.holds(p, agent, world, binding, current_goal)]


class Grounder:
    def __init__(self, resolver=None, evaluator=None):
        self.resolver = resolver or Resolver()
        self.evaluator = evaluator or Evaluator(self.resolver)

    def ground_action(self, schema, agent, world, seed_binding=None):
        seed_binding = seed_binding or Binding()
        names = list(schema.params)
        if not names:
            return [GroundedAction(schema, seed_binding)]

        choices = []
        for name in names:
            if name in seed_binding.values:
                choices.append([seed_binding.values[name]])
            else:
                choices.append(self.resolver.resolve(agent, world, schema.params[name], seed_binding))

        grounded = []
        for combo in product(*choices):
            binding = seed_binding
            for name, resolved in zip(names, combo):
                binding = binding.with_value(name, resolved)
            grounded.append(GroundedAction(schema, binding))
        return grounded

    def applicable_actions(self, schema, agent, world, current_goal=None):
        return [
            action
            for action in self.ground_action(schema, agent, world)
            if not self.evaluator.unmet(action.schema.preconditions, agent, world, action.binding, current_goal)
        ]


class OperationExecutor:
    def __init__(self, resolver=None):
        self.resolver = resolver or Resolver()
        self.effect_handlers = {
            Transfer: self._transfer,
            SetState: self._set_state,
            RevealFromContainer: self._reveal,
            AddToSet: self._add_to_set,
        }

    def apply_all(self, effects, agent, world, binding):
        return [self.apply(effect, agent, world, binding) for effect in effects]

    def apply(self, effect, agent, world, binding):
        handler = self.effect_handlers.get(type(effect))
        if handler is None:
            raise TypeError(f"Unknown operation: {effect!r}")
        return handler(effect, agent, world, binding)

    def _single(self, agent, world, selector, binding, *, include_containers=False):
        matches = self.resolver.resolve(agent, world, selector, binding, include_containers=include_containers)
        if not matches:
            raise ValueError(f"Selector did not resolve: {selector!r}")
        return matches[0]

    def _transfer(self, effect, agent, world, binding):
        source = self._single(agent, world, effect.source, binding)
        target = self._single(agent, world, effect.target, binding)
        item_scope, item_name, item = self._single(agent, world, effect.item, binding)

        if source[1] == "World":
            removed = world.remove_item(item_name)
        elif source[1] == "Me":
            removed = agent.items.pop(item_name, None)
        else:
            removed = source[2].items.pop(item_name, None)

        if removed is None:
            raise ValueError(f"Transfer source did not contain {item_name}")

        if target[1] == "Me":
            agent.items[item_name] = removed
        elif target[1] == "World":
            item_name = world.add_item(removed, item_name)
        else:
            target[2].add_item(removed, item_name)
        return f"Transfer {item_name} from {source[1]} to {target[1]}"

    def _set_state(self, effect, agent, world, binding):
        _, name, obj = self._single(agent, world, effect.subject, binding)
        if hasattr(obj, "apply_effect"):
            obj.apply_effect(effect.key, effect.value)
        else:
            obj.state[effect.key] = effect.value
        return f"Set {name}.{effect.key}={effect.value}"

    def _reveal(self, effect, agent, world, binding):
        containers = self.resolver.resolve(agent, world, effect.container, binding) if effect.container else [
            ("world", name, obj) for name, obj in world.items.items()
        ]
        for _, container_name, container in containers:
            for item_scope, item_name, item in self.resolver.resolve(agent, world, effect.item, binding, include_containers=True):
                if item_scope == f"container:{container_name}":
                    container.remove_item(item_name)
                    world_name = world.add_item(item, item_name)
                    return f"Reveal {world_name} from {container_name}"
        raise ValueError(f"Container item did not resolve: {effect.item!r}")

    def _add_to_set(self, effect, agent, world, binding):
        _, name, obj = self._single(agent, world, effect.subject, binding)
        obj.state.setdefault(effect.key, set()).add(effect.value)
        return f"Add {effect.value} to {name}.{effect.key}"

def substitute_vars(value, replacements):
    if isinstance(value, Var) and value.name in replacements:
        return replacements[value.name]
    if isinstance(value, GoalIs):
        return GoalIs(substitute_vars(value.pred, replacements))
    if isinstance(value, Has):
        return Has(substitute_vars(value.holder, replacements), substitute_vars(value.item, replacements))
    if isinstance(value, StateIs):
        return StateIs(substitute_vars(value.subject, replacements), value.key, value.value)
    if isinstance(value, StateContains):
        return StateContains(substitute_vars(value.subject, replacements), value.key, value.value)
    return value
