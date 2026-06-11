import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configure the page layout and title
st.set_page_config(page_title="U.S. Economic Recovery Dashboard", layout="wide")
@st.cache_data
def load_data():
    # Base URL for raw CSV files from the Economic Tracker repo
    base_url = "https://raw.githubusercontent.com/OpportunityInsights/EconomicTracker/main/data/"

    # Load spending, employment, and geographic crosswalk files
    spending = pd.read_csv(base_url + "Affinity%20-%20State%20-%20Daily.csv")
    employment = pd.read_csv(base_url + "Employment%20-%20State%20-%20Weekly.csv")
    geo = pd.read_csv(base_url + "GeoIDs%20-%20State.csv")

    # Create a proper datetime column for spending data
    spending["date"] = pd.to_datetime(
        spending[["year", "month", "day"]].rename(columns={"day": "day"})
    )
    spending = spending[(spending["date"] >= "2020-01-01") & (spending["date"] <= "2023-12-31")]

    # --- FIX 1: Convert spending columns to numeric BEFORE grouping (coerces '.' to NaN) ---
    spending_cols = ["spend_all", "spend_all_q1", "spend_all_q2", "spend_all_q3", "spend_all_q4"]
    for col in spending_cols:
        spending[col] = pd.to_numeric(spending[col], errors="coerce")

    # Create a proper datetime column for employment data
    employment["date"] = pd.to_datetime(
        employment["year"].astype(str) + "-" + employment["month"].astype(str) + "-" + employment["day_endofweek"].astype(str)
    )
    employment = employment[(employment["date"] >= "2020-01-01") & (employment["date"] <= "2023-12-31")]

    # --- FIX 2: Snap employment dates to upcoming Sunday boundaries (avoids 0 rows) ---
    employment["date"] = employment["date"] + pd.to_timedelta(6 - employment["date"].dt.weekday, unit="D")

    # Resample daily spending to weekly to align with employment frequency
    spending_weekly = spending.groupby([pd.Grouper(key="date", freq="W"), "statefips"]).agg(
        spend_all=("spend_all", "mean"),
        spend_all_q1=("spend_all_q1", "mean"),
        spend_all_q2=("spend_all_q2", "mean"),
        spend_all_q3=("spend_all_q3", "mean"),
        spend_all_q4=("spend_all_q4", "mean"),
    ).reset_index()

    # Merge spending with employment on date and state
    merged = spending_weekly.merge(
        employment[["date", "statefips", "emp", "emp_incq1", "emp_incq2", "emp_incq3", "emp_incq4"]],
        on=["date", "statefips"],
        how="inner"
    )

    # Add human-readable state names from the crosswalk file
    merged = merged.merge(
        geo[["statefips", "statename"]],
        on="statefips",
        how="left"
    )

    # Convert employment metric columns to numeric (handles '.' or empty strings)
    employment_cols = ["emp", "emp_incq1", "emp_incq2", "emp_incq3", "emp_incq4"]
    for col in employment_cols:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")

    return merged

data = load_data()
# Sidebar filter controls
st.sidebar.header("Filters")
tab1, tab2 = st.tabs(["Recovery Analysis", "Resilience Scores"])

with tab1:
    st.sidebar.header("Filters")

    states = sorted(data["statename"].dropna().unique())
    selected_states = st.sidebar.multiselect(
        "Select States",
        options=states,
        default=["California", "Texas", "New York", "Florida"]
    )

    date_min = data["date"].min().to_pydatetime()
    date_max = data["date"].max().to_pydatetime()
    date_range = st.sidebar.slider(
        "Date Range",
        min_value=date_min,
        max_value=date_max,
        value=(date_min, date_max)
    )

    filtered = data[
        (data["statename"].isin(selected_states)) &
        (data["date"] >= pd.Timestamp(date_range[0])) &
        (data["date"] <= pd.Timestamp(date_range[1]))
    ]

    col1, col2, col3 = st.columns(3)
    with col1:
        avg_spend = filtered["spend_all"].mean()
        st.metric("Avg Spending Change", f"{avg_spend:.1%}" if pd.notna(avg_spend) else "N/A")
    with col2:
        avg_emp = filtered["emp"].mean()
        st.metric("Avg Employment Change", f"{avg_emp:.1%}" if pd.notna(avg_emp) else "N/A")
    with col3:
        q4_avg = filtered["spend_all_q4"].mean()
        q1_avg = filtered["spend_all_q1"].mean()
        gap = (q4_avg - q1_avg) if (pd.notna(q4_avg) and pd.notna(q1_avg)) else None
        st.metric("Income Gap (Q4 - Q1)", f"{gap:.1%}" if gap is not None else "N/A")

    st.subheader("Spending Recovery by Income Quartile")

    national = data.groupby("date").agg(
        Q1=("spend_all_q1", "mean"),
        Q2=("spend_all_q2", "mean"),
        Q3=("spend_all_q3", "mean"),
        Q4=("spend_all_q4", "mean"),
    ).reset_index()

    fig_quartile = go.Figure()
    for quartile in ["Q1", "Q2", "Q3", "Q4"]:
        fig_quartile.add_trace(go.Scatter(
            x=national["date"],
            y=national[quartile],
            mode="lines",
            name=f"Income {quartile}"
        ))
    fig_quartile.update_layout(
        yaxis_title="Spending Change (relative to Jan 2020)",
        xaxis_title="Date",
        hovermode="x unified"
    )
    st.plotly_chart(fig_quartile, use_container_width=True)

    st.subheader("State-by-State Recovery Comparison")

    state_recovery = data.groupby("statename").agg(
        avg_spend_recovery=("spend_all", "mean"),
        avg_emp_recovery=("emp", "mean"),
    ).reset_index().dropna()

    state_recovery_sorted = state_recovery.sort_values("avg_spend_recovery", ascending=True).tail(20)

    fig_states = px.bar(
        state_recovery_sorted,
        x="avg_spend_recovery",
        y="statename",
        orientation="h",
        title="Top 20 States by Average Spending Recovery",
        labels={"avg_spend_recovery": "Avg Spending Change", "statename": "State"}
    )
    st.plotly_chart(fig_states, use_container_width=True)

    st.subheader("Spending vs Employment Recovery by State")

    fig_scatter = px.scatter(
        state_recovery,
        x="avg_spend_recovery",
        y="avg_emp_recovery",
        text="statename",
        title="Spending Recovery vs Employment Recovery",
        labels={"avg_spend_recovery": "Avg Spending Recovery", "avg_emp_recovery": "Avg Employment Recovery"}
    )
    fig_scatter.update_traces(textposition="top center", textfont_size=8)
    st.plotly_chart(fig_scatter, use_container_width=True)
