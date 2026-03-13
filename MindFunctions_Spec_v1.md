# MindFunctions Spec v1
**Portable Cognitive Architecture for Embodied, Emotional, Goal-Directed Agents**

## 1. Purpose

MindFunctions is a portable agent architecture intended to support NPCs or autonomous agents that can be placed into different environments and interact with them through a shared internal cognitive structure.

The system is meant to support:

- goal-directed problem solving
- emotional modulation of behavior
- social relationships and memory
- physical constraints and capabilities
- portability across worlds through adapters rather than rewriting the mind each time

The architecture is not intended to hardcode a single game’s rules.  
It is intended to provide a reusable internal agent model that can operate in many domains once connected to a domain/world interface.

## 2. Core Design Principles

### 2.1 Portability
The core mind should remain mostly unchanged across worlds.  
Different environments should mainly require changes in world adapters and domain knowledge.

### 2.2 Embodiment
The agent does not act directly on the world.  
It acts through a body with capabilities, limits, and costs.

### 2.3 Emotional Modulation
Emotion is not cosmetic.  
It changes decision-making, attention, interpretation, and action bias.

### 2.4 Layer Separation
The architecture must clearly separate:

- core cognition
- emotion
- body
- world interface
- domain knowledge

### 2.5 Incremental Generalization
Abstractions should only become part of the core architecture after they survive use across multiple working environments.

## 3. System Scope

The architecture aims to support three broad classes of tasks:

### 3.1 Physical / object interaction
Examples:
- making coffee
- finding tools
- opening containers
- moving objects
- transforming resources

### 3.2 Social interaction
Examples:
- talking
- joking
- insulting
- complimenting
- building trust
- changing relationship state

### 3.3 Survival / utility behavior
Examples:
- navigation
- avoiding danger
- managing stamina
- fulfilling needs
- prioritizing urgent goals

## 4. High-Level Architecture

The system consists of five major modules:

1. **Mind Core**
2. **Emotion System**
3. **Body System**
4. **World Adapter**
5. **Domain Knowledge**

## 5. Module Specifications

# 5.1 Mind Core

## Purpose
The Mind Core is the domain-general reasoning system responsible for selecting and organizing behavior.

## Responsibilities
- maintain goals
- maintain beliefs / working memory
- select operators/actions
- detect impasses
- create subgoals
- track active intentions
- integrate inputs from emotion, memory, and body
- produce high-level action intents

## Inputs
- perceived world state from World Adapter
- body state from Body System
- emotional state from Emotion System
- memories from Memory subsystem
- current goals and active context

## Outputs
- selected operator/action intent
- subgoal creation
- updates to working memory
- requests for information gathering
- requests for body/world actions

## Internal Subsystems

### 5.1.1 Goal Manager
Tracks:
- persistent goals
- active goals
- subgoals
- completed goals
- failed goals

Each goal should have:
- identifier
- type
- priority
- source
- status
- parent goal if it is a subgoal
- optional deadline/urgency
- optional emotional weight

### 5.1.2 Working Memory
Holds current task-relevant information such as:
- observed objects
- inferred object states
- active relationships
- current location
- selected plan fragments
- pending preconditions
- active threats/opportunities

### 5.1.3 Operator Selector
Chooses among possible actions using:
- current goal
- preconditions
- expected outcomes
- emotional bias
- body constraints
- world constraints

### 5.1.4 Impasse / Subgoal Generator
When a selected operator cannot proceed, the system:
- identifies missing preconditions
- creates subgoals to satisfy them
- retries once relevant beliefs are updated

This is where your SOAR-style logic fits very naturally.

### 5.1.5 Deliberation Policy
Controls whether the agent:
- reacts immediately
- plans briefly
- explores
- pauses
- asks for more information internally

This should be influenced by urgency, uncertainty, and emotion.

# 5.2 Emotion System

## Purpose
The Emotion System modulates cognition and behavior based on internal and external conditions.

## Responsibilities
- maintain emotional state variables
- interpret emotionally relevant events
- bias attention and decision-making
- affect social interpretation
- affect memory salience
- alter persistence, risk tolerance, and action preferences

## Design Rule
Emotion should usually modify cognition, not replace it.

## Core Emotional Variables
Initial recommended set:

- joy
- frustration
- fear / wariness
- anger
- attachment
- attraction
- shame / embarrassment
- curiosity

Not all need to exist in v1, but the architecture should support arbitrary emotional dimensions.

## Emotional Effects
Examples:

