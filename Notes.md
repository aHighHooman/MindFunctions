# NPC Loop
- Environment
- State Update 
- State
- Action 

# NPC Axioms
- Reactive to State and Environment
- Generally Active

## Environment(Action.ActionMessage) -> StateUpdate.{ActionMessage,Persons} , Action.???
- Triggered by the **Action Block**
    - The Broadcast Function

- TBD (Processing)

- Triggers the **Status Update Block**
    - The ProcessBroadcast Function



## StateUpdate(State.StateVectors , Environment.{ActionMessage,Persons}) -> State.StateVectors
- Triggered by the **Environment Block**
    - The ProcessBroadcast Function

- Transforms the State Vectors based on given information

- Triggers the **State Block**
    - How?



## State(StateUpdate.StateVectors) -> StateUpdate.StateVectors, Action.DiscretizedStates
- Triggered by the **State Update Block**
    - How?

- Converts vectors into discrete states (i.e. Mood/Emotion or Relationship State)
- Combines vectors/states into compound states

- Triggers the **Action Block** 
    - How?

### Architecture (in Flux)
- Separated into 2 primary types: Mental | Physical
- Separated into 2 secondary types: Visible | Invisible

#### Mental 
- Emotional State       [Visible] 
- Human Relationships   [Invisible]
- TBD

#### Physical 
- Appearance                [Visible]
    - Intrinsic 
        - Scars
    - Extrinsic 
        - Clothing
- Strength - Fitness Vector [Invisible]
    - This will affect the **Intrinic Appearance** but isn't directly apparent
        - What does this mean?
- TBD



## Action(Environment.??? , State.DiscretizedStates) -> Environment.ActionMessage 
 - Triggered by the State Block 
    - How

 - Chooses an action to do based on action choices and current state

 - Triggers the **Environment Block**
    - Using the Broadcast function
