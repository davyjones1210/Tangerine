"""Load account data and calculate the baseline metrics used by the simulator."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class AccountProfile:
    account_id: int
    typical_income: float
    typical_spending: float
    typical_fixed_costs: float
    typical_household_bills: float
    buffer: float
    loan_payment: float
    history_months: int


SUMMARY_COLUMNS = {
    "account_id",
    "month",
    "money_in",
    "money_out",
    "household_bills",
    "insurance",
    "loan_payments",
    "avg_daily_balance",
}


def load_data(data_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the small account/loan files and monthly summary (not raw transactions)."""
    data_path = Path(data_dir)
    summary = pd.read_csv(data_path / "monthly_summary.csv")
    accounts = pd.read_csv(data_path / "accounts.csv")
    loans_path = data_path / "loans.csv"
    loans = pd.read_csv(loans_path) if loans_path.exists() else pd.DataFrame()

    missing_columns = SUMMARY_COLUMNS.difference(summary.columns)
    if missing_columns:
        raise ValueError(
            "monthly_summary.csv is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )
    return summary, accounts, loans


def get_account_ids(accounts: pd.DataFrame) -> list[int]:
    """Return sorted account IDs for the account picker."""
    return sorted(int(account_id) for account_id in accounts["account_id"].dropna().unique())


def build_profile(
    account_id: int,
    monthly_summary: pd.DataFrame,
    loans: pd.DataFrame,
) -> AccountProfile:
    """Calculate an account's baseline using the definitions in the challenge README."""
    history = monthly_summary.loc[monthly_summary["account_id"] == account_id].copy()
    if history.empty:
        raise KeyError(f"No monthly summary found for account {account_id}")

    history = history.sort_values("month")
    numeric_columns = [
        "money_in",
        "money_out",
        "household_bills",
        "insurance",
        "loan_payments",
        "avg_daily_balance",
    ]
    history[numeric_columns] = history[numeric_columns].apply(
        pd.to_numeric, errors="coerce"
    ).fillna(0)
    fixed_costs = (
        history["household_bills"] + history["insurance"] + history["loan_payments"]
    )

    loan_payment = 0.0
    if not loans.empty and {"account_id", "status", "monthly_payment"}.issubset(
        loans.columns
    ):
        active_loans = loans.loc[
            (loans["account_id"] == account_id) & loans["status"].isin(["C", "D"])
        ]
        if not active_loans.empty:
            loan_payment = float(
                pd.to_numeric(active_loans["monthly_payment"], errors="coerce")
                .fillna(0)
                .sum()
            )

    return AccountProfile(
        account_id=int(account_id),
        typical_income=float(history["money_in"].median()),
        typical_spending=float(history["money_out"].median()),
        typical_fixed_costs=float(fixed_costs.median()),
        typical_household_bills=float(history["household_bills"].median()),
        buffer=float(history.tail(6)["avg_daily_balance"].mean()),
        loan_payment=loan_payment,
        history_months=len(history),
    )