- **fear / wariness**
  - increases threat salience
  - biases toward safe operators
  - reduces risky exploration

- **joy / contentment**
  - lowers defensive bias
  - increases social openness
  - reduces urgency for further reward-seeking

- **frustration**
  - increases operator switching
  - reduces patience
  - may increase aggressive or shortcut choices

- **attachment / trust**
  - alters interpretation of another agent’s actions
  - changes social willingness and cooperation thresholds

## Inputs
- interpreted events
- social outcomes
- body condition
- goal success/failure
- memory retrieval cues

## Outputs
- emotional state update
- modulation signals to Mind Core
- salience signals to Memory
- social bias signals

# 5.3 Body System

## Purpose
The Body System represents the agent’s means of perceiving and acting in the environment.

## Responsibilities
- define available actions/capabilities
- define physical limits
- track internal physiological state
- report action costs and constraints
- mediate perception and execution

## Key Idea
The body is not decoration.  
It determines what the mind can actually do.

## Components

### 5.3.1 Capability Model
Examples:
- can_move
- can_pick_up
- can_speak
- can_see
- can_hear
- can_open_container
- can_use_tool

### 5.3.2 Physiological State
Examples:
- energy
- fatigue
- hunger
- pain
- injury
- mobility
- posture
- temperature tolerance

### 5.3.3 Physical Traits
Examples:
- strength
- dexterity
- speed
- reach
- voice clarity
- appearance
- attractiveness-related visible features

These may matter for both action execution and social interpretation.

## Inputs
- commands from Mind Core
- world feedback via adapter

## Outputs
- executable action set
- current constraints
- action success/failure modifiers
- updated body state

# 5.4 World Adapter

## Purpose
The World Adapter is the translation layer between the portable internal architecture and a specific environment.

## Responsibilities
- convert environment observations into internal representations
- convert internal action intents into environment-specific commands
- expose available entities, affordances, and events
- manage synchronization between world state and working memory

## Why This Matters
This is the main mechanism that makes the architecture portable.

The Mind Core should not need to know whether the world is:
- a Python simulation
- a 2D game
- a 3D Unity scene
- a text world
- a grid world

## Inputs
- raw environment state / events / sensory data
- action intents from Mind Core

## Outputs
- normalized observations
- normalized world events
- action execution requests to environment
- execution results back to the agent

## Adapter Duties

### 5.4.1 Observation Translation
Example:
- Unity object with component tags -> internal object with tags, states, affordances

### 5.4.2 Action Translation
Example:
- internal action `Open(Container_2)` -> engine-specific interaction call

### 5.4.3 Affordance Exposure
Example:
- object has tags like `Container`, `Openable`, `Provides_Water`

### 5.4.4 Event Packaging
Example:
- “Bob insulted Alice in public”
- “Kettle now contains hot water”
- “Path to sink blocked”

# 5.5 Domain Knowledge

## Purpose
Domain Knowledge stores environment-specific concepts and rules that are not part of the general mind.

## Responsibilities
- define object categories
- define affordances
- define action schemas
- define state predicates
- define social norms if relevant
- define domain-specific causal knowledge

## Examples

### Coffee world
- kettles transform water to hot water
- mugs hold liquids
- cupboards may contain objects

### Social world
- insults reduce like/trust
- jokes can improve mood depending on context
- flirting depends on attraction, trust, and setting

## Important Rule
Domain knowledge may change between worlds; core cognition should not.

## 6. Memory Specification

Memory should be its own subsystem, even if lightweight in v1.

## Types of Memory

### 6.1 Working Memory
Short-term active state used for current reasoning.

### 6.2 Episodic Memory
Stores specific events:
- what happened
- who was involved
- when
- outcome
- emotional weight

### 6.3 Semantic Memory
Stores general learned facts:
- mugs hold liquids
- Alice is trustworthy
- this door is usually locked

### 6.4 Social Memory
Stores relationship-relevant history:
- prior interactions
- trust violations
- positive bonding events
- repeated patterns

## Memory Effects
Memory should influence:
- future operator selection
- social expectations
- emotional priming
- prioritization
- learned heuristics

## 7. Agent Loop

This should be the standard control loop.

### 7.1 Perceive
Receive environment observations through adapter.

### 7.2 Interpret
Convert observations into internal events, beliefs, affordances, and candidate updates.

### 7.3 Update Body
Apply body-state changes caused by time, actions, or environment.

### 7.4 Update Emotion
Evaluate emotional impact of events, failures, successes, and social outcomes.

