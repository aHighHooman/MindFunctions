def build_coffee_rule_bundle():
    drink_vessel = "tag:Drink_Vessel"
    fluid_transformer = "tag:Fluid_Transformer"
    hot_water_provider = "tag:Provides_Hot_Water"
    water_dispenser = "tag:Dispenses_Water"
    container = "tag:Container"

    return {
        "proposal_rules": [
            {
                "name": "Proposal_Drink_Coffee",
                "conditions": [("goal", ("Me", "drank", "Coffee"))],
                "proposed_action": "Action_Drink_Coffee",
            },
            {
                "name": "Proposal_Mix_Coffee_And_Water",
                "conditions": [("goal", (drink_vessel, "has", "Coffee"))],
                "proposed_action": "Action_Mix_Coffee_And_Water",
            },
            {
                "name": "Proposal_Grab_CoffeeBox",
                "conditions": [("goal", ("Me", "has", "CoffeeBox"))],
                "proposed_action": "Action_Grab_CoffeeBox",
            },
            {
                "name": "Proposal_Grab_Drink_Vessel",
                "conditions": [("goal", ("Me", "has", drink_vessel))],
                "proposed_action": "Action_Grab_Drink_Vessel",
            },
            {
                "name": "Proposal_Check_Cupboard_1",
                "conditions": [("goal", ("World", "has", "CoffeeBox")), ("World", "has", container), (container, "is_open", False)],
                "proposed_action": "Action_Check_Cupboard_1",
            },
            {
                "name": "Proposal_Check_Cupboard_2",
                "conditions": [("goal", ("World", "has", drink_vessel)), ("World", "has", container), (container, "is_open", False)],
                "proposed_action": "Action_Check_Cupboard_2",
            },
            {
                "name": "Proposal_Fill_Mug_Hot_Water",
                "conditions": [("goal", (drink_vessel, "has", "Hot_Water")), ("World", "has", hot_water_provider)],
                "proposed_action": "Action_Fill_Mug_Hot_Water",
            },
            {
                "name": "Proposal_Boil_Water",
                "conditions": [("goal", (fluid_transformer, "has", "Hot_Water")), ("World", "has", fluid_transformer)],
                "proposed_action": "Action_Boil_Water",
            },
            {
                "name": "Proposal_Boil_Water_From_Hot_Water_Provider_Goal",
                "conditions": [("goal", (hot_water_provider, "has", "Hot_Water")), ("World", "has", fluid_transformer)],
                "proposed_action": "Action_Boil_Water",
            },
            {
                "name": "Proposal_Fill_Kettle_Water",
                "conditions": [("goal", (fluid_transformer, "has", "Water")), ("World", "has", water_dispenser)],
                "proposed_action": "Action_Fill_Kettle_Water",
            },
        ],
        "action_rules": [
            {
                "name": "Action_Drink_Coffee",
                "preconditions": [("Me", "has", drink_vessel), (drink_vessel, "has", "Coffee")],
                "effects": [("Me", "drank", "Coffee")],
            },
            {
                "name": "Action_Mix_Coffee_And_Water",
                "preconditions": [("Me", "has", "CoffeeBox"), ("Me", "has", drink_vessel), (drink_vessel, "has", "Hot_Water")],
                "effects": [(drink_vessel, "has", "Coffee")],
            },
            {
                "name": "Action_Grab_CoffeeBox",
                "preconditions": [("World", "has", "CoffeeBox")],
                "effects": [("Me", "has", "CoffeeBox")],
            },
            {
                "name": "Action_Grab_Drink_Vessel",
                "preconditions": [("World", "has", drink_vessel)],
                "effects": [("Me", "has", drink_vessel)],
            },
            {
                "name": "Action_Check_Cupboard_1",
                "preconditions": [("World", "has", container), (container, "is_open", False)],
                "effects": [(container, "is_open", True)],
            },
            {
                "name": "Action_Check_Cupboard_2",
                "preconditions": [("World", "has", container), (container, "is_open", False)],
                "effects": [(container, "is_open", True)],
            },
            {
                "name": "Action_Fill_Mug_Hot_Water",
                "preconditions": [("World", "has", hot_water_provider), (hot_water_provider, "has", "Hot_Water"), ("Me", "has", drink_vessel)],
                "effects": [(drink_vessel, "has", "Hot_Water")],
            },
            {
                "name": "Action_Boil_Water",
                "preconditions": [("World", "has", fluid_transformer), (fluid_transformer, "has", "Water")],
                "effects": [(fluid_transformer, "has", "Hot_Water")],
            },
            {
                "name": "Action_Fill_Kettle_Water",
                "preconditions": [("World", "has", water_dispenser), ("World", "has", fluid_transformer)],
                "effects": [(fluid_transformer, "has", "Water")],
            },
        ],
    }


