import random
import unittest

import MakingCoffeeWithSoar as coffee
import soar_rule_library
from typed_rule_engine import (
    Binding,
    Name,
    OperationExecutor,
)


class TypedSoarRuleTests(unittest.TestCase):
    def test_single_coffee_world_succeeds(self):
        random.seed(0)
        stage = coffee.build_world()
        agent = coffee.Agent(stage, coffee.build_rules(), verbose=False)

        self.assertTrue(agent.run(max_steps=100))
        self.assertIn("Coffee", agent.state["drank"])
        self.assertIn("Mug", agent.items)
        self.assertIn("CoffeeBox", agent.items)

    def test_multi_object_world_succeeds(self):
        random.seed(4)
        stage = coffee.build_multi_world(seed=4)
        agent = coffee.Agent(stage, coffee.build_rules(), verbose=False)

        self.assertTrue(agent.run(max_steps=200))
        self.assertIn("Coffee", agent.state["drank"])

    def test_container_reveal_uses_resolver_for_tag_lookup(self):
        stage = coffee.build_world()
        rules = coffee.build_rules()
        agent = coffee.Agent(stage, rules, verbose=False)
        action = next(rule for rule in rules.action_rules if rule.name == "Action_Check_Cupboard_2")
        grounded = agent.grounder.applicable_actions(action, agent, stage)

        self.assertTrue(grounded)
        events = agent.executor.apply_all(action.effects, agent, stage, grounded[0].binding)

        self.assertIn("Reveal Mug from Cupboard", events)
        self.assertIn("Mug", stage.items)
        self.assertNotIn("Mug", stage.get("Cupboard").items)

    def test_transfer_moves_world_item_to_agent_inventory(self):
        stage = coffee.World()
        stage.add_item(coffee.DrinkMix(), "CoffeeBox")
        agent = coffee.Agent(stage, coffee.RuleSet(), verbose=False)
        executor = OperationExecutor()

        event = executor.apply(soar_rule_library.grab_rule(Name("CoffeeBox")).effects[0], agent, stage, Binding({"item": ("world", "CoffeeBox", stage.items["CoffeeBox"])}))

        self.assertEqual(event, "Transfer CoffeeBox from World to Me")
        self.assertIn("CoffeeBox", agent.items)
        self.assertNotIn("CoffeeBox", stage.items)

    def test_invalid_operation_fails_loudly(self):
        stage = coffee.World()
        agent = coffee.Agent(stage, coffee.RuleSet(), verbose=False)

        with self.assertRaises(TypeError):
            OperationExecutor().apply(("Me", "has", "Coffee"), agent, stage, Binding())


if __name__ == "__main__":
    unittest.main()
