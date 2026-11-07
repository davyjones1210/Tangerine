import unittest
from dataclasses import replace

from resilience_engine.data import AccountProfile
from resilience_engine.engine import Shock, simulate


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.profile = AccountProfile(
            account_id=1,
            typical_income=2000,
            typical_spending=1800,
            typical_fixed_costs=900,
            typical_household_bills=500,
            buffer=3000,
            loan_payment=100,
            history_months=12,
        )

    def test_combined_shock_calculates_runway(self):
        result = simulate(
            self.profile,
            Shock(income_multiplier=0.55, household_bill_increase_pct=0.15, one_off_costs=500),
        )
        self.assertEqual(result.income_after_shock, 1100)
        self.assertEqual(result.spending_after_shock, 1875)
        self.assertEqual(result.buffer_left, 2500)
        self.assertEqual(result.monthly_gap, 775)
        self.assertEqual(result.runway_months, 3.2)

    def test_no_shortfall_has_no_numeric_runway(self):
        result = simulate(self.profile)
        self.assertTrue(result.has_no_shortfall)
        self.assertIsNone(result.runway_months)

    def test_depleted_buffer_means_zero_runway(self):
        result = simulate(self.profile, Shock(one_off_costs=3000))
        self.assertEqual(result.runway_months, 0)

    def test_runway_is_capped_at_120_months(self):
        result = simulate(
            replace(self.profile, buffer=500000),
            Shock(income_multiplier=0, one_off_costs=0),
        )
        self.assertEqual(result.runway_months, 120)

    def test_negative_shock_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            Shock(income_multiplier=-0.1)


if __name__ == "__main__":
    unittest.main()