import unittest

from resilience_engine.data import AccountProfile
from resilience_engine.engine import ScenarioResult
from resilience_engine.planning import build_backup_plan, build_goal_plan


class PlanningTests(unittest.TestCase):
    def setUp(self):
        self.profile = AccountProfile(1, 2000, 1500, 900, 500, 300, 0, 12)

    def test_goal_plan_uses_three_months_of_fixed_costs(self):
        plan = build_goal_plan(self.profile)
        self.assertEqual(plan.target_amount, 2700)
        self.assertEqual(plan.remaining_amount, 2400)
        self.assertEqual(plan.suggested_monthly_contribution, 500)
        self.assertEqual(plan.months_to_goal, 5)

    def test_goal_plan_reports_no_timeline_without_surplus(self):
        profile = AccountProfile(1, 1000, 1200, 900, 500, 0, 0, 12)
        plan = build_goal_plan(profile)
        self.assertEqual(plan.suggested_monthly_contribution, 0)
        self.assertIsNone(plan.months_to_goal)

    def test_goal_plan_uses_spending_when_fixed_costs_are_zero(self):
        profile = AccountProfile(1, 2000, 1000, 0, 500, 0, 0, 12)
        plan = build_goal_plan(profile, target_months=2)
        self.assertEqual(plan.target_amount, 2000)

    def test_backup_plan_reports_shortfall_and_runway(self):
        scenario = ScenarioResult(1000, 1500, 400, 500, 0.8)
        plan = build_backup_plan(scenario)
        self.assertEqual(plan.monthly_adjustment_needed, 500)
        self.assertEqual(plan.runway_months, 0.8)
        self.assertFalse(plan.has_no_shortfall)

    def test_invalid_goal_horizon_is_rejected(self):
        with self.assertRaises(ValueError):
            build_goal_plan(self.profile, target_months=0)


if __name__ == "__main__":
    unittest.main()