with tab2:
    st.subheader("Economic Resilience Scores")
    st.markdown("A composite score ranking states by recovery strength. Adjust the weights below to explore different priorities.")

    st.markdown("**Methodology:** Each component is normalized to 0-100. The final score is a weighted average of spending recovery speed, employment recovery speed, and income equality (smaller gap between highest and lowest income quartile recovery).")

    wcol1, wcol2, wcol3 = st.columns(3)
    with wcol1:
        w_spend = st.slider("Spending Weight (%)", 0, 100, 40, key="w_spend")
    with wcol2:
        w_emp = st.slider("Employment Weight (%)", 0, 100, 40, key="w_emp")
    with wcol3:
        w_equality = st.slider("Equality Weight (%)", 0, 100, 20, key="w_equality")

    total_weight = w_spend + w_emp + w_equality

    if total_weight == 0:
        st.warning("Weights must sum to more than 0.")
    else:
        # Aggregate recovery metrics per state
        scores = data.groupby("statename").agg(
            spend_recovery=("spend_all", "mean"),
            emp_recovery=("emp", "mean"),
            q4_recovery=("spend_all_q4", "mean"),
            q1_recovery=("spend_all_q1", "mean"),
        ).reset_index().dropna()

        # Calculate absolute income gap (smaller is better)
        scores["income_gap"] = (scores["q4_recovery"] - scores["q1_recovery"]).abs()

        # Normalize each component to 0-100 scale
        def normalize(series):
            smin = series.min()
            smax = series.max()
            if smax == smin:
                return pd.Series([50.0] * len(series), index=series.index)
            return ((series - smin) / (smax - smin)) * 100

        scores["spend_score"] = normalize(scores["spend_recovery"])
        scores["emp_score"] = normalize(scores["emp_recovery"])
        # Negate income_gap so smaller gaps get higher scores
        scores["equality_score"] = normalize(-scores["income_gap"])

        # Combine into weighted resilience score
        scores["resilience_score"] = (
            (w_spend / total_weight) * scores["spend_score"] +
            (w_emp / total_weight) * scores["emp_score"] +
            (w_equality / total_weight) * scores["equality_score"]
        )

        scores_sorted = scores.sort_values("resilience_score", ascending=False).reset_index(drop=True)
        scores_sorted.index = scores_sorted.index + 1

        # Horizontal bar chart of top 25 states
        fig_resilience = px.bar(
            scores_sorted.head(25),
            x="resilience_score",
            y="statename",
            orientation="h",
            title="Top 25 States by Economic Resilience Score",
            labels={"resilience_score": "Resilience Score (0-100)", "statename": "State"},
            color="resilience_score",
            color_continuous_scale="Viridis"
        )
        fig_resilience.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_resilience, use_container_width=True)

        # Full state ranking table
        st.dataframe(
            scores_sorted[["statename", "resilience_score", "spend_score", "emp_score", "equality_score"]]
            .rename(columns={
                "statename": "State",
                "resilience_score": "Overall Score",
                "spend_score": "Spending Score",
                "emp_score": "Employment Score",
                "equality_score": "Equality Score"
            })
            .style.format({"Overall Score": "{:.1f}", "Spending Score": "{:.1f}", "Employment Score": "{:.1f}", "Equality Score": "{:.1f}"}),
            use_container_width=True
        )
st.markdown("---")
st.markdown("**Data Source:** [Opportunity Insights Economic Tracker](https://tracktherecovery.org/) | Harvard University")
st.markdown("**Methodology:** Spending data from anonymized credit card transactions. Employment data from payroll processors. All values represent percentage changes relative to January 2020 baseline.")
