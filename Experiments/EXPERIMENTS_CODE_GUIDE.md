# Experiments Code Guide

## Scope

This document covers the code-bearing experiment files under `Experiments/` and skips the text-only `.md` notes, images, and cache files.

I use **guard** in two ways:

1. **Branch guards**: explicit `if` / `elif` checks in code.
2. **Semantic guards**: preconditions, trigger conditions, or rule conditions that gate whether an action/exchange can happen.

That split matters here because some files are mostly data/rules with very few `if` statements, while others are engines with lots of branching but only a few domain rules.

## High-Level Read

- **CiF** is the cleanest self-contained social simulation experiment. It has a reusable engine, declarative exchange content, scenario data, a runner, and tests.
- **SOAR Experiments** are the strongest planning/procedural experiments, but they currently duplicate core rule-engine logic in two places.
- **Utility Experimentation** contains one real reusable experiment (`PureUtilityExperiment.py`) and one scratchpad (`ProbabilityCostTesting.py`).
- **Lowest-value code to cut first**: `chatbotTesting.py`, `ProbabilityCostTesting.py`, and duplicated SOAR planner logic if you consolidate.

## 1. CiF

### What it is

The CiF folder models short social scenes between characters. Each turn:

1. A situation supplies characters, relationship values, moods, statuses, context, enabled exchanges, and trigger rules.
2. The engine scores every eligible exchange for the current initiator/responder pair.
3. The highest-volition exchange is chosen.
4. The responder acceptance score decides `accept` vs `reject`.
5. Effects mutate relationships, moods, and statuses.
6. Trigger rules may add second-order state changes like `romantic_tension`, `awkward`, `enemy`, or `jealous`.

### File-by-file

#### `chatbotTesting.py`

What it does:
- A one-off Ollama chat script with alternating speakers and a hardcoded model/persona.

How it works:
- Starts with a roleplay prompt.
- Makes one model call.
- Stores the model reply in a two-view conversation log.

Guard count:
- **2 branch guards**
- `if not initialize`
- `if speaker`

Assessment:
- Pure scratch code.
- Hardcoded host and model.
- Not connected to the CiF engine.
- Best candidate for deletion if you want to reduce noise.

#### `cif_content.py`

What it does:
- Defines the social vocabulary used by the engine:
  - condition builders like `relationship_is`, `metric_at_least`, `has_status`
  - effect builders like `change_link`, `change_mood`, `add_status`
  - the social exchange library
  - trigger rules

How it works:
- Each `SocialExchange` defines:
  - `preconditions`
  - initiator influence rules
  - responder influence rules
  - accept effects
  - reject effects
  - text instantiations
- The engine imports this data and evaluates it at runtime.

Guard count:
- **29 branch guards**
- **9 semantic exchange preconditions** across 9 exchanges
- **41 initiator influence guards**
- **31 responder influence guards**
- **5 trigger guards**

Exchange guard inventory:

| Exchange | Preconditions | Why it exists |
| --- | --- | --- |
| `Converse` | none | Always-available fallback interaction |
| `Compliment` | relationship is not `enemy` | Blocks praise in fully hostile states |
| `Joke` | relationship is not `enemy` | Prevents jokes in enemy context |
| `Flirt` | relationship is not `enemy`; initiator attraction >= 15 | Blocks romance unless some attraction exists |
| `Insult` | none | Always-available hostility path |
| `Apologize` | either direction has `awkward` | Only appears after social friction |
| `Comfort` | responder wariness >= 15 | Only appears when the responder is upset enough |
| `AskOut` | attraction >= 35; like >= 20 | Requires strong romantic momentum |
| `RejectAdvance` | either direction has `romantic_tension` | Only appears after romantic escalation |

Trigger guard inventory:

| Trigger | Guard | Effect |
| --- | --- | --- |
| `romantic_tension` | last 2 events are accepted `Flirt` exchanges by the same pair, and tension is not already set | Adds `romantic_tension` both ways |
| `awkward_after_rejection` | last 2 events are rejections in `Flirt` / `AskOut` / `RejectAdvance` for the same pair | Adds `awkward` both ways |
| `hostility_spiral` | pair has at least 2 `Insult` events in the last 3, and relationship is not already `enemy` | Escalates relationship to `bad_acquaintance` or `enemy` |
| `comfort_pattern` | same pair has at least 2 accepted `Comfort` events in the last 5 | Adds `comfortable_with` and boosts trust |
| `jealous_observer` | latest event is an accepted `Flirt` or `AskOut`, and a third character has trait `jealous` plus attraction >= 25 to the responder | Raises envy and adds `jealous` status |

