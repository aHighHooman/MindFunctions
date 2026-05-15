from typed_rule_engine import (
    ME,
    WORLD,
    ActionSchema,
    AddToSet,
    GoalIs,
    Has,
    Name,
    ProposalRule,
    RevealFromContainer,
    SetState,
    StateContains,
    StateIs,
    Tag,
    Transfer,
    Var,
)


def bundle(proposals, actions):
    return {
        "proposal_rules": list(proposals),
        "action_rules": list(actions),
    }


def as_selector(value):
    if isinstance(value, (Name, Tag, Var)):
        return value
    raise TypeError(f"Expected Name, Tag, or Var selector, got: {value!r}")


def goal_proposal(name, goal, proposed_action, *conditions, priority=0):
    return ProposalRule(name, [GoalIs(goal), *conditions], proposed_action, priority)


def grab_rule(item_selector, action_name=None, param_name="item"):
    item_selector = as_selector(item_selector)
    action_name = action_name or f"Action_Grab_{selector_label(item_selector)}"
    return ActionSchema(
        name=action_name,
        params={param_name: item_selector},
        preconditions=[Has(WORLD, Var(param_name))],
        effects=[Transfer(Var(param_name), source=WORLD, target=ME)],
    )


def retrieve_rule(name, item_selector, container_selector):
    item_selector = as_selector(item_selector)
    container_selector = as_selector(container_selector)
    return ActionSchema(
        name=name,
        params={},
        preconditions=[Has(WORLD, container_selector)],
        effects=[RevealFromContainer(item_selector, container=container_selector, target=WORLD)],
    )


def selector_label(selector):
    if isinstance(selector, Name):
        return selector.value
    raise TypeError(f"Default action names require Name selectors, got: {selector!r}")


def build_coffee_goal():
    return StateContains(ME, "drank", "Coffee")


def build_coffee_rule_bundle():
    drink_vessel = Tag("Drink_Vessel")
    fluid_transformer = Tag("Fluid_Transformer")
    hot_water_provider = Tag("Provides_Hot_Water")
    water_dispenser = Tag("Dispenses_Water")
    container = Tag("Container")
    coffee_box = Name("CoffeeBox")

    drink_coffee_goal = build_coffee_goal()
    vessel_has_coffee = StateIs(drink_vessel, "has", "Coffee")
    vessel_has_hot_water = StateIs(drink_vessel, "has", "Hot_Water")
    kettle_has_hot_water = StateIs(fluid_transformer, "has", "Hot_Water")
    kettle_has_water = StateIs(fluid_transformer, "has", "Water")
    provider_has_hot_water = StateIs(hot_water_provider, "has", "Hot_Water")

    return bundle(
        proposals=[
            goal_proposal("Proposal_Drink_Coffee", drink_coffee_goal, "Action_Drink_Coffee"),
            goal_proposal("Proposal_Mix_Coffee_And_Water", vessel_has_coffee, "Action_Mix_Coffee_And_Water"),
            goal_proposal("Proposal_Grab_CoffeeBox", Has(ME, coffee_box), "Action_Grab_CoffeeBox"),
            goal_proposal("Proposal_Grab_Drink_Vessel", Has(ME, drink_vessel), "Action_Grab_Drink_Vessel"),
            goal_proposal("Proposal_Check_Cupboard_1", Has(WORLD, coffee_box), "Action_Check_Cupboard_1", Has(WORLD, container)),
            goal_proposal("Proposal_Check_Cupboard_2", Has(WORLD, drink_vessel), "Action_Check_Cupboard_2", Has(WORLD, container)),
            goal_proposal("Proposal_Fill_Mug_Hot_Water", vessel_has_hot_water, "Action_Fill_Mug_Hot_Water", Has(WORLD, hot_water_provider)),
            goal_proposal("Proposal_Boil_Water", kettle_has_hot_water, "Action_Boil_Water", Has(WORLD, fluid_transformer)),
            goal_proposal("Proposal_Boil_Water_From_Hot_Water_Provider_Goal", provider_has_hot_water, "Action_Boil_Water", Has(WORLD, fluid_transformer)),
            goal_proposal("Proposal_Fill_Kettle_Water", kettle_has_water, "Action_Fill_Kettle_Water", Has(WORLD, water_dispenser)),
        ],
        actions=[
            ActionSchema(
                "Action_Drink_Coffee",
                {"vessel": drink_vessel},
                [Has(ME, Var("vessel")), StateIs(Var("vessel"), "has", "Coffee")],
                [AddToSet(ME, "drank", "Coffee")],
            ),
            ActionSchema(
                "Action_Mix_Coffee_And_Water",
                {"vessel": drink_vessel},
                [Has(ME, coffee_box), Has(ME, Var("vessel")), StateIs(Var("vessel"), "has", "Hot_Water")],
                [SetState(Var("vessel"), "has", "Coffee")],
            ),
            grab_rule(coffee_box),
            grab_rule(drink_vessel, "Action_Grab_Drink_Vessel", "vessel"),
            retrieve_rule("Action_Check_Cupboard_1", coffee_box, container),
            retrieve_rule("Action_Check_Cupboard_2", drink_vessel, container),
            ActionSchema(
                "Action_Fill_Mug_Hot_Water",
                {"provider": hot_water_provider, "vessel": drink_vessel},
                [Has(WORLD, Var("provider")), StateIs(Var("provider"), "has", "Hot_Water"), Has(ME, Var("vessel"))],
                [SetState(Var("vessel"), "has", "Hot_Water")],
            ),
            ActionSchema(
                "Action_Boil_Water",
                {"kettle": fluid_transformer},
                [Has(WORLD, Var("kettle")), StateIs(Var("kettle"), "has", "Water")],
                [SetState(Var("kettle"), "has", "Hot_Water")],
            ),
            ActionSchema(
                "Action_Fill_Kettle_Water",
                {"source": water_dispenser, "kettle": fluid_transformer},
                [Has(WORLD, Var("source")), Has(WORLD, Var("kettle"))],
                [SetState(Var("kettle"), "has", "Water")],
            ),
        ],
    )
