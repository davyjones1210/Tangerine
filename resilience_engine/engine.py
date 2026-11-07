"""Shock inputs and runway calculation."""

from dataclasses import dataclass

from resilience_engine.data import AccountProfile


@dataclass(frozen=True)
class Shock:
    income_multiplier: float = 1.0
    household_bill_increase_pct: float = 0.0
    one_off_costs: float = 0.0
    duration_months: int = 0

    def __post_init__(self) -> None:
        if self.income_multiplier < 0:
            raise ValueError("income_multiplier cannot be negative")
        if self.household_bill_increase_pct < 0:
            raise ValueError("household_bill_increase_pct cannot be negative")
        if self.one_off_costs < 0:
            raise ValueError("one_off_costs cannot be negative")
        if self.duration_months < 0:
            raise ValueError("duration_months cannot be negative")


@dataclass(frozen=True)
class ScenarioResult:
    income_after_shock: float
    spending_after_shock: float
    buffer_left: float
    monthly_gap: float
    runway_months: float | None

    @property
    def has_no_shortfall(self) -> bool:
        return self.monthly_gap <= 0


def simulate(profile: AccountProfile, shock: Shock = Shock()) -> ScenarioResult:
    """Apply a shock and calculate runway using the challenge's stated formula."""
    income = profile.typical_income * shock.income_multiplier
    spending = profile.typical_spending + (
        profile.typical_household_bills * shock.household_bill_increase_pct
    )
    buffer_left = profile.buffer - shock.one_off_costs
    monthly_gap = spending - income

    if buffer_left <= 0:
        runway = 0.0
    elif monthly_gap <= 0:
        runway = None
    else:
        runway = round(min(buffer_left / monthly_gap, 120), 1)

    return ScenarioResult(
        income_after_shock=income,
        spending_after_shock=spending,
        buffer_left=buffer_left,
        monthly_gap=monthly_gap,
        runway_months=runway,
    )