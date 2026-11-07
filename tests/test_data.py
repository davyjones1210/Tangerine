import unittest

import pandas as pd

from resilience_engine.data import build_profile, get_account_ids


class DataTests(unittest.TestCase):
    def setUp(self):
        self.summary = pd.DataFrame(
            [
                [42, "2025-01", 1000, 800, 200, 50, 100, 10],
                [42, "2025-02", 1200, 900, 300, 50, 100, 20],
                [42, "2025-03", 1100, 700, 250, 50, 100, 30],
            ],
            columns=[
                "account_id", "month", "money_in", "money_out", "household_bills",
                "insurance", "loan_payments", "avg_daily_balance",
            ],
        )
        self.loans = pd.DataFrame(
            [[1, 42, "C", 125], [2, 42, "A", 900]],
            columns=["loan_id", "account_id", "status", "monthly_payment"],
        )

    def test_profile_uses_medians_and_latest_six_balance_rows(self):
        profile = build_profile(42, self.summary, self.loans)
        self.assertEqual(profile.typical_income, 1100)
        self.assertEqual(profile.typical_spending, 800)
        self.assertEqual(profile.typical_fixed_costs, 400)
        self.assertEqual(profile.typical_household_bills, 250)
        self.assertEqual(profile.buffer, 20)
        self.assertEqual(profile.loan_payment, 125)
        self.assertEqual(profile.history_months, 3)

    def test_only_active_loan_statuses_are_counted(self):
        loans = self.loans.copy()
        loans.loc[0, "status"] = "B"
        profile = build_profile(42, self.summary, loans)
        self.assertEqual(profile.loan_payment, 0)

    def test_unknown_account_raises_key_error(self):
        with self.assertRaises(KeyError):
            build_profile(999, self.summary, self.loans)

    def test_account_ids_are_sorted(self):
        accounts = pd.DataFrame({"account_id": [42, 7, 42]})
        self.assertEqual(get_account_ids(accounts), [7, 42])


if __name__ == "__main__":
    unittest.main()