### 7.5 Update Memory
Store salient events and retrieve relevant past experiences.

### 7.6 Deliberate
Evaluate goals, select operators, handle impasses, and possibly generate subgoals.

### 7.7 Act
Send action intent through body and world adapter.

### 7.8 Observe Result
Receive success/failure/outcome and repeat.

Compactly:

**Perceive -> Interpret -> Update Body -> Update Emotion -> Update Memory -> Deliberate -> Act -> Observe Result**

## 8. Internal Representation Format

The architecture should use normalized internal representations.

### 8.1 Entities
Each entity should have:
- unique id
- type
- tags
- visible properties
- hidden/inferred properties if known
- relation to self

### 8.2 Predicates / State Atoms
Examples:
- `Has(Me, Mug)`
- `Contains(Kettle, Water)`
- `Open(Cupboard)`
- `Trust(Me, Bob) = 42`
- `Emotion(Me, Wariness) = 60`

### 8.3 Action Intents
Examples:
- `PickUp(Mug)`
- `Open(Cupboard)`
- `Speak(Bob, Joke.Friendly)`
- `MoveTo(Sink)`

These are internal intents; the world adapter decides how to execute them in the target environment.

## 9. Social System Specification

## Purpose
Support relationships and socially influenced decision-making.

## Core Variables
Per agent-pair:
- familiarity
- trust
- like
- respect
- attraction
- fear
- resentment

## Social Effects
These should influence:
- interpretation of others’ actions
- what actions are considered appropriate
- willingness to cooperate
- willingness to flirt, joke, insult, forgive, or assist

## Rule
Social state must update through interaction history, not only static presets.

## 10. Planning Model

The architecture should support hybrid planning:

### 10.1 Reactive control
For urgent or simple situations.

### 10.2 Rule/operator-based control
For structured action selection.

### 10.3 Subgoal generation
For failed preconditions and impasses.

### 10.4 Learned heuristics
Optional future layer for improving efficiency.

For now, SOAR-style operator selection with subgoaling is a good backbone.

## 11. Success Criteria for v1

v1 is successful if the same core architecture can function in at least three different domains with mostly unchanged Mind Core:

1. object interaction domain
2. social interaction domain
3. navigation/resource domain

The following may change per domain:
- world adapter
- domain knowledge
- object/action vocabulary

The following should remain mostly stable:
- goal handling
- working memory
- operator selection
- impasse/subgoal logic
- emotion-body-memory integration pattern

## 12. Non-Goals for v1

To keep scope sane, v1 should **not** attempt to solve:

- general intelligence
- unrestricted language understanding
- human-level psychology
- full realism of social behavior
- fully learned end-to-end cognition
- universal transfer across arbitrary worlds

v1 is about a reusable architecture, not a complete synthetic mind.

## 13. Proposed Codebase Structure

Here’s the repo structure I’d recommend:

```text
mindfunctions/
    core/
        agent.py
        goal_manager.py
        working_memory.py
        operator_selector.py
        planner.py
        state_representation.py

    emotion/
        emotion_system.py
        appraisal.py
        emotion_state.py

    body/
        body.py
        capabilities.py
        physiology.py

    memory/
        working_memory.py
        episodic_memory.py
        semantic_memory.py
        social_memory.py

    social/
        relationships.py
        social_rules.py

    adapters/
        base_adapter.py
        coffee_adapter.py
        social_adapter.py
        navigation_adapter.py

    domains/
        coffee_world/
            objects.py
            actions.py
            rules.py
        social_world/
            actions.py
            rules.py
        navigation_world/
            actions.py
            rules.py

    experiments/
        coffee_demo.py
        social_demo.py
        navigation_demo.py

    tests/
        test_goals.py
        test_subgoals.py
        test_emotion_modulation.py
        test_adapter_translation.py
```

## 14. Immediate Implementation Priorities

Order I’d recommend:

### Phase 1
- formalize internal state representation
- isolate goal/subgoal mechanism
- define base world adapter interface
- clean up coffee world as benchmark domain

### Phase 2
- add body-state constraints
- add simple emotion modulation
- add episodic/social memory hooks

### Phase 3
- build social benchmark world
- verify same core works there

### Phase 4
- build third benchmark world
- extract only abstractions that survive all three

## 15. One-sentence project definition

**MindFunctions is a portable cognitive architecture for embodied agents that combines goal-directed reasoning, emotional modulation, body constraints, and world adapters to support reusable behavior across different environments.**
