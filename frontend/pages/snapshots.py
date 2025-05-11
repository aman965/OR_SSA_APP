import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.right_log_panel import show_right_log_panel

st.set_page_config(page_title="2. Snapshots", page_icon="📸")

# Initialize session state for logs if not exists
if "global_logs" not in st.session_state:
    st.session_state.global_logs = ["Snapshots page initialized."]

st.title("Snapshots")

# Section 1: Create Snapshot
st.header("Create Snapshot")

# Snapshot name
snapshot_name = st.text_input(
    "Snapshot Name",
    help="Enter a name for this snapshot"
)

# Description
description = st.text_area(
    "Description",
    help="Enter a description for this snapshot"
)

# HOOK: Create snapshot in backend
if st.button("Create Snapshot"):
    if not snapshot_name:
        st.error("Please enter a snapshot name")
    else:
        st.session_state.global_logs.append(f"Creating snapshot: {snapshot_name}")
        st.success(f"Snapshot '{snapshot_name}' created successfully!")

# Section 2: Snapshots & Scenarios
st.header("Snapshots & Scenarios")

snapshots = {
    "snap_2024_05_11": [
        {"name": "Scenario 1", "status": "solved", "reason": ""},
        {"name": "Scenario 2", "status": "failed", "reason": "Vehicle limit exceeded"}
    ],
    "order_batch_snap": [
        {"name": "Scenario 3", "status": "solved", "reason": ""}
    ]
}

for snap_name, scenarios in snapshots.items():
    with st.expander(f"📦 {snap_name}"):
        for scenario in scenarios:
            col1, col2, col3 = st.columns([3, 1, 2])
            with col1:
                st.markdown(f"**{scenario['name']}**")
            with col2:
                st.markdown(f"Status: `{scenario['status']}`")
            with col3:
                if scenario["status"] == "solved":
                    if st.button(f"View Results ({snap_name} - {scenario['name']})", key=f"view_{snap_name}_{scenario['name']}"):
                        # Use sample data for smooth flow
                        snapshot_name = snap_name
                        scenario_name = scenario["name"]
                        st.session_state["selected_snapshot_for_results"] = snapshot_name
                        st.session_state["selected_scenario_for_results"] = scenario_name
                        st.session_state.global_logs.append(f"View Results for {snapshot_name} - {scenario_name}")
                        st.switch_page("pages/view_results.py")
                elif scenario["status"] == "failed":
                    st.button("Failed", disabled=True, help=scenario["reason"] or "No reason provided", key=f"fail_{snap_name}_{scenario['name']}")
                else:
                    st.button("Not Solved", disabled=True, help="Scenario not yet solved", key=f"not_solved_{snap_name}_{scenario['name']}")

# Debug Panel Toggle
if st.sidebar.checkbox("Show Debug Info", value=False):
    with st.expander("🔍 Debug Panel", expanded=True):
        st.markdown("### Session State")
        st.json(st.session_state)

from components.right_log_panel import show_right_log_panel
show_right_log_panel(["Navigated to View Results"]) 