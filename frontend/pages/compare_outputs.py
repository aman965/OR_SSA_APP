import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import django
from pathlib import Path
import json
import glob

# Add the backend directory to the Python path for Django ORM access
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_PATH = os.path.abspath(os.path.join(BASE_DIR, "../backend"))
MEDIA_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../media"))
sys.path.append(BACKEND_PATH)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orsaas_backend.settings')
django.setup()
from core.models import Snapshot, Scenario
from components.right_log_panel import show_right_log_panel
from components.file_utils import load_solution_summary, load_compare_metrics, generate_compare_metrics, get_scenario_output_dir

def reset_stuck_scenarios():
    """Reset scenarios that have been stuck in 'solving' state for too long"""
    try:
        stuck_scenarios = Scenario.objects.filter(status="solving")
        if stuck_scenarios.exists():
            for scenario in stuck_scenarios:
                scenario.status = "failed"
                scenario.reason = "Reset: Scenario was stuck in solving state"
                scenario.save()
                st.session_state.global_logs.append(f"Reset stuck scenario: {scenario.name} (ID: {scenario.id})")
    except Exception as e:
        st.session_state.global_logs.append(f"Error resetting stuck scenarios: {str(e)}")

st.set_page_config(page_title="Compare Outputs", page_icon="🔀")

if "global_logs" not in st.session_state:
    st.session_state.global_logs = ["Compare Outputs page initialized."]

# Reset any stuck scenarios when loading the page
reset_stuck_scenarios()

st.title("Compare Scenario Outputs")

def find_all_metrics_files():
    """Scan media/scenarios/ for all compare_metrics.json files (directly in scenario folder)"""
    metrics_files = []
    scenarios_dir = os.path.join(MEDIA_ROOT, "scenarios")
    
    if not os.path.exists(scenarios_dir):
        st.session_state.global_logs.append(f"Scenarios directory not found: {scenarios_dir}")
        return metrics_files
    
    pattern = os.path.join(scenarios_dir, "*", "compare_metrics.json")
    metrics_files = glob.glob(pattern)
    
    st.session_state.global_logs.append(f"Found {len(metrics_files)} metrics files")
    return metrics_files

def load_metrics_data(metrics_files):
    """Load metrics data from all found files, with fallback for missing/empty kpis"""
    metrics_data = []
    default_kpis = {k: 0 for k in ['total_distance', 'total_routes', 'avg_route_distance', 'customers_served', 'max_route_length', 'avg_utilization']}
    for file_path in metrics_files:
        try:
            with open(file_path, 'r') as f:
                metrics = json.load(f)
            scenario_id = os.path.basename(os.path.dirname(file_path))
            metrics['file_path'] = file_path
            metrics['scenario_id'] = scenario_id
            # Fallback for missing/empty kpis
            if 'kpis' not in metrics or not metrics['kpis']:
                metrics['kpis'] = default_kpis.copy()
            metrics_data.append(metrics)
        except Exception as e:
            st.session_state.global_logs.append(f"Error loading metrics file {file_path}: {str(e)}")
    return metrics_data

def scan_for_scenarios_with_metrics():
    """Find all scenarios with metrics and return them"""
    scenarios_with_metrics = []
    
    all_scenarios = Scenario.objects.filter(status__in=["solved", "failed"])
    
    for scenario in all_scenarios:
        output_dir = get_scenario_output_dir(scenario.id)
        metrics_path = os.path.join(output_dir, "compare_metrics.json")
        if os.path.exists(metrics_path):
            scenarios_with_metrics.append(scenario)
            st.session_state.global_logs.append(f"Found metrics for scenario {scenario.name} (ID: {scenario.id})")
        else:
            try:
                metrics = generate_compare_metrics(scenario.id)
                if metrics:
                    scenarios_with_metrics.append(scenario)
                    st.session_state.global_logs.append(f"Generated metrics for scenario {scenario.name} (ID: {scenario.id})")
            except Exception as e:
                st.session_state.global_logs.append(f"Error generating metrics for scenario {scenario.name}: {str(e)}")
    
    if not scenarios_with_metrics:
        metrics_files = find_all_metrics_files()
        metrics_data = load_metrics_data(metrics_files)
        
        for metrics in metrics_data:
            try:
                scenario_id = metrics.get('scenario_id')
                if scenario_id:
                    scenario = Scenario.objects.get(id=scenario_id)
                    if scenario not in scenarios_with_metrics:
                        scenarios_with_metrics.append(scenario)
                        st.session_state.global_logs.append(f"Found metrics file for scenario {scenario.name} (ID: {scenario.id})")
            except Scenario.DoesNotExist:
                st.session_state.global_logs.append(f"Scenario with ID {scenario_id} not found in database")
            except Exception as e:
                st.session_state.global_logs.append(f"Error processing metrics: {str(e)}")
    
    return scenarios_with_metrics