Optimization ideas:
- Replace stringly-typed directions like `"forward"`, `"reverse"`, `"either"` with enums or constants.
- Pre-index `situation.characters` by name so `initiator_has_trait` and `responder_has_trait` do not scan the character list every time.
- Exchanges are repetitive; consider a small schema or helper factory for baseline influence rules.
- Trigger conditions and effects could be grouped into a dedicated `triggers.py` if the library keeps growing.

Keep/cut guidance:
- **Keep**. This is one of the most valuable experiment files in the repo.

#### `cif_engine.py`

What it does:
- Runs the CiF simulation.

How it works:
- `build_initial_state` creates default relationship/numeric/status/mood state and overlays scenario values.
- `score_rules` sums active influence-rule weights.
- `score_exchange` rejects exchanges that fail preconditions, then computes volition and acceptance.
- `choose_turn` evaluates all possible responders and exchanges for the current initiator and picks a highest-volition candidate.
- `run_situation` executes turn-by-turn state mutation and trigger evaluation.

Guard count:
- **14 branch guards**

Important runtime guards:
- Skip self-to-self exchanges.
- Reject an exchange immediately if any precondition fails.
- Raise an error if a turn has no eligible exchanges.
- Outcome guard: `accept` when acceptance >= 0, otherwise `reject`.
- Trigger rules only fire when their condition returns true.

Optimization ideas:
- Cache the list of character names per situation instead of rebuilding it in multiple functions.
- `snapshot` + `describe_changes` is readable, but allocates a lot of dictionaries every turn; acceptable now, but it is the first place to optimize if run counts grow.
- `choose_turn` currently scores every enabled exchange for every responder every turn. Fine for current scale, but a pruning layer could help if you add many more exchanges.

Keep/cut guidance:
- **Keep**. This is the CiF runtime core.

#### `cif_situations.py`

What it does:
- Defines 7 scenario configurations.

How it works:
- Imports the exchange library and trigger library.
- Creates `Situation` objects with initial state, context, allowed exchanges, turn limits, and seeds.

Guard count:
- **0 branch guards**
- Structural guard rail is in the data:
  - only listed exchanges are allowed per situation
  - turn limits cap runtime

Situation guard surface:

| Situation | Enabled exchanges | Turn limit |
| --- | --- | --- |
| `awkward_first_meeting` | 5 | 8 |
| `friendly_hangout` | 4 | 8 |
| `tense_reunion` | 4 | 8 |
| `crush_at_a_party` | 7 | 10 |
| `comfort_after_failure` | 4 | 8 |
| `public_embarrassment` | 6 | 10 |
| `jealous_triangle` | 7 | 12 |

Optimization ideas:
- If scenario count grows, move to one file per scenario family or a data file.

Keep/cut guidance:
- **Keep**. Pure scenario data is cheap and useful.

#### `run_cif_experiments.py`

What it does:
- CLI runner for listing situations, printing summaries, or printing full transcripts.

Guard count:
- **7 branch guards**

Useful guards:
- `--list` short-circuits to situation listing.
- `--transcript` toggles verbose output.
- Pair summary skips self-pairs.

Keep/cut guidance:
- **Keep**. Small, useful, and low-maintenance.

#### `test_cif_experiments.py`

What it does:
- Smoke and invariants test suite for the CiF system.

What it verifies:
- every situation runs
- every used exchange is enabled for that situation
- numeric state stays clamped
- trigger-driven status changes appear where expected

Guard count:
- **2 branch guards**

Keep/cut guidance:
- **Keep**. Cheap safety net with good value.

### CiF cut summary

Cut first:
- `chatbotTesting.py`

Keep:
- `cif_content.py`
- `cif_engine.py`
- `cif_situations.py`
- `run_cif_experiments.py`
- `test_cif_experiments.py`

## 2. SOAR Experiments

### What it is

This folder explores rule-based planning with subgoals and impasses.

The flow is:

1. The agent has a goal.
2. Proposal rules suggest actions when their conditions match the current goal and world state.
3. The agent chooses one proposal.
4. If action preconditions fail, the missing precondition becomes a subgoal.
5. If action preconditions pass, the action mutates world or inventory state.

That is the most important idea in this folder: **missing preconditions become new goals**.

### File-by-file

#### `MakingCoffeeWithSoar.py`

What it does:
- Full coffee-world planner and simulator.
- Includes world model, item classes, rule engine, agent, world builders, rule loading, and batch trial runners.

How it works:
- `World` manages locations and location-local visibility.
- `Container` supports hidden contents that become visible when opened.
- `DrinkVessel`, `FluidTransformer`, `FluidSource`, and `DrinkMix` provide domain-specific state transitions.
- `Rule` and `ActionRule` evaluate atoms like `("Me", "has", "CoffeeBox")` or `(container, "NOT_is_open")`.
- `Agent.executeAction` creates subgoals on failed preconditions.
- `build_rules` imports a rule bundle from `soar_rule_library.py`.
- `run_trials` and `run_multi_everything_trials` stress-test the domain.

