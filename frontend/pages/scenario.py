import streamlit as st
import pandas as pd
from datetime import datetime
import time
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.right_log_panel import show_right_log_panel

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

# Mock snapshot list
snapshots = ["snap_2024_05_11", "order_batch_snap"]
selected_snapshot = st.selectbox(
    "Select a Snapshot",
    snapshots,
    help="Choose a snapshot to create a scenario from"
)

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

# HOOK: Send GPT tweak prompt to backend and parse response
if st.button("Send to GPT"):
    if gpt_prompt:
        st.session_state.global_logs.append(f"GPT prompt sent: {gpt_prompt[:50]}...")
        st.info("GPT understood: 'Add constraint that no vehicle serves > 5 customers.'")
    else:
        st.warning("Please enter a prompt for GPT")

# Section 3: Run Model Simulation
st.header("Run Model")

# HOOK: Send scenario to solver backend and stream logs
if st.button("Run Model"):
    if not scenario_name:
        st.error("Please enter a scenario name")
    elif not selected_snapshot:
        st.error("Please select a snapshot")
    else:
        # Start timer
        st.session_state.start_time = time.time()
        st.session_state.model_solved = False
        
        # Add solver logs
        solver_logs = [
            "Starting solver...",
            "Parsing scenario parameters...",
            "Running CBC model...",
            "Solution found: 3 routes",
            "Saving results to /media/scenarios"
        ]
        st.session_state.global_logs.extend(solver_logs)
        
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
        st.session_state.global_logs.append(f"Model solved in {st.session_state.elapsed_time:.1f} seconds")

# Show View Output button if model is solved
if st.session_state.model_solved:
    # HOOK: Save scenario status as 'solved' and enable output view
    if st.button("View Output"):
        st.session_state.global_logs.append("Viewing model output")
        st.info("Model output would be displayed here")
        # Mock output display
        st.json({
            "objective_value": 1234.56,
            "solution_time": f"{st.session_state.elapsed_time:.1f} seconds",
            "status": "optimal",
            "constraints_satisfied": True
        })

# HOOK: Save scenario with parameters + GPT output to database
if st.button("Create Scenario"):
    if not scenario_name:
        st.error("Please enter a scenario name")
    elif not selected_snapshot:
        st.error("Please select a snapshot")
    else:
        st.session_state.global_logs.append(f"Creating scenario: {scenario_name}")
        st.success(f"Scenario '{scenario_name}' created successfully!")

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