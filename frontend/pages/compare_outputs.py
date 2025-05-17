import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import django
from pathlib import Path

# Add the backend directory to the Python path for Django ORM access
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_PATH = os.path.abspath(os.path.join(BASE_DIR, "../backend"))
sys.path.append(BACKEND_PATH)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orsaas_backend.settings')
django.setup()
from core.models import Snapshot, Scenario
from components.right_log_panel import show_right_log_panel

st.set_page_config(page_title="Compare Outputs", page_icon="🔀")

if "global_logs" not in st.session_state:
    st.session_state.global_logs = ["Compare Outputs page initialized."]

st.title("Compare Scenario Outputs")

# Section 1: Select Snapshot + Scenarios
st.header("Select Scenarios to Compare")

snapshots_with_scenarios = Snapshot.objects.filter(scenario__isnull=False).distinct()
snapshot_names = [s.name for s in snapshots_with_scenarios]

if not snapshot_names:
    st.warning("No snapshots with scenarios found. Please create scenarios first.")
    compare_clicked = False
else:
    selected_snapshot_name = st.selectbox(
        "Select Snapshot",
        snapshot_names,
        help="Choose a snapshot to compare scenarios from"
    )

    selected_snapshot = Snapshot.objects.get(name=selected_snapshot_name)
    scenarios = Scenario.objects.filter(snapshot=selected_snapshot, status__in=["solved", "failed"])
    scenario_names = [s.name for s in scenarios]

    if not scenario_names:
        st.warning(f"No processed scenarios found for snapshot '{selected_snapshot_name}'. Please run scenarios first.")
        selected_scenarios = []
        compare_clicked = False
    else:
        default_scenarios = scenario_names[:min(2, len(scenario_names))]
        selected_scenarios = st.multiselect(
            "Select 2 to 4 Scenarios",
            scenario_names,
            default=default_scenarios,
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

    # Load real data for each scenario
    import json
    from components.file_utils import load_solution_summary, load_compare_metrics, generate_compare_metrics
    
    tables = {}
    kpis = {}
    
    for scenario_name in selected_scenarios:
        scenario = Scenario.objects.get(name=scenario_name, snapshot=selected_snapshot)
        
        metrics = load_compare_metrics(scenario.id)
        if not metrics:
            st.info(f"Generating comparison metrics for scenario '{scenario_name}'...")
            metrics = generate_compare_metrics(scenario.id)
        
        if metrics:
            if scenario.status == "solved":
                solution_data = load_solution_summary(scenario.id)
                route_data = []
                if solution_data and 'routes' in solution_data:
                    for i, route in enumerate(solution_data.get('routes', []), 1):
                        if isinstance(route, list):
                            route_data.append({
                                'Route ID': f'R{i}',
                                'Stops': len(route) - 2 if len(route) > 2 else 0,
                                'Distance (km)': 0,  # We don't have individual route distances in this format
                                'Duration (min)': 0  # We don't have duration in this format
                            })
                        elif isinstance(route, dict):
                            route_data.append({
                                'Route ID': f'R{i}',
                                'Stops': len(route.get('stops', [])),
                                'Distance (km)': round(route.get('distance', 0), 2),
                                'Duration (min)': round(route.get('duration', 0), 2)
                            })
                tables[scenario_name] = pd.DataFrame(route_data)
            else:
                tables[scenario_name] = pd.DataFrame({
                    'Route ID': ['N/A'],
                    'Stops': [0],
                    'Distance (km)': [0],
                    'Duration (min)': [0]
                })
            
            kpis[scenario_name] = metrics.get('kpis', {})
        else:
            st.warning(f"Could not load metrics data for scenario '{scenario_name}'")
            tables[scenario_name] = pd.DataFrame({
                'Route ID': ['N/A'],
                'Stops': [0],
                'Distance (km)': [0],
                'Duration (min)': [0]
            })
            kpis[scenario_name] = {
                'total_distance': 0,
                'total_routes': 0,
                'avg_route_distance': 0,
                'customers_served': 0,
                'max_route_length': 0,
                'avg_utilization': 0
            }

    # Tab 1: Tabular Comparison
    with tabs[0]:
        st.subheader("Tabular Output Side-by-Side")
        cols = st.columns(len(selected_scenarios))
        for i, s in enumerate(selected_scenarios):
            with cols[i]:
                st.markdown(f"#### {s}")
                st.dataframe(tables[s], hide_index=True)

    # Tab 2: KPI Comparison
    with tabs[1]:
        st.subheader("KPI Table and Radar Chart")
        
        kpi_display_names = {
            'total_distance': 'Total Distance (km)',
            'total_routes': 'Total Routes',
            'avg_route_distance': 'Avg Route Distance (km)',
            'customers_served': 'Customers Served',
            'max_route_length': 'Max Route Length',
            'avg_utilization': 'Avg Utilization (%)'
        }
        
        formatted_kpis = {}
        for s in selected_scenarios:
            formatted_kpis[s] = {}
            for k, v in kpis[s].items():
                display_name = kpi_display_names.get(k, k)
                if isinstance(v, (int, float)):
                    if k == 'avg_utilization':
                        formatted_kpis[s][display_name] = f"{v:.1f}%"
                    elif isinstance(v, float):
                        formatted_kpis[s][display_name] = f"{v:.2f}"
                    else:
                        formatted_kpis[s][display_name] = v
                else:
                    formatted_kpis[s][display_name] = v
        
        kpi_df = pd.DataFrame(formatted_kpis)
        st.dataframe(kpi_df)
        
        # Radar chart for KPIs (select numeric KPIs only)
        numeric_kpis = ['total_distance', 'total_routes', 'avg_route_distance', 'customers_served', 'max_route_length', 'avg_utilization']
        radar_df = pd.DataFrame({
            scenario_name: [float(kpis[scenario_name].get(kpi, 0)) for kpi in numeric_kpis]
            for scenario_name in selected_scenarios
        }, index=[kpi_display_names.get(kpi, kpi) for kpi in numeric_kpis])
        
        radar_df_norm = radar_df.copy()
        for idx in radar_df.index:
            max_val = radar_df.loc[idx].max()
            if max_val > 0:  # Avoid division by zero
                radar_df_norm.loc[idx] = radar_df.loc[idx] / max_val
            else:
                radar_df_norm.loc[idx] = 0
        
        # Create radar chart
        fig = go.Figure()
        for scenario_name in selected_scenarios:
            fig.add_trace(go.Scatterpolar(
                r=radar_df_norm[scenario_name].values,
                theta=radar_df_norm.index,
                fill='toself',
                name=scenario_name
            ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=True,
            title="KPI Comparison (Normalized)"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Tab 3: Plot Comparison
    with tabs[2]:
        st.subheader("Bar Chart Comparison")
        
        bar_kpis = ['total_distance', 'avg_route_distance', 'customers_served']
        bar_kpi_names = [kpi_display_names.get(k, k) for k in bar_kpis]
        
        bar_data = {
            'Scenario': selected_scenarios
        }
        
        for kpi, display_name in zip(bar_kpis, bar_kpi_names):
            bar_data[display_name] = [kpis[s].get(kpi, 0) for s in selected_scenarios]
        
        bar_df = pd.DataFrame(bar_data)
        
        fig_bar = px.bar(
            bar_df,
            x='Scenario',
            y=bar_kpi_names,
            barmode='group',
            title="Key Performance Indicators by Scenario",
            labels={
                'value': 'Value',
                'variable': 'KPI'
            }
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