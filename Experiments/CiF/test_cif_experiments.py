from __future__ import annotations

import sys
from pathlib import Path
import unittest


THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from cif_engine import run_situation
from cif_situations import SITUATIONS


class CiFExperimentTests(unittest.TestCase):
    def test_every_situation_runs_to_its_turn_limit(self):
        for situation in SITUATIONS.values():
            with self.subTest(situation=situation.id):
                result = run_situation(situation)
                self.assertEqual(len(result.transcript), situation.turn_limit)

    def test_every_exchange_used_is_enabled_for_that_situation(self):
        for situation in SITUATIONS.values():
            enabled = {exchange.name for exchange in situation.enabled_exchanges}
            with self.subTest(situation=situation.id):
                result = run_situation(situation)
                for turn in result.transcript:
                    self.assertIn(turn["exchange"], enabled)

    def test_numeric_state_stays_clamped(self):
        tracked_metrics = {"like", "trust", "attraction"}
        mood_metrics = {"joy", "wariness", "envy"}
        for situation in SITUATIONS.values():
            with self.subTest(situation=situation.id):
                result = run_situation(situation)
                for metrics in result.final_state.numeric.values():
                    for name in tracked_metrics:
                        self.assertGreaterEqual(metrics[name], -100)
                        self.assertLessEqual(metrics[name], 100)
                for metrics in result.final_state.moods.values():
                    for name in mood_metrics:
                        self.assertGreaterEqual(metrics[name], -100)
                        self.assertLessEqual(metrics[name], 100)

    def test_trigger_driven_status_changes_show_up_in_key_situations(self):
        party = run_situation(SITUATIONS["crush_at_a_party"])
        self.assertTrue(
            any(
                "romantic_tension" in note or "awkward status" in note
                for turn in party.transcript
                for note in turn["trigger_notes"]
            )
        )

        comfort = run_situation(SITUATIONS["comfort_after_failure"])
        self.assertTrue(
            any(
                "comfortable with each other" in note
                for turn in comfort.transcript
                for note in turn["trigger_notes"]
            )
        )

        triangle = run_situation(SITUATIONS["jealous_triangle"])
        self.assertTrue(
            any(
                "grows jealous" in note
                for turn in triangle.transcript
                for note in turn["trigger_notes"]
            )
        )


if __name__ == "__main__":
    unittest.main()
