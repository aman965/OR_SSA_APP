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

sys.path.append(os.path.join(BACKEND_PATH, "services"))

st.set_page_config(page_title="View Results", page_icon="📊", layout="wide")

# Initialize session state for logs if not exists
if "global_logs" not in st.session_state:
    st.session_state.global_logs = ["View Results page initialized."]

# Initialize session state for GPT analysis
if "gpt_analysis_result" not in st.session_state:
    st.session_state.gpt_analysis_result = None
if "gpt_analysis_loading" not in st.session_state:
    st.session_state.gpt_analysis_loading = False

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

    # Applied Constraints Section
    if 'applied_constraints' in solution and solution['applied_constraints']:
        st.subheader("🎯 Applied Constraints")
        constraints_df = pd.DataFrame(solution['applied_constraints'])
        
        # Enhanced constraint display
        for i, constraint in enumerate(solution['applied_constraints']):
            with st.expander(f"Constraint {i+1}: {constraint.get('type', 'Unknown')}", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("**Original Prompt:**")
                    st.code(constraint.get('original', 'N/A'))
                with col2:
                    st.write("**Constraint Type:**")
                    st.info(constraint.get('type', 'Unknown'))
                with col3:
                    st.write("**Parsing Method:**")
                    method = constraint.get('method', 'unknown')
                    if method == 'pattern_matching':
                        st.success("🎯 Pattern Matching")
                        st.caption("Confidence: ≥85% (High)")
                    elif method == 'llm':
                        st.warning("🤖 LLM Parsing")  
                        st.caption("Confidence: <85% (Used OpenAI)")
                    elif method == 'fallback':
                        st.info("🔄 Fallback Parsing")
                        st.caption("No pattern match, OpenAI unavailable")
                    elif method == 'fallback_pattern':
                        st.success("🔍 Fallback Pattern Match")
                        st.caption("Matched improved pattern rules")
                    else:
                        st.error("❓ Unknown Method")
                        st.caption(f"Method: {method}")
    else:
        st.subheader("🎯 Applied Constraints")
        st.info("No custom constraints were applied to this scenario.")

    # GPT Constraint Prompt Display
    if scenario.gpt_prompt and scenario.gpt_prompt.strip():
        st.subheader("🗣️ User Constraint Prompt")
        st.info(f"💬 **Original Request:** {scenario.gpt_prompt}")
        if 'applied_constraints' not in solution or not solution['applied_constraints']:
            st.warning("⚠️ Constraint prompt was provided but no constraints were successfully applied.")

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

    # Load demand data for route calculations
    try:
        dataset_path = os.path.join(MEDIA_ROOT, scenario.snapshot.linked_upload.file.name)
        demand_df = pd.read_csv(dataset_path)
        demand_dict = {}
        if 'demand' in demand_df.columns:
            demand_dict = dict(zip(demand_df.index, demand_df['demand']))
        else:
            st.warning("No demand column found in dataset")
    except Exception as e:
        st.warning(f"Could not load demand data: {e}")
        demand_dict = {}

    # Enhanced Routes Table with Load/Demand
    st.subheader("Route Details")
    try:
        route_rows = []
        for i, route in enumerate(solution.get("routes", []), 1):
            route_id = f"R{i}"
            # Handle both old (list) and new (dict) route formats
            if isinstance(route, dict):
                stops = len(route.get("stops", [])) - 2 if len(route.get("stops", [])) > 2 else 0
                distance = round(route.get("distance", 0), 2)
                duration = round(route.get("duration", 0), 2)
                stop_sequence = route.get("stops", [])
                sequence = " → ".join(str(node) for node in stop_sequence)
            else:
                stops = len(route) - 2 if len(route) > 2 else 0
                distance = None
                duration = None
                stop_sequence = route
                sequence = " → ".join(str(node) for node in route)
            
            # Calculate total load/demand for this route
            total_load = 0
            if demand_dict:
                # Sum demand for all customer stops (excluding depot)
                customer_stops = [stop for stop in stop_sequence if stop != 0]  # Assuming depot is node 0
                total_load = sum(demand_dict.get(stop, 0) for stop in customer_stops)
            
            route_rows.append({
                "Route ID": route_id,
                "Stops": stops,
                "Total Load": total_load if demand_dict else "N/A",
                "Distance (km)": distance,
                "Duration (min)": duration,
                "Sequence": sequence
            })
        
        # Display enhanced route table
        route_df = pd.DataFrame(route_rows)
        st.dataframe(route_df, use_container_width=True)
        
        # Load utilization metrics
        if demand_dict:
            total_demand = sum(demand_dict.get(i, 0) for i in demand_dict.keys() if i != 0)  # Exclude depot
            vehicle_capacity = scenario.param1  # P1 is capacity
            
            st.subheader("📊 Load Analysis")
            load_cols = st.columns(3)
            with load_cols[0]:
                st.metric("Total Demand", f"{total_demand} units")
            with load_cols[1]:
                max_load_per_route = max([row["Total Load"] for row in route_rows if row["Total Load"] != "N/A"], default=0)
                st.metric("Max Route Load", f"{max_load_per_route} units")
            with load_cols[2]:
                if vehicle_capacity and max_load_per_route:
                    utilization = (max_load_per_route / vehicle_capacity) * 100
                    st.metric("Max Utilization", f"{utilization:.1f}%")
                else:
                    st.metric("Max Utilization", "N/A")
                    
    except Exception as e:
        st.error(f"⚠️ Error loading Route Details: {e}")
        import traceback
        st.code(traceback.format_exc())

    # Enhanced Visualizations
    st.subheader("Route Analysis")
    viz_cols = st.columns(2)
    
    with viz_cols[0]:
        # Distance per Route Bar Chart
        fig_distance = px.bar(
            pd.DataFrame(route_rows),
            x="Route ID",
            y="Distance (km)",
            title="Distance per Route",
            color="Distance (km)",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_distance, use_container_width=True)
    
    with viz_cols[1]:
        # Load per Route Bar Chart (if demand data available)
        if demand_dict:
            fig_load = px.bar(
                pd.DataFrame(route_rows),
                x="Route ID", 
                y="Total Load",
                title="Load per Route",
                color="Total Load",
                color_continuous_scale="Plasma"
            )
            st.plotly_chart(fig_load, use_container_width=True)
        else:
            # Fallback to stops per route
            fig_stops = px.bar(
                pd.DataFrame(route_rows),
                x="Route ID",
                y="Stops",
                title="Stops per Route",
                color="Stops",
                color_continuous_scale="Plasma"
            )
            st.plotly_chart(fig_stops, use_container_width=True)

    st.subheader("🤖 GPT-powered Solution Analysis")
    st.write("Ask questions about this solution in natural language. Examples:")
    st.info("""
    - "What is the average utilization by vehicle?"
    - "Show a table of stops per route"
    - "Plot the distance distribution across routes"
    - "Which route has the highest demand?"
    """)
    
    # User input for GPT analysis
    user_question = st.text_input("Enter your question about the solution:", key="gpt_question")
    
    # Function to run GPT analysis
    def run_gpt_analysis():
        st.session_state.gpt_analysis_loading = True
        st.session_state.global_logs.append(f"Starting GPT analysis for scenario {scenario.id} with question: {user_question}")
        try:
            sys.path.append(os.path.join(BACKEND_PATH, "services"))
            try:
                from gpt_output_analysis_new import analyze_output
                st.session_state.global_logs.append(f"Using new gpt_output_analysis_new module")
            except ImportError:
                # Fall back to the old implementation if the new one isn't available
                from gpt_output_analysis import analyze_output
                st.session_state.global_logs.append(f"Using original gpt_output_analysis module")
            
            st.session_state.global_logs.append(f"Calling analyze_output with question: {user_question} and scenario_id: {scenario.id}")
            result = analyze_output(user_question, scenario.id)
            st.session_state.global_logs.append(f"Got result from analyze_output: {result}")
            
            if not isinstance(result, dict) or 'type' not in result or 'data' not in result:
                st.session_state.global_logs.append(f"Invalid result format: {result}")
                result = {"type": "error", "data": "Invalid response format from analysis service"}
            
            st.session_state.gpt_analysis_result = result
            st.session_state.global_logs.append(f"GPT analysis completed with result type: {st.session_state.gpt_analysis_result.get('type', 'unknown')}")
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            st.session_state.global_logs.append(f"Error in GPT analysis: {str(e)}")
            st.session_state.global_logs.append(f"Error details: {error_details}")
            st.session_state.gpt_analysis_result = {"type": "error", "data": f"Error: {str(e)}"}
        
        st.session_state.gpt_analysis_loading = False
    
    # Submit button for GPT analysis
    analyze_col1, analyze_col2 = st.columns([3, 1])
    
    st.session_state.global_logs.append(f"Button state check - user_question: '{user_question}', is empty: {not user_question}, loading: {st.session_state.gpt_analysis_loading}")
    
    with analyze_col2:
        if st.button("Analyze", key="analyze_button", use_container_width=True):
            if user_question:
                st.session_state.global_logs.append("Analyze button clicked")
                with analyze_col1:
                    st.write("Starting analysis...")
                run_gpt_analysis()
                try:
                    st.rerun()  # For Streamlit >= 1.27.0
                except:
                    pass  # Continue without rerunning if not available
            else:
                st.warning("Please enter a question first")
                st.session_state.global_logs.append("Analyze button clicked but no question entered")
    
    if st.session_state.gpt_analysis_loading:
        with st.spinner("Analyzing solution..."):
            st.empty()
    
    if st.session_state.gpt_analysis_result:
        result = st.session_state.gpt_analysis_result
        result_type = result.get("type", "")
        result_data = result.get("data", "")
        
        if result_type == "error":
            st.error(f"Error: {result_data}")
        elif result_type == "value":
            st.success(f"Answer: {result_data}")
        elif result_type == "table":
            try:
                if len(result_data) > 1:
                    headers = result_data[0]
                    rows = result_data[1:]
                    df = pd.DataFrame(rows, columns=headers)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("Table data is empty or invalid")
            except Exception as e:
                st.error(f"Error displaying table: {str(e)}")
                st.json(result_data)
        elif result_type == "chart":
            try:
                st.session_state.global_logs.append(f"Chart data: {result_data}")
                
                chart_type = result_data.get("chart_type", "bar")
                title = result_data.get("title", "Chart")
                
                labels = result_data.get("labels", [])
                values = result_data.get("values", [])
                
                if not isinstance(labels, list):
                    st.session_state.global_logs.append(f"Converting labels to list: {labels}")
                    labels = [str(labels)]
                
                if not isinstance(values, list):
                    st.session_state.global_logs.append(f"Converting values to list: {values}")
                    try:
                        values = [float(values)]
                    except (ValueError, TypeError):
                        values = [0]
                
                if not isinstance(labels, list) or not isinstance(values, list):
                    st.warning("Invalid chart data: labels and values must be lists")
                    st.json(result_data)
                    st.session_state.global_logs.append(f"Invalid chart data: labels={type(labels)}, values={type(values)}")
                elif len(labels) == 0 or len(values) == 0:
                    st.warning("Empty chart data: labels or values are empty")
                    st.json(result_data)
                    st.session_state.global_logs.append(f"Empty chart data: labels={len(labels)}, values={len(values)}")
                elif len(labels) != len(values):
                    st.warning(f"Mismatched chart data: labels ({len(labels)}) and values ({len(values)}) must have the same length")
                    if len(labels) < len(values):
                        labels.extend([f"Item {i+1}" for i in range(len(labels), len(values))])
                    else:
                        values.extend([0] * (len(labels) - len(values)))
                    st.session_state.global_logs.append(f"Padded chart data: labels={len(labels)}, values={len(values)}")
                
                data = {"labels": labels, "values": values}
                st.session_state.global_logs.append(f"Creating DataFrame with data: {data}")
                
                chart_df = pd.DataFrame(data)
                st.session_state.global_logs.append(f"Created DataFrame with shape {chart_df.shape}")
                
                try:
                    if chart_type == "bar":
                        fig = px.bar(
                            data_frame=chart_df,
                            x="labels",
                            y="values",
                            title=title,
                            labels={"labels": "Category", "values": "Value"}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    elif chart_type == "line":
                        fig = px.line(
                            data_frame=chart_df,
                            x="labels",
                            y="values",
                            title=title,
                            labels={"labels": "Category", "values": "Value"}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    elif chart_type == "pie":
                        fig = px.pie(
                            data_frame=chart_df,
                            names="labels",
                            values="values",
                            title=title
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning(f"Unsupported chart type '{chart_type}', falling back to bar chart")
                        fig = px.bar(
                            data_frame=chart_df,
                            x="labels",
                            y="values",
                            title=f"{title} (Fallback Bar Chart)",
                            labels={"labels": "Category", "values": "Value"}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating chart: {str(e)}")
                    st.session_state.global_logs.append(f"Error creating chart: {str(e)}")
                    st.dataframe(chart_df)
            except Exception as e:
                st.error(f"Error processing chart data: {str(e)}")
                st.session_state.global_logs.append(f"Error processing chart data: {str(e)}")
                import traceback
                st.session_state.global_logs.append(traceback.format_exc())
                st.json(result_data)
        else:
            st.json(result_data)

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