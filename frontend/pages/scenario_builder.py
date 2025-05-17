import streamlit as st
import pandas as pd
import time
import sys
import os
import django
import json
import subprocess
from datetime import datetime # Added for time tracking

# Add the backend directory to the Python path for Django ORM access
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_PATH = os.path.abspath(os.path.join(BASE_DIR, "../backend"))
MEDIA_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../media")) # Define MEDIA_ROOT
sys.path.append(BACKEND_PATH)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orsaas_backend.settings')
django.setup()
from core.models import Snapshot, Scenario
from components.right_log_panel import show_right_log_panel

st.set_page_config(page_title="Scenario Builder", page_icon="⚙️", layout="wide")

# Initialize session state for logs if not exists
if "global_logs" not in st.session_state:
    st.session_state.global_logs = ["Scenario Builder initialized."]
if "running_scenario" not in st.session_state:
    st.session_state.running_scenario = None
# Session state for solve start times, keyed by scenario_id
# e.g., st.session_state["scenario_solve_start_time_123"] = datetime_obj

# --- Helper Function to Run Model (Placeholder) ---
def run_model_for_scenario(scenario_id):
    st.session_state.running_scenario = scenario_id
    st.session_state[f"scenario_solve_start_time_{scenario_id}"] = datetime.now()
    redirect_to_results = False
    snapshot_name_for_redirect = None
    scenario_name_for_redirect = None

    try:
        scenario = Scenario.objects.select_related('snapshot').get(id=scenario_id) # Ensure snapshot is loaded
        st.info(f"Starting model run for scenario: {scenario.name} (ID: {scenario.id})...")
        st.session_state.global_logs.append(f"Model run initiated for Scenario ID: {scenario.id} ({scenario.name}).")

        scenario.status = "solving"
        scenario.reason = ""
        scenario.save()
        # st.rerun() 

        scenario_dir = os.path.join(MEDIA_ROOT, "scenarios", str(scenario.id))
        output_dir = os.path.join(scenario_dir, "outputs")
        os.makedirs(scenario_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        st.session_state.global_logs.append(f"Created directories: {scenario_dir} and {output_dir}")
        
        # Initialize paths for solution and failure files to avoid scope issues
        solution_path = os.path.join(output_dir, "solution_summary.json")
        failure_path = os.path.join(output_dir, "failure_summary.json")
        model_lp_path = os.path.join(output_dir, "model.lp")

        scenario_data = {
            "scenario_id": scenario.id,
            "scenario_name": scenario.name,
            "snapshot_id": scenario.snapshot.id,
            "snapshot_name": scenario.snapshot.name,
            "params": {
                "param1": scenario.param1,
                "param2": scenario.param2,
                "param3": scenario.param3,
                "param4": scenario.param4,
                "param5": scenario.param5,
            },
            "gpt_prompt": scenario.gpt_prompt,
            "dataset_file_path": os.path.join(MEDIA_ROOT, scenario.snapshot.linked_upload.file.name)
        }
        scenario_json_path = os.path.join(scenario_dir, "scenario.json")
        with open(scenario_json_path, 'w') as f:
            json.dump(scenario_data, f, indent=4)
        st.session_state.global_logs.append(f"Created scenario.json at {scenario_json_path}")

        progress_bar = st.progress(0, text="Model solving in progress...")
        start_time_for_loop = st.session_state[f"scenario_solve_start_time_{scenario_id}"]

        # Run the VRP solver as a subprocess
        try:
            solver_path = os.path.join(BACKEND_PATH, "solver", "vrp_solver.py")
            result = subprocess.run(
                [sys.executable, solver_path, "--scenario-path", scenario_json_path],
                check=True,
                capture_output=True,
                text=True,
                timeout=180  # Add timeout to prevent infinite runs
            )
            st.session_state.global_logs.append(f"VRP solver output: {result.stdout}")
            
            # Check for solution or failure files in both output_dir and scenario_dir
            alt_solution_path = os.path.join(scenario_dir, "solution_summary.json")
            alt_failure_path = os.path.join(scenario_dir, "failure_summary.json")
            
            # Check for solution file in both locations
            if os.path.exists(solution_path):
                with open(solution_path, 'r') as f:
                    solution = json.load(f)
                scenario.status = "solved"
                scenario.reason = ""
                progress_bar.empty()
                st.success(f"✅ Model for scenario '{scenario.name}' solved successfully!")
                st.session_state.global_logs.append(f"Scenario {scenario.id} solved successfully.")
                
                # Prepare for redirect
                redirect_to_results = True
                snapshot_name_for_redirect = scenario.snapshot.name
                scenario_name_for_redirect = scenario.name
            elif os.path.exists(alt_solution_path):
                import shutil
                shutil.copy2(alt_solution_path, solution_path)
                st.session_state.global_logs.append(f"Copied solution file from {alt_solution_path} to {solution_path}")
                
                with open(solution_path, 'r') as f:
                    solution = json.load(f)
                scenario.status = "solved"
                scenario.reason = ""
                progress_bar.empty()
                st.success(f"✅ Model for scenario '{scenario.name}' solved successfully!")
                st.session_state.global_logs.append(f"Scenario {scenario.id} solved successfully.")
                
                # Prepare for redirect
                redirect_to_results = True
                snapshot_name_for_redirect = scenario.snapshot.name
                scenario_name_for_redirect = scenario.name
            elif os.path.exists(failure_path):
                with open(failure_path, 'r') as f:
                    failure = json.load(f)
                scenario.status = "failed"
                scenario.reason = failure.get("message", "Unknown failure")
                progress_bar.empty()
                st.error(f"Model for scenario '{scenario.name}' failed. Reason: {scenario.reason}")
                st.session_state.global_logs.append(f"Scenario {scenario.id} failed. Reason: {scenario.reason}")
            elif os.path.exists(alt_failure_path):
                import shutil
                shutil.copy2(alt_failure_path, failure_path)
                st.session_state.global_logs.append(f"Copied failure file from {alt_failure_path} to {failure_path}")
                
                with open(failure_path, 'r') as f:
                    failure = json.load(f)
                scenario.status = "failed"
                scenario.reason = failure.get("message", "Unknown failure")
                progress_bar.empty()
                st.error(f"Model for scenario '{scenario.name}' failed. Reason: {scenario.reason}")
                st.session_state.global_logs.append(f"Scenario {scenario.id} failed. Reason: {scenario.reason}")
            else:
                # Check for model.lp file in scenario directory
                model_lp_path = os.path.join(scenario_dir, "model.lp")
                if os.path.exists(model_lp_path):
                    st.session_state.global_logs.append(f"Found model.lp file at {model_lp_path} but no solution or failure files")
                    import shutil
                    os.makedirs(output_dir, exist_ok=True)
                    output_model_lp = os.path.join(output_dir, "model.lp")
                    shutil.copy2(model_lp_path, output_model_lp)
                    st.session_state.global_logs.append(f"Copied model.lp to {output_model_lp}")
                    
                    failure_data = {
                        "status": "error",
                        "message": "Model was created but solver did not produce output files"
                    }
                    with open(failure_path, 'w') as f:
                        json.dump(failure_data, f, indent=4)
                    
                    scenario.status = "failed"
                    scenario.reason = failure_data["message"]
                    scenario.save()
                    progress_bar.empty()
                    st.error(f"Model for scenario '{scenario.name}' failed. {failure_data['message']}")
                else:
                    raise FileNotFoundError("Neither solution nor failure file was created")
                
        except subprocess.CalledProcessError as e:
            scenario.status = "failed"
            error_msg = f"Solver error: {e.stderr}"
            scenario.reason = error_msg
            progress_bar.empty()
            st.error(f"Model for scenario '{scenario.name}' failed. Reason: {error_msg}")
            st.session_state.global_logs.append(f"Scenario {scenario.id} failed. Reason: {error_msg}")
            if not os.path.exists(failure_path):
                with open(failure_path, 'w') as f:
                    json.dump({"status": "error", "message": error_msg}, f, indent=4)
        except Exception as e:
            scenario.status = "failed"
            scenario.reason = f"Error running solver: {str(e)}"
            progress_bar.empty()
            st.error(f"Model for scenario '{scenario.name}' failed. Reason: {scenario.reason}")
            st.session_state.global_logs.append(f"Scenario {scenario.id} failed. Reason: {scenario.reason}")

        # Fallback: If still 'solving' and no output files, mark as failed
        if scenario.status == "solving":
            
            model_lp_exists = os.path.exists(model_lp_path)
            st.session_state.global_logs.append(f"Model LP file exists: {model_lp_exists}")
            
            if not os.path.exists(solution_path) and not os.path.exists(failure_path):
                scenario.status = "failed"
                failure_reason = "Solver did not create any output files."
                if model_lp_exists:
                    failure_reason += " Model LP file was created but solving failed."
                scenario.reason = failure_reason
                scenario.save()
                st.error(f"Model failed: {failure_reason}")
                st.session_state.global_logs.append(f"Scenario {scenario.id} marked as failed due to missing outputs.")

        scenario.save()

    except Scenario.DoesNotExist:
        st.error(f"Scenario with ID {scenario_id} not found.")
        st.session_state.global_logs.append(f"Attempted to run non-existent Scenario ID: {scenario_id}")
    except Exception as e:
        st.error(f"An error occurred while running the model for scenario ID {scenario_id}: {str(e)}")
        st.session_state.global_logs.append(f"Error running model for Scenario ID {scenario_id}: {str(e)}")
        try:
            scenario_obj = Scenario.objects.get(id=scenario_id)
            scenario_obj.status = "failed"
            scenario_obj.reason = f"Execution error: {str(e)}"
            scenario_obj.save()
        except Scenario.DoesNotExist:
            pass 
        except Exception as e_save:
             st.session_state.global_logs.append(f"Error saving fail status for Scenario ID {scenario_id}: {str(e_save)}")
    finally:
        st.session_state.running_scenario = None
        if f"scenario_solve_start_time_{scenario_id}" in st.session_state:
            del st.session_state[f"scenario_solve_start_time_{scenario_id}"]
        
        if redirect_to_results:
            st.session_state["selected_snapshot_for_results"] = snapshot_name_for_redirect
            st.session_state["selected_scenario_for_results"] = scenario_name_for_redirect
            st.info("Redirecting to results page...") # Give user a moment to see the message
            time.sleep(1) # Brief pause before switching
            st.switch_page("pages/view_results.py") # Corrected path for switch_page
        else:
            st.rerun()

st.title("Scenario Builder & Runner")

# Section 1: Create New Scenario
with st.expander("Create New Scenario", expanded=True):
    st.header("Scenario Configuration")
    try:
        snapshots_qs = Snapshot.objects.order_by("-created_at") # Renamed to avoid conflict
        snapshot_names = [s.name for s in snapshots_qs]
        if not snapshot_names:
            st.warning("No snapshots found. Please create a snapshot first on the 'Snapshots' page.")
            selected_snapshot_name_form = None # Unique key for form
            snapshot_obj_form = None
        else:
            selected_snapshot_name_form = st.selectbox("Select Snapshot", snapshot_names, help="Choose an existing snapshot to link this scenario to.", key="new_scenario_snapshot_select")
            snapshot_obj_form = Snapshot.objects.get(name=selected_snapshot_name_form) if selected_snapshot_name_form else None
    except Exception as e:
        st.error(f"Error loading snapshots: {e}")
        st.session_state.global_logs.append(f"Error loading snapshots: {e}")
        # snapshots_qs will be empty or not defined, handle downstream
        snapshot_names = [] 
        selected_snapshot_name_form = None
        snapshot_obj_form = None
        
    scenario_name_form = st.text_input(
        "Scenario Name",
        help="Enter a unique name for this scenario within the selected snapshot",
        key="new_scenario_name"
    )

    st.subheader("Parameters")
    cols_params = st.columns(3)
    with cols_params[0]:
        param1_form = st.number_input("P1 (Float > 0)", min_value=0.01, value=1.0, step=0.1, format="%.2f", help="Parameter 1", key="p1_form")
        param4_form = st.toggle("P4 (Toggle)", value=False, help="Parameter 4", key="p4_form")
    with cols_params[1]:
        param2_form = st.number_input("P2 (Int ≥ 0)", min_value=0, value=0, step=1, help="Parameter 2", key="p2_form")
        param5_form = st.checkbox("P5 (Checkbox)", value=False, help="Parameter 5", key="p5_form")
    with cols_params[2]:
        param3_form = st.slider("P3 (0-100)", min_value=0, max_value=100, value=50, help="Parameter 3", key="p3_form")

    st.subheader("GPT-based Constraint Tweak")
    gpt_prompt_tweak_form = st.text_area(
        "Describe any custom model tweak (optional)",
        height=100,
        help="Enter any specific modifications or constraints for the model using natural language.",
        key="new_scenario_gpt_tweak_form"
    )

    if st.button("Create Scenario", type="primary", key="create_scenario_btn"):
        if not scenario_name_form:
            st.error("Scenario Name cannot be empty.")
        elif not snapshot_obj_form:
            st.error("Please select a Snapshot.")
        else:
            if Scenario.objects.filter(name=scenario_name_form, snapshot=snapshot_obj_form).exists():
                st.warning(f"A scenario named '{scenario_name_form}' already exists for snapshot '{snapshot_obj_form.name}'. Please choose a different name.")
            else:
                try:
                    new_scenario = Scenario.objects.create(
                        name=scenario_name_form, snapshot=snapshot_obj_form,
                        param1=param1_form, param2=param2_form, param3=param3_form, 
                        param4=param4_form, param5=param5_form,
                        gpt_prompt=gpt_prompt_tweak_form, status="created"
                    )
                    st.success(f"✅ Scenario '{new_scenario.name}' created successfully for snapshot '{snapshot_obj_form.name}'.")
                    st.session_state.global_logs.append(f"Scenario '{new_scenario.name}' created. Status: created.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating scenario: {e}")
                    st.session_state.global_logs.append(f"Error creating scenario '{scenario_name_form}': {e}")

st.divider()

st.header("Manage and Run Scenarios")

col_filter1, col_filter2 = st.columns(2)
with col_filter1:
    # Ensure snapshot_names is available from the form loading section or reload if necessary
    # This relies on snapshot_names being populated when the page loads initially.
    filter_snapshot_name = st.selectbox(
        "Filter by Snapshot", 
        options=["All Snapshots"] + (snapshot_names if 'snapshot_names' in locals() and snapshot_names else []),
        key="filter_snapshot"
    )
with col_filter2:
    filter_status = st.selectbox(
        "Filter by Status", 
        options=["All Statuses", "created", "solving", "solved", "failed"], 
        key="filter_status"
    )

scenarios_qs_display = Scenario.objects.select_related('snapshot', 'snapshot__linked_upload').order_by("-created_at") # Renamed for clarity

if filter_snapshot_name != "All Snapshots":
    scenarios_qs_display = scenarios_qs_display.filter(snapshot__name=filter_snapshot_name)
if filter_status != "All Statuses":
    scenarios_qs_display = scenarios_qs_display.filter(status=filter_status)

if not scenarios_qs_display.exists():
    st.info("No scenarios found matching your criteria. Try creating one or adjusting filters.")
else:
    st.subheader(f"Found {scenarios_qs_display.count()} Scenarios")
    
    list_cols_headers = st.columns((2, 2, 1, 1, 1, 1, 2, 2))
    headers = ["Scenario Name", "Snapshot", "P1", "P2", "P3", "Status", "Actions", "Details"]
    for col, header_text in zip(list_cols_headers, headers):
        col.markdown(f"**{header_text}**")
    
    st.markdown("---")

    for scenario_item in scenarios_qs_display: # Renamed to avoid conflict
        list_cols_row = st.columns((2, 2, 1, 1, 1, 1, 2, 2))
        list_cols_row[0].markdown(f"{scenario_item.name}")
        list_cols_row[1].markdown(f"{scenario_item.snapshot.name}")
        list_cols_row[2].caption(f"{scenario_item.param1}")
        list_cols_row[3].caption(f"{scenario_item.param2}")
        list_cols_row[4].caption(f"{scenario_item.param3}")
        
        status_color = "grey"
        if scenario_item.status == "solved": status_color = "green"
        elif scenario_item.status == "failed": status_color = "red"
        elif scenario_item.status == "solving": status_color = "orange"
        list_cols_row[5].markdown(f":{status_color}[●] {scenario_item.status}")

        placeholder_run = list_cols_row[6].empty()
        is_this_scenario_running = (st.session_state.running_scenario == scenario_item.id)

        run_button_disabled = scenario_item.status == "solving" or is_this_scenario_running
        button_text = "▶️ Run Model"
        button_help = "Run optimization model for this scenario"
        if is_this_scenario_running:
            button_text = "⏳ Running..."
            button_help = "This scenario is currently being processed by your session."
        elif scenario_item.status == "solving":
            button_text = "🔄 Queued/Solving..."
            button_help = "This scenario is being processed (possibly by another session or a previous run)."
        
        if placeholder_run.button(button_text, key=f"run_{scenario_item.id}", help=button_help, disabled=run_button_disabled):
            run_model_for_scenario(scenario_item.id)

        with list_cols_row[7].expander("Show Details"):
            st.caption(f"ID: {scenario_item.id}")
            st.caption(f"Created: {scenario_item.created_at.strftime('%Y-%m-%d %H:%M')}")
            st.caption(f"P4 (Toggle): {scenario_item.param4}, P5 (Checkbox): {scenario_item.param5}")
            if scenario_item.gpt_prompt:
                st.caption(f"GPT Tweak: {scenario_item.gpt_prompt[:50]}...")
            if scenario_item.reason:
                 st.caption(f"Failure Reason: {scenario_item.reason}")
            
            scenario_media_dir_item = os.path.join(MEDIA_ROOT, "scenarios", str(scenario_item.id)) # Renamed
            if os.path.exists(scenario_media_dir_item):
                st.caption("Files:")
                for f_name in os.listdir(scenario_media_dir_item):
                    if f_name.endswith(".json") or f_name.endswith(".lp"):
                         st.caption(f"- {f_name}")
            
        st.markdown("---")

show_right_log_panel(st.session_state.global_logs)

if st.sidebar.checkbox("Show Debug Info", value=False, key="scenario_builder_debug"):
    with st.expander("🔍 Debug Panel", expanded=True):
        st.markdown("### Session State")
        st.json(st.session_state)                                        