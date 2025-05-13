import streamlit as st
import pandas as pd
from datetime import datetime
import time
import sys
import os

def safe_switch_page(page_name):
    try:
        pages_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pages"))
        available_pages = [f[:-3] for f in os.listdir(pages_dir) if f.endswith(".py")]
        full_path = os.path.join(pages_dir, f"{page_name}.py")

        st.sidebar.write("🧭 Pages Available:", available_pages)
        st.sidebar.write(f"🔍 Checking existence of: {full_path}")
        st.sidebar.write(f"✅ File Exists: {os.path.exists(full_path)}")

        if page_name in available_pages:
            st.success(f"Switching to: {page_name}")
            st.switch_page(page_name)
        else:
            st.error(f"❌ Page '{page_name}' not found. Ensure it exists in 'pages/' and ends with '.py'")
    except Exception as e:
        st.exception(f"🚨 Unexpected error in safe_switch_page: {e}")

# Add the backend directory to the Python path for Django ORM access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orsaas_backend.settings')
django.setup()
from backend.core.models import Snapshot, Scenario

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from frontend.components.right_log_panel import show_right_log_panel

st.set_page_config(page_title="3. Scenario Builder", page_icon="⚙️")

# Initialize session state for timer and model status
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'model_solved' not in st.session_state:
    st.session_state.model_solved = False
if 'elapsed_time' not in st.session_state:
    st.session_state.elapsed_time = 0
if 'test_scenario_status' not in st.session_state:
    st.session_state.test_scenario_status = 'created'  # created, solving, solved, failed
if 'global_logs' not in st.session_state:
    st.session_state.global_logs = ["Scenario Builder initialized."]

st.title("Scenario Builder")

# Section 1: Scenario Configuration
st.header("Scenario Configuration")

# Load snapshots from DB
snapshots = Snapshot.objects.order_by("-created_at")
snapshot_names = [s.name for s in snapshots]
selected_snapshot_name = st.selectbox("Select Snapshot", snapshot_names) if snapshot_names else None
snapshot_obj = Snapshot.objects.get(name=selected_snapshot_name) if selected_snapshot_name else None

# Scenario name
scenario_name = st.text_input(
    "Scenario Name",
    help="Enter a name for this scenario"
)

# Parameters Section
st.subheader("Parameters")

# Param1: Float input (>0)
param1 = st.number_input(
    "Parameter 1 (Float > 0)",
    min_value=0.1,
    value=1.0,
    step=0.1,
    help="Enter a positive float value"
)

# Param2: Stepper input (int ≥ 0)
param2 = st.number_input(
    "Parameter 2 (Integer ≥ 0)",
    min_value=0,
    value=0,
    step=1,
    help="Enter a non-negative integer"
)

# Param3: Slider (0 to 100)
param3 = st.slider(
    "Parameter 3 (0-100)",
    min_value=0,
    max_value=100,
    value=50,
    help="Select a value between 0 and 100"
)

# Param4: Toggle
param4 = st.toggle(
    "Parameter 4 (Toggle)",
    value=False,
    help="Toggle this parameter on/off"
)

# Param5: Checkbox
param5 = st.checkbox(
    "Parameter 5 (Checkbox)",
    value=False,
    help="Select this parameter"
)

# Section 2: GPT Prompt
st.header("Model Tweaks")

# GPT Prompt input
gpt_prompt = st.text_area(
    "Describe any custom model tweak",
    help="Enter any specific modifications or constraints for the model"
)

# HOOK: Save scenario to DB and mark status as 'created'
if st.button("Create Scenario"):
    if not scenario_name:
        st.error("Please enter a scenario name")
    elif not snapshot_obj:
        st.error("Please select a snapshot")
    else:
        # HOOK: Prevent duplicate scenario creation under same snapshot
        if Scenario.objects.filter(name=scenario_name, snapshot=snapshot_obj).exists():
            st.warning("Scenario with this name already exists for this snapshot.")
        else:
            # Save scenario to DB
            Scenario.objects.create(
                name=scenario_name,
                snapshot=snapshot_obj,
                param1=param1,
                param2=param2,
                param3=param3,
                param4=param4,
                param5=param5,
                gpt_prompt=gpt_prompt,
                gpt_response="Mock GPT response",  # Placeholder
                status="created"
            )
            st.success(f"Scenario '{scenario_name}' created and linked to snapshot '{snapshot_obj.name}'.")
            st.session_state.global_logs.append(f"Scenario '{scenario_name}' created for snapshot '{snapshot_obj.name}'.")

# Section 3: Run Model Simulation
st.header("Run Model")

# HOOK: Send scenario to solver backend and stream logs
if st.button("Run Model"):
    if not scenario_name:
        st.error("Please enter a scenario name")
    elif not selected_snapshot_name:
        st.error("Please select a snapshot")
    else:
        # Start timer
        st.session_state.start_time = time.time()
        st.session_state.model_solved = False
        
        # Show solving message
        solving_placeholder = st.empty()
        while time.time() - st.session_state.start_time < 5:
            elapsed = time.time() - st.session_state.start_time
            solving_placeholder.info(f"Solving... Elapsed time: {elapsed:.1f} seconds")
            time.sleep(0.1)
        
        # Model solved
        st.session_state.model_solved = True
        st.session_state.elapsed_time = time.time() - st.session_state.start_time
        solving_placeholder.success(f"✅ Model Solved Successfully in {st.session_state.elapsed_time:.1f} seconds")
        # Redirect to results if solved
        if st.session_state.model_solved:
            st.session_state["selected_snapshot_for_results"] = selected_snapshot_name
            st.session_state["selected_scenario_for_results"] = scenario_name
            st.success("Scenario solved! Redirecting to results...")
            st.switch_page("view_results")

    # Show View Output button if model is solved
    if st.session_state.model_solved:
        if st.button("View Output"):
            st.info("Model output would be displayed here")
            st.json({
                "objective_value": 1234.56,
                "solution_time": f"{st.session_state.elapsed_time:.1f} seconds",
                "status": "optimal",
                "constraints_satisfied": True
            })

# Test Section for Session State
st.header("Session State Test")
st.subheader("Current Status: " + st.session_state.test_scenario_status)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("Set Created"):
        st.session_state.test_scenario_status = 'created'
        st.session_state.global_logs.append("Status set to: created")
        st.success("Status set to: created")

with col2:
    if st.button("Set Solving"):
        st.session_state.test_scenario_status = 'solving'
        st.session_state.global_logs.append("Status set to: solving")
        st.success("Status set to: solving")

with col3:
    if st.button("Set Solved"):
        st.session_state.test_scenario_status = 'solved'
        st.session_state.global_logs.append("Status set to: solved")
        st.success("Status set to: solved")

with col4:
    if st.button("Set Failed"):
        st.session_state.test_scenario_status = 'failed'
        st.session_state.global_logs.append("Status set to: failed")
        st.success("Status set to: failed")

# Show the right log panel
show_right_log_panel(st.session_state.global_logs)

# Debug Panel
if st.sidebar.checkbox("Show Debug Info", value=False):
    with st.expander("🔍 Debug Panel", expanded=True):
        st.markdown("### Session State")
        st.json(st.session_state) 