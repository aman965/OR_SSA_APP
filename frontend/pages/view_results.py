import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import sys
import django
from datetime import datetime

# Add the backend directory to the Python path for Django ORM access
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_PATH = os.path.abspath(os.path.join(BASE_DIR, "../backend"))
MEDIA_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../media"))
sys.path.append(BACKEND_PATH)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orsaas_backend.settings')
django.setup()
from core.models import Scenario, Snapshot
from components.right_log_panel import show_right_log_panel

st.set_page_config(page_title="View Results", page_icon="📊", layout="wide")

# Initialize session state for logs if not exists
if "global_logs" not in st.session_state:
    st.session_state.global_logs = ["View Results page initialized."]

# Get selected scenario info from session state
selected_snapshot = st.session_state.get("selected_snapshot_for_results")
selected_scenario = st.session_state.get("selected_scenario_for_results")

if not selected_snapshot or not selected_scenario:
    st.error("No scenario selected. Please go back to the Scenario Builder and select a scenario to view.")
    if st.button("Back to Scenario Builder"):
        st.switch_page("pages/scenario_builder.py")
    st.stop()

try:
    # Fetch scenario from database
    scenario = Scenario.objects.select_related('snapshot').get(
        name=selected_scenario,
        snapshot__name=selected_snapshot
    )
    
    if scenario.status != "solved":
        st.error(f"Scenario '{scenario.name}' is not solved. Current status: {scenario.status}")
        if st.button("Back to Scenario Builder"):
            st.switch_page("pages/scenario_builder.py")
        st.stop()

    # Load solution data
    solution_path = os.path.join(MEDIA_ROOT, "scenarios", str(scenario.id), "outputs", "solution_summary.json")
    if not os.path.exists(solution_path):
        alt_solution_path = os.path.join(MEDIA_ROOT, "scenarios", str(scenario.id), "solution_summary.json")
        if os.path.exists(alt_solution_path):
            solution_path = alt_solution_path
        else:
            st.error(f"Solution file not found for scenario '{scenario.name}'")
            if st.button("Back to Scenario Builder"):
                st.switch_page("pages/scenario_builder.py")
            st.stop()

    with open(solution_path, 'r') as f:
        solution = json.load(f)

    # Page Header
    st.title("📊 Solution Results")
    
    # Back button
    if st.button("← Back to Scenario Builder"):
        st.switch_page("pages/scenario_builder.py")

    # Scenario Info
    st.subheader("Scenario Information")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Scenario", scenario.name)
        st.metric("Snapshot", scenario.snapshot.name)
    with col2:
        st.metric("Created", scenario.created_at.strftime("%Y-%m-%d %H:%M"))
        st.metric("Parameters", f"P1: {scenario.param1}, P2: {scenario.param2}, P3: {scenario.param3}")

    # KPI Cards
    st.subheader("Key Performance Indicators")
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.metric("Total Distance", f"{solution['total_distance']:.2f} km")
    with kpi_cols[1]:
        st.metric("Vehicles Used", str(solution['vehicle_count']))
    with kpi_cols[2]:
        total_stops = sum(len(route) - 2 for route in solution['routes'])  # -2 for depot start/end
        st.metric("Total Stops", str(total_stops))
    with kpi_cols[3]:
        avg_route_length = solution['total_distance'] / len(solution['routes'])
        st.metric("Avg Route Length", f"{avg_route_length:.2f} km")

    # Routes Table
    st.subheader("Route Details")
    routes_data = []
    for i, route in enumerate(solution['routes'], 1):
        route_distance = sum(
            abs(route[j] - route[j+1])  # Simple distance calculation
            for j in range(len(route)-1)
        )
        routes_data.append({
            "Route": f"R{i}",
            "Stops": len(route) - 2,  # Exclude depot start/end
            "Distance (km)": route_distance,
            "Sequence": " → ".join(str(node) for node in route)
        })
    
    routes_df = pd.DataFrame(routes_data)
    st.dataframe(routes_df, use_container_width=True)

    # Visualizations
    st.subheader("Route Analysis")
    viz_cols = st.columns(2)
    
    with viz_cols[0]:
        # Distance per Route Bar Chart
        fig_distance = px.bar(
            routes_df,
            x="Route",
            y="Distance (km)",
            title="Distance per Route",
            color="Distance (km)",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_distance, use_container_width=True)
    
    with viz_cols[1]:
        # Stops per Route Bar Chart
        fig_stops = px.bar(
            routes_df,
            x="Route",
            y="Stops",
            title="Stops per Route",
            color="Stops",
            color_continuous_scale="Plasma"
        )
        st.plotly_chart(fig_stops, use_container_width=True)

    # Raw Solution Data
    with st.expander("View Raw Solution Data"):
        st.json(solution)

except Scenario.DoesNotExist:
    st.error(f"Scenario '{selected_scenario}' not found in snapshot '{selected_snapshot}'")
    if st.button("Back to Scenario Builder"):
        st.switch_page("pages/scenario_builder.py")
except Exception as e:
    st.error(f"Error loading results: {str(e)}")
    st.session_state.global_logs.append(f"Error loading results: {str(e)}")
    if st.button("Back to Scenario Builder"):
        st.switch_page("pages/scenario_builder.py")

# Show the right log panel
show_right_log_panel(st.session_state.global_logs)

# Debug Panel
if st.sidebar.checkbox("Show Debug Info", value=False):
    with st.expander("🔍 Debug Panel", expanded=True):
        st.markdown("### Session State")
        st.json(st.session_state)   