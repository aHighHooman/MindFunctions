## Locations
- House with multiple rooms + crafting room
- Village with shops and house

## Tests
### Search/Retrieval
- Find [Object X] in current location
- Find [Object X] in current region
- Get  [Object X] in current location 
    - One object will be visible but not accessible the other will be accessible but will need to discover
- Implemented first-pass scenarios:
  - `search_local_visible`
  - `search_local_hidden`
  - `search_remote_location`

### Crafting
- Craft [Object X] with N stages but few inputs
- Craft [Object X] with few stages but N inputs
- Craft [Object X] with N stages and N inputs
- Implemented first-pass scenarios:
  - `craft_one_stage_two_inputs`
  - `craft_two_stage_three_inputs`
  - `craft_three_stage_four_inputs`

### Interruptions
- Work on [Goal X]; switch to [Goal Y] mid-process
- Work on [Goal X]; be able to adapt if environment changes or acts unusually (being unable to get an item)

### Impossible Tasks
- Be able to "give up" if either 1) enough work is spent on the goal without success or 2) No apparent way to solve the issue or 3) The subgoal costs more than the goal is worth

### Learning
- Craft an [Object X] N times and proceed to optimize task
- Find an [Object X] N times and proceed to optimize tasks

### Final Benchmarks
- Craft [Object X] with N stages and N inputs, however the inputs are not visible
- More to come
