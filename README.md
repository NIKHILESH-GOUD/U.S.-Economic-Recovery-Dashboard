# U.S. Economic Recovery Dashboard

An interactive dashboard analyzing how consumer spending and employment recovered unevenly across U.S. states and income groups (2020-2023), using the Opportunity Insights Economic Tracker dataset from Harvard University.

## Live Dashboard

[View the live dashboard](https://us-economic-recovery-dashboard-qg3ydwzvyamuuumrfnhzcw.streamlit.app)

## Business Question

How did economic recovery from the 2020 downturn vary across U.S. states and income groups? Which populations recovered fastest, and where do structural gaps remain?

## Methodology

- **Data Source:** Opportunity Insights Economic Tracker (Harvard University)
- **Spending Data:** Anonymized credit card transactions representing percentage changes relative to January 2020 baseline
- **Employment Data:** Payroll processor records representing percentage changes relative to January 2020 baseline
- **Analysis Period:** 2020-2023
- **Tools:** Python, pandas, Plotly, Streamlit

## Key Findings

1. Higher-income quartiles (Q3, Q4) recovered consumer spending faster than lower-income quartiles (Q1, Q2).
2. Employment recovery lagged spending recovery across most states.
3. States with diverse economies tended to recover more evenly across income groups.

## Repository Structure

- `app.py` - Streamlit dashboard application
- `analysis.ipynb` - Full exploratory data analysis notebook (Google Colab)
- `requirements.txt` - Python dependencies with pinned versions

## Data Attribution

Data from the [Opportunity Insights Economic Tracker](https://tracktherecovery.org/).
Citation: Chetty, Friedman, Hendren, Stepner, and the Opportunity Insights Team (2020).