def build_coffee_village_rule_bundle():
    drink_vessel = "tag:Drink_Vessel"
    fluid_transformer = "tag:Fluid_Transformer"
    hot_water_provider = "tag:Provides_Hot_Water"
    water_dispenser = "tag:Dispenses_Water"
    container = "tag:Container"

    return {
        "proposal_rules": [
            {
                "name": "Proposal_Drink_Coffee",
                "conditions": [("goal", ("Me", "drank", "Coffee"))],
                "proposed_action": "Action_Drink_Coffee",
            },
            {
                "name": "Proposal_Go_To_Village_For_CoffeeBox",
                "conditions": [("goal", ("Me", "has", "CoffeeBox")), ("Me", "NOT_at", "Village"), ("Village", "has", "tag:Provides_CoffeeBox")],
                "proposed_action": "Action_Go_To_Village",
            },
            {
                "name": "Proposal_Go_To_Village_For_World_CoffeeBox",
                "conditions": [("goal", ("World", "has", "CoffeeBox")), ("Me", "NOT_at", "Village"), ("Village", "has", "tag:Provides_CoffeeBox")],
                "proposed_action": "Action_Go_To_Village",
            },
            {
                "name": "Proposal_Go_To_House_For_Drink_Vessel",
                "conditions": [("goal", ("Me", "has", drink_vessel)), ("Me", "NOT_at", "House"), ("House", "has", drink_vessel)],
                "proposed_action": "Action_Go_To_House",
            },
            {
                "name": "Proposal_Go_To_House_For_World_Drink_Vessel",
                "conditions": [("goal", ("World", "has", drink_vessel)), ("Me", "NOT_at", "House"), ("House", "has", drink_vessel)],
                "proposed_action": "Action_Go_To_House",
            },
            {
                "name": "Proposal_Go_To_House_For_Hot_Water",
                "conditions": [("goal", (drink_vessel, "has", "Hot_Water")), ("Me", "NOT_at", "House"), ("House", "has", hot_water_provider)],
                "proposed_action": "Action_Go_To_House",
            },
            {
                "name": "Proposal_Go_To_House_For_Boil_Water",
                "conditions": [("goal", (fluid_transformer, "has", "Hot_Water")), ("Me", "NOT_at", "House"), ("House", "has", fluid_transformer)],
                "proposed_action": "Action_Go_To_House",
            },
            {
                "name": "Proposal_Go_To_House_For_Hot_Water_Provider_Goal",
                "conditions": [("goal", (hot_water_provider, "has", "Hot_Water")), ("Me", "NOT_at", "House"), ("House", "has", fluid_transformer)],
                "proposed_action": "Action_Go_To_House",
            },
            {
                "name": "Proposal_Go_To_House_For_Water",
                "conditions": [("goal", (fluid_transformer, "has", "Water")), ("Me", "NOT_at", "House"), ("House", "has", water_dispenser)],
                "proposed_action": "Action_Go_To_House",
            },
            {
                "name": "Proposal_Mix_Coffee_And_Water",
                "conditions": [("goal", (drink_vessel, "has", "Coffee"))],
                "proposed_action": "Action_Mix_Coffee_And_Water",
            },
            {
                "name": "Proposal_Grab_CoffeeBox",
                "conditions": [("goal", ("Me", "has", "CoffeeBox"))],
                "proposed_action": "Action_Grab_CoffeeBox",
            },
            {
                "name": "Proposal_Grab_Drink_Vessel",
                "conditions": [("goal", ("Me", "has", drink_vessel))],
                "proposed_action": "Action_Grab_Drink_Vessel",
            },
            {
                "name": "Proposal_Check_Cupboard_1",
                "conditions": [("goal", ("World", "has", "CoffeeBox")), ("World", "has", container), (container, "is_open", False)],
                "proposed_action": "Action_Check_Cupboard_1",
            },
            {
                "name": "Proposal_Check_Cupboard_2",
                "conditions": [("goal", ("World", "has", drink_vessel)), ("World", "has", container), (container, "is_open", False)],
                "proposed_action": "Action_Check_Cupboard_2",
            },
            {
                "name": "Proposal_Fill_Mug_Hot_Water",
                "conditions": [("goal", (drink_vessel, "has", "Hot_Water")), ("World", "has", hot_water_provider)],
                "proposed_action": "Action_Fill_Mug_Hot_Water",
            },
            {
                "name": "Proposal_Boil_Water",
                "conditions": [("goal", (fluid_transformer, "has", "Hot_Water")), ("World", "has", fluid_transformer)],
                "proposed_action": "Action_Boil_Water",
            },
            {
                "name": "Proposal_Boil_Water_From_Hot_Water_Provider_Goal",
                "conditions": [("goal", (hot_water_provider, "has", "Hot_Water")), ("World", "has", fluid_transformer)],
                "proposed_action": "Action_Boil_Water",
            },
            {
                "name": "Proposal_Fill_Kettle_Water",
                "conditions": [("goal", (fluid_transformer, "has", "Water")), ("World", "has", water_dispenser)],
                "proposed_action": "Action_Fill_Kettle_Water",
            },
        ],
        "action_rules": [
            {
                "name": "Action_Go_To_Village",
                "preconditions": [("Me", "NOT_at", "Village")],
                "effects": [("Me", "at", "Village")],
            },
            {
                "name": "Action_Go_To_House",
                "preconditions": [("Me", "NOT_at", "House")],
                "effects": [("Me", "at", "House")],
            },
            {
                "name": "Action_Drink_Coffee",
                "preconditions": [("Me", "has", drink_vessel), (drink_vessel, "has", "Coffee")],
                "effects": [("Me", "drank", "Coffee")],
            },
            {
                "name": "Action_Mix_Coffee_And_Water",
                "preconditions": [("Me", "has", "CoffeeBox"), ("Me", "has", drink_vessel), (drink_vessel, "has", "Hot_Water")],
                "effects": [(drink_vessel, "has", "Coffee")],
            },
            {
                "name": "Action_Grab_CoffeeBox",
                "preconditions": [("World", "has", "CoffeeBox")],
                "effects": [("Me", "has", "CoffeeBox")],
            },
            {
                "name": "Action_Grab_Drink_Vessel",
                "preconditions": [("World", "has", drink_vessel)],
                "effects": [("Me", "has", drink_vessel)],
            },
            {
                "name": "Action_Check_Cupboard_1",
                "preconditions": [("World", "has", container), (container, "is_open", False)],
                "effects": [(container, "is_open", True)],
            },
            {
                "name": "Action_Check_Cupboard_2",
                "preconditions": [("World", "has", container), (container, "is_open", False)],
                "effects": [(container, "is_open", True)],
            },
            {
                "name": "Action_Fill_Mug_Hot_Water",
                "preconditions": [("World", "has", hot_water_provider), (hot_water_provider, "has", "Hot_Water"), ("Me", "has", drink_vessel)],
                "effects": [(drink_vessel, "has", "Hot_Water")],
            },
            {
                "name": "Action_Boil_Water",
                "preconditions": [("World", "has", fluid_transformer), (fluid_transformer, "has", "Water")],
                "effects": [(fluid_transformer, "has", "Hot_Water")],
            },
            {
                "name": "Action_Fill_Kettle_Water",
                "preconditions": [("World", "has", water_dispenser), ("World", "has", fluid_transformer)],
                "effects": [(fluid_transformer, "has", "Water")],
            },
        ],
    }


