# Financial Resilience Simulator

This Python tool lets you select an account, inspect its typical income, spending, fixed costs and savings buffer, apply adjustable income, household-bill and one-off-cost shocks, and view the resulting runway. It also creates a simple emergency-fund goal and a shock backup plan. Calculations use the definitions in the challenge README and the provided CSVs in `data/`.

## Run and verify

From the project directory, install the dependencies and run the unit tests:

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

The tests cover data/profile metrics, shock and runway calculations, and both planning outputs. To launch the interactive simulator:

```powershell
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, select any account ID, and adjust the scenario controls. The app reads `data/monthly_summary.csv`, `data/accounts.csv`, and `data/loans.csv`; raw transactions are not needed.

## Biggest finding

Across the 4,500 accounts, **1,181 (26.2%) have median monthly spending above median monthly income**. Of all accounts, **115 (2.6%) also have a trailing-six-month average daily balance below one month of typical spending**. These figures apply the simulator's per-account medians and buffer definition to the supplied data. They are a screening signal, not a prediction of default or a financial recommendation; monthly medians can hide changes and irregular cash flows.

## Code map

- `resilience_engine/data.py` loads the CSV data and derives account baselines.
- `resilience_engine/engine.py` applies scenario shocks and calculates runway.
- `resilience_engine/planning.py` builds the goal and backup plans.
- `app.py` provides the Streamlit interface.
- `tests/` contains the unit tests for the core modules.