Guard count:
- **98 branch guards**
- Coffee domain bundle loaded by default has:
  - **18 proposal rules**
  - **42 proposal condition atoms**
  - **11 action rules**
  - **20 action precondition atoms**

Most important semantic guards in the coffee bundle:

| Guard family | Examples |
| --- | --- |
| Goal guards | `("goal", ("Me", "drank", "Coffee"))`, `("goal", ("Me", "has", "CoffeeBox"))` |
| Travel guards | `("Me", "NOT_at", "Village")`, `("House", "has", "tag:Drink_Vessel")` |
| Discovery guards | `("World", "has", "tag:Container")`, `(container, "NOT_is_open")` |
| Resource guards | `("World", "has", "CoffeeBox")`, `("World", "has", "tag:Provides_Hot_Water")` |
| Production guards | `(drink_vessel, "has", "Hot_Water")`, `(fluid_transformer, "has", "Water")` |
| Completion guards | `("Me", "has", drink_vessel)` and `(drink_vessel, "has", "Coffee")` before drinking |

Optimization ideas:
- Biggest issue: this file duplicates much of `SoarGeneral.py`.
- `build_rules` dynamically imports the rule library every time; cache the loaded module or import normally.
- The `__main__` block runs `run_multi_everything_trials(n=20000)`, which is too heavy for a default script entrypoint.
- World/item/rule/agent classes should be split into smaller modules if this experiment is meant to survive.

Keep/cut guidance:
- **Keep the ideas, not the duplication**.
- If trimming, keep either this as the only SOAR engine or keep `SoarGeneral.py` as the reusable base and shrink this to domain-only classes plus builders.

#### `soar_rule_library.py`

What it does:
- Stores reusable rule bundles for coffee, search/retrieval, and crafting.

How it works:
- Returns plain dictionaries for proposal and action rules.
- `get_rule_bundle` dispatches bundle construction.

Guard count:
- **2 branch guards**
- Semantic guard surface depends on bundle:
  - `coffee`: 42 proposal atoms, 20 action-precondition atoms
  - search/retrieval example: 10 proposal atoms, 4 action-precondition atoms
  - 3-stage crafting example: 23 proposal atoms, 12 action-precondition atoms

Optimization ideas:
- Good candidate to keep.
- Could benefit from validation helpers so malformed rule specs fail early.

Keep/cut guidance:
- **Keep**. This is compact and reusable.

#### `soar_scenario_tests.py`

What it does:
- Scenario-based validation harness for search and crafting bundles.

How it works:
- Builds worlds from scenario specs.
- Runs the planner.
- Verifies inventory, forbidden actions, required action order, and summary stats.

Guard count:
- **20 branch guards**

Scenario guard surface:

| Scenario | Proposal atoms | Action-precondition atoms | Proposal rules | Action rules |
| --- | ---: | ---: | ---: | ---: |
| `search_local_visible` | 10 | 4 | 3 | 3 |
| `search_local_hidden` | 10 | 4 | 3 | 3 |
| `search_remote_location` | 10 | 4 | 3 | 3 |
| `craft_one_stage_two_inputs` | 11 | 6 | 5 | 5 |
| `craft_two_stage_three_inputs` | 17 | 9 | 8 | 7 |
| `craft_three_stage_four_inputs` | 23 | 12 | 11 | 9 |

Optimization ideas:
- Keep this as the main regression harness if you consolidate the SOAR code.
- `callable` in the dataclass could be typed more strictly.

Keep/cut guidance:
- **Keep**. High signal, low clutter.

#### `SoarGeneral.py`

What it does:
- A general-purpose version of the same rule/planning engine without the coffee-world location/container details.
- Adds utility decay/utility satisfaction concepts.

How it works:
- Generic objects live in a flat world.
- Proposal rules choose candidate actions.
- Failed preconditions generate subgoals.
- Utility helper methods can refresh a base need goal such as `("Me", "satisfied", "food")`.

Guard count:
- **64 branch guards**

Important runtime guards:
- special handling for `goal`, `World has`, `Me has`, `Me satisfied`, and `Time at_least` atoms
- no-op protection when effects would not change state
- subgoal creation only when missing preconditions exist
- proposal failure becomes an impasse

Optimization ideas:
- This overlaps heavily with `MakingCoffeeWithSoar.py`.
- Shared planner logic should be extracted once and reused by both files.

Keep/cut guidance:
- **Keep only if it becomes the shared planner core**.
- If not consolidating, this is the first large SOAR file I would consider cutting because the more feature-rich coffee file already re-implements most of it.

### SOAR cut summary