def build_search_retrieval_rule_bundle(*, target_name, target_location="House", container_ref="tag:Container"):
    travel_action = f"Action_Go_To_{target_location}"

    return {
        "proposal_rules": [
            {
                "name": f"Proposal_Grab_{target_name}",
                "conditions": [("goal", ("Me", "has", target_name)), ("World", "has", target_name)],
                "proposed_action": f"Action_Grab_{target_name}",
            },
            {
                "name": f"Proposal_Go_To_{target_location}_For_{target_name}",
                "conditions": [("goal", ("Me", "has", target_name)), ("Me", "NOT_at", target_location), (target_location, "has", target_name)],
                "proposed_action": travel_action,
            },
            {
                "name": f"Proposal_Open_Container_For_{target_name}",
                "conditions": [("goal", ("Me", "has", target_name)), ("Me", "at", target_location), ("World", "NOT_has", target_name), ("World", "has", container_ref), (container_ref, "is_open", False)],
                "proposed_action": "Action_Check_Container",
            },
        ],
        "action_rules": [
            {
                "name": travel_action,
                "preconditions": [("Me", "NOT_at", target_location)],
                "effects": [("Me", "at", target_location)],
            },
            {
                "name": f"Action_Grab_{target_name}",
                "preconditions": [("World", "has", target_name)],
                "effects": [("Me", "has", target_name)],
            },
            {
                "name": "Action_Check_Container",
                "preconditions": [("World", "has", container_ref), (container_ref, "is_open", False)],
                "effects": [(container_ref, "is_open", True)],
            },
        ],
    }


