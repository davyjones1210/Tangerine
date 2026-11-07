"""Streamlit interface for the account-level resilience simulator."""

from pathlib import Path

import pandas as pd
import streamlit as st

from resilience_engine.data import build_profile, get_account_ids, load_data
from resilience_engine.engine import Shock, simulate
from resilience_engine.planning import build_backup_plan, build_goal_plan


DATA_DIR = Path(__file__).parent / "data"


@st.cache_data(show_spinner="Loading account history...")
def load_app_data(data_dir: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return load_data(data_dir)


st.set_page_config(page_title="Resilience Simulator", page_icon="🍊", layout="wide")
st.title("Financial resilience simulator")
st.caption("Account-level estimates from the provided bank dataset. All values in CAD.")

try:
    monthly_summary, accounts, loans = load_app_data(str(DATA_DIR))
except (OSError, ValueError) as error:
    st.error(f"Could not load the dataset: {error}")
    st.stop()

account_ids = get_account_ids(accounts)
if not account_ids:
    st.error("No accounts were found in accounts.csv.")
    st.stop()

with st.sidebar:
    st.header("Customer and shock")
    account_id = st.selectbox("Account ID", account_ids)
    st.subheader("Scenario")
    income_multiplier = st.slider(
        "Income remaining (%)", min_value=0, max_value=150, value=55, step=5
    ) / 100
    bill_increase_pct = st.slider(
        "Household bills increase (%)", min_value=0, max_value=100, value=0, step=5
    ) / 100
    one_off_costs = st.number_input(
        "One-off cost (CAD)", min_value=0.0, value=0.0, step=100.0
    )
    duration_months = st.number_input(
        "Shock duration (months)", min_value=0, value=6, step=1
    )

try:
    profile = build_profile(account_id, monthly_summary, loans)
except KeyError as error:
    st.error(str(error))
    st.stop()

shock = Shock(
    income_multiplier=income_multiplier,
    household_bill_increase_pct=bill_increase_pct,
    one_off_costs=one_off_costs,
    duration_months=int(duration_months),
)
scenario = simulate(profile, shock)
goal = build_goal_plan(profile)
backup = build_backup_plan(scenario)

st.subheader(f"Account {profile.account_id}")
st.caption(f"Baseline uses {profile.history_months} monthly records.")
metrics = st.columns(5)
metrics[0].metric("Typical monthly income", f"${profile.typical_income:,.2f}")
metrics[1].metric("Typical monthly spending", f"${profile.typical_spending:,.2f}")
metrics[2].metric("Fixed costs", f"${profile.typical_fixed_costs:,.2f}")
metrics[3].metric("Savings buffer", f"${profile.buffer:,.2f}")
metrics[4].metric(
    "Baseline runway",
    "No shortfall (120+)"
    if simulate(profile).runway_months is None
    else f"{simulate(profile).runway_months:.1f} months",
)

st.subheader("Scenario result")
runway_text = (
    "No shortfall (120+)"
    if scenario.runway_months is None
    else f"{scenario.runway_months:.1f} months"
)
scenario_metrics = st.columns(5)
scenario_metrics[0].metric("Income after shock", f"${scenario.income_after_shock:,.2f}")
scenario_metrics[1].metric("Spending after shock", f"${scenario.spending_after_shock:,.2f}")
scenario_metrics[2].metric("Monthly shortfall", f"${max(0, scenario.monthly_gap):,.2f}")
scenario_metrics[3].metric("Buffer after one-off", f"${scenario.buffer_left:,.2f}")
scenario_metrics[4].metric("Runway", runway_text)
st.caption(
    f"Shock settings: {income_multiplier:.0%} of typical income for "
    f"{int(duration_months)} months; household bills +{bill_increase_pct:.0%}. "
    "Runway applies the shocked monthly gap as a steady-state estimate, capped at 120 months."
)

st.subheader("Plans")
goal_column, backup_column = st.columns(2)
with goal_column:
    st.markdown("**Emergency-fund goal**")
    st.write(f"Three-month target: **${goal.target_amount:,.2f}**")
    st.write(f"Remaining to target: **${goal.remaining_amount:,.2f}**")
    st.write(f"Suggested monthly contribution: **${goal.suggested_monthly_contribution:,.2f}**")
    if goal.months_to_goal is None:
        st.write("At the observed median income and spending, there is no monthly surplus to fund this goal.")
    else:
        st.write(f"Estimated time at that contribution: **{goal.months_to_goal} months**")
with backup_column:
    st.markdown("**Shock backup**")
    if backup.has_no_shortfall:
        st.write("No monthly shortfall under this scenario. Keep the remaining buffer available for unexpected costs.")
    else:
        st.write(
            f"Reduce spending or replace income by **${backup.monthly_adjustment_needed:,.2f} per month** "
            "to stop drawing down the buffer."
        )
    st.write(f"Buffer after one-off cost: **${backup.buffer_after_one_off_costs:,.2f}**")

with st.expander("How these numbers are calculated"):
    st.markdown(
        "- Income and spending are medians of `money_in` and `money_out`.\n"
        "- Fixed costs are the median monthly sum of household bills, insurance, and loan payments.\n"
        "- Buffer is the mean `avg_daily_balance` over the last six rows by month.\n"
        "- Household-bill shocks add a percentage of median household bills to typical spending.\n"
        "- Runway is buffer after one-off costs divided by the positive monthly shortfall; it is 0 when the buffer is depleted and capped at 120 months.\n"
        "- Active loan payments come from loans with status C or D."
    )

account_history = monthly_summary.loc[
    monthly_summary["account_id"] == profile.account_id
].sort_values("month")
with st.expander("Account history"):
    chart_data = account_history.set_index("month")[["money_in", "money_out", "month_end_balance"]]
    st.line_chart(chart_data)