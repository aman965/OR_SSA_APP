import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from frontend.components.right_log_panel import show_right_log_panel

st.set_page_config(page_title="Compare Outputs", page_icon="🔀")

if "global_logs" not in st.session_state:
    st.session_state.global_logs = ["Compare Outputs page initialized."]

st.title("Compare Scenario Outputs")

# Section 1: Select Snapshot + Scenarios
st.header("Select Scenarios to Compare")

snapshots = ["snap_2024_05_11", "order_batch_snap"]
scenarios_dict = {
    "snap_2024_05_11": ["scenario_1", "scenario_2", "scenario_3"],
    "order_batch_snap": ["scenario_4", "scenario_5", "scenario_6", "scenario_7"]
}

selected_snapshot = st.selectbox(
    "Select Snapshot",
    snapshots,
    help="Choose a snapshot to compare scenarios from"
)

available_scenarios = scenarios_dict[selected_snapshot]
selected_scenarios = st.multiselect(
    "Select 2 to 4 Scenarios",
    available_scenarios,
    default=available_scenarios[:2],
    help="Pick 2 to 4 scenarios to compare"
)

if len(selected_scenarios) < 2 or len(selected_scenarios) > 4:
    st.warning("Please select between 2 and 4 scenarios to compare.")
    compare_clicked = False
else:
    compare_clicked = st.button("Compare Scenarios")

# Section 2: Show Comparison (After Button Click)
if compare_clicked:
    st.header("Scenario Comparison")
    tabs = st.tabs(["📊 Tabular Comparison", "📈 KPI Comparison", "📉 Plot Comparison"])

    # Mock data for each scenario
    mock_tables = {
        s: pd.DataFrame({
            'Route ID': [f'R{i+1}' for i in range(3)],
            'Stops': [5+i for i in range(3)],
            'Distance (km)': [40+5*i for i in range(3)],
            'Duration (min)': [100+10*i for i in range(3)]
        }) for s in selected_scenarios
    }
    mock_kpis = {
        s: {
            'Total Distance': 120+10*i,
            'Total Routes': 3,
            'Max Route Length': 55-2*i,
            'Avg Utilization': 80+2*i
        } for i, s in enumerate(selected_scenarios)
    }

    # Tab 1: Tabular Comparison
    with tabs[0]:
        st.subheader("Tabular Output Side-by-Side")
        cols = st.columns(len(selected_scenarios))
        for i, s in enumerate(selected_scenarios):
            with cols[i]:
                st.markdown(f"#### {s}")
                st.dataframe(mock_tables[s], hide_index=True)

    # Tab 2: KPI Comparison
    with tabs[1]:
        st.subheader("KPI Table and Radar Chart")
        kpi_df = pd.DataFrame(mock_kpis).T
        st.dataframe(kpi_df)
        # Radar chart
        categories = list(kpi_df.columns)
        fig = go.Figure()
        for s in selected_scenarios:
            fig.add_trace(go.Scatterpolar(
                r=list(kpi_df.loc[s]),
                theta=categories,
                fill='toself',
                name=s
            ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            showlegend=True,
            title="KPI Radar Comparison"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Tab 3: Plot Comparison
    with tabs[2]:
        st.subheader("Bar Chart Comparison")
        # Bar chart for Total Distance
        bar_df = pd.DataFrame({
            'Scenario': selected_scenarios,
            'Total Distance': [mock_kpis[s]['Total Distance'] for s in selected_scenarios],
            'Max Route Length': [mock_kpis[s]['Max Route Length'] for s in selected_scenarios]
        })
        fig_bar = px.bar(
            bar_df,
            x='Scenario',
            y=['Total Distance', 'Max Route Length'],
            barmode='group',
            title="Total Distance and Max Route Length by Scenario"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# HOOK: Load and merge scenario result files for tabular and KPI comparison
# HOOK: Generate radar chart dynamically based on selected KPIs
# HOOK: Prepare consistent data structure for plot overlays

# Show the right log panel
show_right_log_panel(st.session_state.global_logs)

# Debug Panel
if st.sidebar.checkbox("Show Debug Info", value=False):
    with st.expander("🔍 Debug Panel", expanded=True):
        st.markdown("### Session State")
        st.json(st.session_state) 