def build_crafting_rule_bundle(*, steps, resource_locations):
    proposal_rules = []
    action_rules = []
    base_input_names = set(resource_locations)

    for step in steps:
        output_name = step["output"]

        proposal_rules.append(
            {
                "name": f"Proposal_Craft_{output_name}",
                "conditions": [("goal", ("Me", "has", output_name))],
                "proposed_action": f"Action_Craft_{output_name}",
            }
        )
        action_rules.append(
            {
                "name": f"Action_Craft_{output_name}",
                "preconditions": [("Me", "has", item_name) for item_name in step["inputs"]],
                "effects": [("Me", "consume", item_name) for item_name in step["inputs"]] + [("Me", "create", output_name)],
            }
        )

        base_input_names.discard(output_name)

    for item_name in sorted(base_input_names):
        source_location = resource_locations[item_name]
        travel_action = f"Action_Go_To_{source_location}"

        proposal_rules.append(
            {
                "name": f"Proposal_Grab_{item_name}",
                "conditions": [("goal", ("Me", "has", item_name)), ("World", "has", item_name)],
                "proposed_action": f"Action_Grab_{item_name}",
            }
        )
        proposal_rules.append(
            {
                "name": f"Proposal_Go_To_{source_location}_For_{item_name}",
                "conditions": [("goal", ("Me", "has", item_name)), ("Me", "NOT_at", source_location), (source_location, "has", item_name)],
                "proposed_action": travel_action,
            }
        )

        action_rules.append(
            {
                "name": f"Action_Grab_{item_name}",
                "preconditions": [("World", "has", item_name)],
                "effects": [("Me", "has", item_name)],
            }
        )

        if any(rule["name"] == travel_action for rule in action_rules):
            continue

        action_rules.append(
            {
                "name": travel_action,
                "preconditions": [("Me", "NOT_at", source_location)],
                "effects": [("Me", "at", source_location)],
            }
        )

    return {
        "proposal_rules": proposal_rules,
        "action_rules": action_rules,
    }


RULE_BUNDLE_BUILDERS = {
    "coffee": build_coffee_rule_bundle,
    "coffee_village": build_coffee_village_rule_bundle,
    "search_retrieval": build_search_retrieval_rule_bundle,
    "crafting": build_crafting_rule_bundle,
}


def get_rule_bundle(bundle_name, **bundle_kwargs):
    if bundle_name not in RULE_BUNDLE_BUILDERS:
        valid = ", ".join(sorted(RULE_BUNDLE_BUILDERS))
        raise ValueError(f"Unknown rule bundle '{bundle_name}'. Expected one of: {valid}")
    return RULE_BUNDLE_BUILDERS[bundle_name](**bundle_kwargs)