# Section 1: Select Snapshot + Scenarios
st.header("Select Scenarios to Compare")

if "comparison_data" not in st.session_state:
    st.session_state.comparison_data = {
        "tables": {},
        "kpis": {},
        "selected_scenarios": [],
        "selected_snapshot": None
    }

scenarios_with_metrics = scan_for_scenarios_with_metrics()

if not scenarios_with_metrics:
    st.warning("No scenarios with metrics found. Please create and run scenarios first.")
    st.session_state.global_logs.append("No scenarios with metrics found.")
    
    with st.expander("Debug Information", expanded=True):
        st.write("### Checking for metrics files...")
        metrics_files = find_all_metrics_files()
        if metrics_files:
            st.write(f"Found {len(metrics_files)} metrics files:")
            for file in metrics_files:
                st.write(f"- {file}")
            
            st.write("### Sample metrics content:")
            try:
                with open(metrics_files[0], 'r') as f:
                    sample_metrics = json.load(f)
                st.json(sample_metrics)
            except Exception as e:
                st.write(f"Error reading sample metrics: {str(e)}")
        else:
            st.write("No metrics files found. Please run scenarios to generate metrics.")
else:
    snapshots_with_metrics = {}
    for scenario in scenarios_with_metrics:
        if scenario.snapshot not in snapshots_with_metrics:
            snapshots_with_metrics[scenario.snapshot] = []
        snapshots_with_metrics[scenario.snapshot].append(scenario)
    
    snapshot_names = [s.name for s in snapshots_with_metrics.keys()]
    
    if not snapshot_names:
        st.warning("No snapshots with scenarios found. Please create scenarios first.")
        st.session_state.global_logs.append("No snapshots with scenarios found.")
        compare_clicked = False
    else:
        selected_snapshot_name = st.selectbox(
            "Select Snapshot",
            snapshot_names,
            help="Choose a snapshot to compare scenarios from"
        )
        
        selected_snapshot = next((s for s in snapshots_with_metrics.keys() if s.name == selected_snapshot_name), None)
        scenarios = snapshots_with_metrics.get(selected_snapshot, [])
        scenario_names = [s.name for s in scenarios]
        
        if not scenario_names:
            st.warning(f"No processed scenarios found for snapshot '{selected_snapshot_name}'. Please run scenarios first.")
            st.session_state.global_logs.append(f"No processed scenarios found for snapshot '{selected_snapshot_name}'.")
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
                if compare_clicked:
                    st.session_state.global_logs.append(f"Compare button clicked for scenarios: {', '.join(selected_scenarios)}")
                    st.session_state.comparison_data = {
                        "tables": {},
                        "kpis": {},
                        "selected_scenarios": selected_scenarios,
                        "selected_snapshot": selected_snapshot_name
                    }