Best trim path:
- Keep `soar_rule_library.py`
- Keep `soar_scenario_tests.py`
- Keep **one** planner core
- Remove or merge the duplicated planner code from either `MakingCoffeeWithSoar.py` or `SoarGeneral.py`

If you want the smallest clean set:
- keep `SoarGeneral.py` as engine
- move coffee-specific object classes/world builders into a much smaller domain file
- keep tests and rule bundles

If you want the most complete demo:
- keep `MakingCoffeeWithSoar.py`
- cut or archive `SoarGeneral.py`

## 3. Utility Experimentation

### `ProbabilityCostTesting.py`

What it does:
- Small Monte Carlo scratch script for a budget/probability process.

How it works:
- Repeats 1000 trials.
- In each trial, budget accumulates.
- Budget can trigger a forced event when it exceeds `hyperParameter * 1/p`.
- A random event can also fire with probability `p`.
- Results are plotted as a histogram.

Guard count:
- **3 branch guards**
- forced-spend guard: `budget > hyperParameter * 1/p`
- random-event guard: `random.random() < p`
- affordability guard: `budget > 0`

Optimization ideas:
- Convert to functions if you want to keep it.
- Right now it is not reusable, not tested, and not connected to the rest of the repo.

Keep/cut guidance:
- **Cut first unless this exact budget test is still useful**.

### `PureUtilityExperiment.py`

What it does:
- Simulates a simple agent choosing actions by predicted utility impact.

How it works:
- Utilities are `food`, `energy`, `fun`, plus `money`.
- Each step scores all actions against predicted post-decay state.
- Score is mostly negative weighted deficit pressure, with extra value for money when it unlocks future restorative actions.
- Best-scoring action is applied with noise.
- Reports final state, averages, critical counts, and action counts.

Guard count:
- **8 branch guards**

Main semantic guards:
- reject actions that would make money negative
- only count unlock bonus when a future action is currently unaffordable but would become affordable
- only credit unlock value for utilities below `UNLOCK_THRESHOLD`
- critical-state counting uses `CRITICAL_THRESHOLD`
- verbose mode controls per-step trace output

Optimization ideas:
- Good small experiment.
- `score_action` loops through all actions to estimate unlock bonus on every scoring call; still fine at this scale.
- If expanded, separate policy scoring from simulation/reporting.

Keep/cut guidance:
- **Keep**. Small, readable, and non-duplicated.

## Guard Count Summary

| File | Branch guards | Main semantic guards |
| --- | ---: | --- |
| `CiF/chatbotTesting.py` | 2 | init/speaker branching only |
| `CiF/cif_content.py` | 29 | 9 exchange preconditions, 72 influence rules, 5 trigger guards |
| `CiF/cif_engine.py` | 14 | exchange precondition filtering, no-self exchange, accept/reject threshold |
| `CiF/cif_situations.py` | 0 | scenario-enabled exchanges and turn limits |
| `CiF/run_cif_experiments.py` | 7 | CLI mode/output guards |
| `CiF/test_cif_experiments.py` | 2 | test-only checks |
| `SOAR Experiments/MakingCoffeeWithSoar.py` | 98 | 18 proposal rules, 42 proposal atoms, 11 action rules, 20 action preconditions |
| `SOAR Experiments/soar_rule_library.py` | 2 | bundle selection and generated rule guards |
| `SOAR Experiments/soar_scenario_tests.py` | 20 | scenario validation guards |
| `SOAR Experiments/SoarGeneral.py` | 64 | generic rule/planner/utility gating |
| `Utility Experimentation/ProbabilityCostTesting.py` | 3 | threshold / chance / affordability |
| `Utility Experimentation/PureUtilityExperiment.py` | 8 | affordability, unlock, threshold, verbose guards |

## What To Cut When It Is Time

### Cut first

1. `Experiments/CiF/chatbotTesting.py`
2. `Experiments/Utility Experimentation/ProbabilityCostTesting.py`
3. One of the two large SOAR engines after consolidation:
   - `Experiments/SOAR Experiments/MakingCoffeeWithSoar.py`
   - `Experiments/SOAR Experiments/SoarGeneral.py`

### Keep longest

1. `Experiments/CiF/cif_content.py`
2. `Experiments/CiF/cif_engine.py`
3. `Experiments/CiF/cif_situations.py`
4. `Experiments/CiF/test_cif_experiments.py`
5. `Experiments/SOAR Experiments/soar_rule_library.py`
6. `Experiments/SOAR Experiments/soar_scenario_tests.py`
7. `Experiments/Utility Experimentation/PureUtilityExperiment.py`

### If you want one sentence of pruning advice

The cleanest reduction is: **delete the scratch scripts, keep CiF, keep the SOAR rule bundles/tests, and merge the two SOAR engines down to one**.
