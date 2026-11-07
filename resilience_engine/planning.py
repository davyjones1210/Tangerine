"""Simple, auditable savings-goal and shock-backup plans."""

from dataclasses import dataclass
from math import ceil

from resilience_engine.data import AccountProfile
from resilience_engine.engine import ScenarioResult


@dataclass(frozen=True)
class GoalPlan:
    target_months: int
    target_amount: float
    remaining_amount: float
    suggested_monthly_contribution: float
    months_to_goal: int | None


@dataclass(frozen=True)
class BackupPlan:
    monthly_adjustment_needed: float
    buffer_after_one_off_costs: float
    runway_months: float | None
    has_no_shortfall: bool


def build_goal_plan(profile: AccountProfile, target_months: int = 3) -> GoalPlan:
    """Set a target from fixed costs (or spending when fixed costs are zero)."""
    if target_months <= 0:
        raise ValueError("target_months must be positive")

    monthly_essentials = profile.typical_fixed_costs or profile.typical_spending
    target_amount = monthly_essentials * target_months
    remaining = max(0.0, target_amount - max(0.0, profile.buffer))
    contribution = max(0.0, profile.typical_income - profile.typical_spending)
    months_to_goal = (
        0
        if remaining == 0
        else ceil(remaining / contribution)
        if contribution > 0
        else None
    )
    return GoalPlan(
        target_months=target_months,
        target_amount=target_amount,
        remaining_amount=remaining,
        suggested_monthly_contribution=contribution,
        months_to_goal=months_to_goal,
    )


def build_backup_plan(scenario: ScenarioResult) -> BackupPlan:
    """Translate the scenario into the monthly adjustment needed to stop depletion."""
    return BackupPlan(
        monthly_adjustment_needed=max(0.0, scenario.monthly_gap),
        buffer_after_one_off_costs=scenario.buffer_left,
        runway_months=scenario.runway_months,
        has_no_shortfall=scenario.has_no_shortfall,
    )