# Section 2: Show Comparison (After Button Click)
if "selected_scenarios" in st.session_state.comparison_data and st.session_state.comparison_data["selected_scenarios"]:
    selected_scenarios = st.session_state.comparison_data["selected_scenarios"]
    selected_snapshot_name = st.session_state.comparison_data["selected_snapshot"]
    
    try:
        selected_snapshot = Snapshot.objects.get(name=selected_snapshot_name)
        
        st.header("Scenario Comparison")
        tabs = st.tabs(["📊 Tabular Comparison", "📈 KPI Comparison", "📉 Plot Comparison"])
        
        if not st.session_state.comparison_data["tables"] or not st.session_state.comparison_data["kpis"]:
            for scenario_name in selected_scenarios:
                try:
                    scenario = Scenario.objects.get(name=scenario_name, snapshot=selected_snapshot)
                    # st.write(f"Loading data for scenario: {scenario_name} (ID: {scenario.id})")
                    
                    # Load metrics
                    metrics = load_compare_metrics(scenario.id)
                    # st.write(f"Loaded metrics: {metrics}")
                    
                    if not metrics:
                        st.warning(f"No compare_metrics.json for scenario '{scenario_name}'")
                        # Generate metrics if not found
                        metrics = generate_compare_metrics(scenario.id)
                        # st.write(f"Generated metrics: {metrics}")
                    
                    # Always ensure we have KPIs
                    if not metrics or 'kpis' not in metrics:
                        metrics = {
                            'kpis': {
                                'total_distance': 0,
                                'total_routes': 0,
                                'avg_route_distance': 0,
                                'customers_served': 0,
                                'max_route_length': 0,
                                'avg_utilization': 0
                            }
                        }
                    
                    st.session_state.comparison_data["kpis"][scenario_name] = metrics.get('kpis', {})
                    st.session_state.global_logs.append(f"Loaded KPIs for scenario {scenario_name}: {metrics.get('kpis', {})}")
                    
                    # Load solution data
                    solution_data = load_solution_summary(scenario.id)
                    # st.write(f"Loaded solution data: {solution_data}")
                    
                    route_data = []
                    if solution_data and 'routes' in solution_data:
                        for i, route in enumerate(solution_data.get('routes', []), 1):
                            if isinstance(route, list):
                                route_data.append({
                                    'Route ID': f'R{i}',
                                    'Stops': len(route) - 2 if len(route) > 2 else 0,
                                    'Distance (km)': 'N/A',
                                    'Duration (min)': 'N/A'
                                })
                            elif isinstance(route, dict):
                                route_data.append({
                                    'Route ID': f'R{i}',
                                    'Stops': len(route.get('stops', [])),
                                    'Distance (km)': round(route.get('distance', 0), 2) if 'distance' in route else 'N/A',
                                    'Duration (min)': round(route.get('duration', 0), 2) if 'duration' in route else 'N/A'
                                })
                    else:
                        # Always show at least an empty table with headers
                        route_data.append({
                            'Route ID': 'N/A',
                            'Stops': 0,
                            'Distance (km)': 'N/A',
                            'Duration (min)': 'N/A'
                        })
                    
                    st.session_state.comparison_data["tables"][scenario_name] = pd.DataFrame(route_data)
                    # st.write(f"Created route table with {len(route_data)} routes")
                    
                except Exception as e:
                    st.error(f"Error loading data for scenario '{scenario_name}': {str(e)}")
                    st.session_state.global_logs.append(f"Error: {str(e)}")
        
        tables = st.session_state.comparison_data["tables"]
        kpis = st.session_state.comparison_data["kpis"]
        
        # Tab 1: Tabular Comparison
        with tabs[0]:
            st.subheader("Tabular Output Side-by-Side")
            
            if not tables:
                st.info("No tabular data available for the selected scenarios.")
            else:
                cols = st.columns(len(selected_scenarios))
                for i, s in enumerate(selected_scenarios):
                    with cols[i]:
                        st.markdown(f"#### {s}")
                        if s in tables and not tables[s].empty:
                            st.dataframe(tables[s], hide_index=True)
                        else:
                            st.info(f"No route data available for {s}")
        
        # Tab 2: KPI Comparison
        with tabs[1]:
            st.subheader("KPI Table and Radar Chart")
            
            if not kpis:
                st.info("No KPI data available for the selected scenarios.")
            else:
                kpi_display_names = {
                    'total_distance': 'Total Distance (km)',
                    'total_routes': 'Total Routes',
                    'avg_route_distance': 'Avg Route Distance (km)',
                    'customers_served': 'Customers Served',
                    'max_route_length': 'Max Route Length',
                    'avg_utilization': 'Avg Utilization'
                }
                
                # Create numeric DataFrame (all values as float)
                df_kpis = pd.DataFrame({
                    s: {kpi_display_names.get(k, k): float(kpis[s].get(k, 0)) for k in kpi_display_names}
                    for s in selected_scenarios if s in kpis
                })

                # Create display DataFrame with string formatting
                df_display = df_kpis.copy()
                # Convert all numeric columns to string with 2 decimal places
                for col in df_display.columns:
                    df_display[col] = df_display[col].apply(lambda x: f"{x:.2f}")
                # Format utilization as percentage
                if "Avg Utilization" in df_display.index:
                    df_display.loc["Avg Utilization"] = df_display.loc["Avg Utilization"].apply(
                        lambda x: f"{float(x.strip('%')):.1f}%" if isinstance(x, str) else f"{x:.1f}%"
                    )

                # Display with fallback
                try:
                    st.dataframe(df_display)
                except Exception as e:
                    st.error(f"⚠️ Failed to display KPI table: {e}")
                    st.write("Raw numeric DataFrame (fallback):")
                    st.dataframe(df_kpis)
                
                # Create radar chart using raw numeric values from df_kpis
                numeric_kpis = ['total_distance', 'total_routes', 'avg_route_distance', 
                               'customers_served', 'max_route_length', 'avg_utilization']
                
                valid_scenarios = [s for s in selected_scenarios if s in kpis]
                
                if len(valid_scenarios) >= 2:
                    # Create radar chart data using raw numeric values
                    radar_df = pd.DataFrame({
                        scenario_name: [float(kpis[scenario_name].get(kpi, 0)) for kpi in numeric_kpis]
                        for scenario_name in valid_scenarios
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
                    for scenario_name in valid_scenarios:
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
                else:
                    st.info("Need at least 2 scenarios with valid KPI data to create a radar chart.")
        
        # Tab 3: Plot Comparison
        with tabs[2]:
            st.subheader("Bar Chart Comparison")
            
            if not kpis:
                st.info("No KPI data available for the selected scenarios.")
            else:
                bar_kpis = ['total_distance', 'avg_route_distance', 'customers_served']
                bar_kpi_names = [kpi_display_names.get(k, k) for k in bar_kpis]
                
                valid_scenarios = [s for s in selected_scenarios if s in kpis]
                
                if valid_scenarios:
                    bar_data = {
                        'Scenario': valid_scenarios
                    }
                    
                    for kpi, display_name in zip(bar_kpis, bar_kpi_names):
                        bar_data[display_name] = [kpis[s].get(kpi, 0) for s in valid_scenarios]
                    
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
                else:
                    st.info("No valid KPI data available for the selected scenarios.")
    except Exception as e:
        st.error(f"Error displaying comparison: {str(e)}")
        st.session_state.global_logs.append(f"Error: {str(e)}")

# Show the right log panel
show_right_log_panel(st.session_state.global_logs)

# Debug Panel
if st.sidebar.checkbox("Show Debug Info", value=False):
    with st.expander("🔍 Debug Panel", expanded=True):
        st.markdown("### Session State")
        st.json({k: v for k, v in st.session_state.items() if k != "comparison_data"})
        
        st.markdown("### Metrics Files")
        metrics_files = find_all_metrics_files()
        st.write(f"Found {len(metrics_files)} metrics files:")
        for file_path in metrics_files:
            st.write(f"- {file_path}")
            try:
                with open(file_path, 'r') as f:
                    metrics = json.load(f)
                st.write(f"  KPIs: {metrics.get('kpis', {})}")
            except Exception as e:
                st.write(f"  Error loading metrics: {str(e)}")
        
        st.markdown("### Database Scenarios")
        for scenario in Scenario.objects.all():
            st.write(f"Scenario: {scenario.name} (ID: {scenario.id}, Status: {scenario.status})")
            output_dir = get_scenario_output_dir(scenario.id)
            metrics_path = os.path.join(output_dir, "compare_metrics.json")
            if os.path.exists(metrics_path):
                st.write(f"  Metrics exist at: {metrics_path}")
            else:
                st.write(f"  No metrics found at: {metrics_path}")    

def load_compare_metrics(scenario_id):
    """Load comparison metrics from compare_metrics.json, checking multiple possible locations.
    Returns the metrics dict if valid, or empty dict if not found/invalid."""
    scenario_dir = os.path.join("media", "scenarios", str(scenario_id))
    metrics_paths = [
        os.path.join(scenario_dir, "compare_metrics.json"),
        os.path.join(scenario_dir, "outputs", "compare_metrics.json"),
    ]
    
    for path in metrics_paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    metrics = json.load(f)
                if (
                    isinstance(metrics, dict)
                    and metrics.get("status", "") == "solved"
                    and "kpis" in metrics 
                    and isinstance(metrics["kpis"], dict)
                    and metrics["kpis"]  # Ensure kpis dict is not empty
                ):
                    st.session_state.global_logs.append(
                        f"Successfully loaded compare_metrics.json from {path} for scenario {scenario_id}"
                    )
                    return metrics
                else:
                    st.session_state.global_logs.append(
                        f"compare_metrics.json at {path} missing 'kpis' or not solved."
                    )
            except Exception as e:
                st.session_state.global_logs.append(
                    f"Failed to load compare_metrics.json from {path}: {str(e)}"
                )
    
    st.session_state.global_logs.append(
        f"No valid compare_metrics.json found for scenario {scenario_id}"
    )
    return {}  # fallback if not found or invalid    