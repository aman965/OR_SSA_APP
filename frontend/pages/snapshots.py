import sys
import os
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_PATH = os.path.abspath(os.path.join(BASE_DIR, "../backend"))
sys.path.append(BACKEND_PATH)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orsaas_backend.settings')
django.setup()
from core.models import Upload, Snapshot

from django.conf import settings

st.set_page_config(page_title="2. Snapshots", page_icon="📸")

# Initialize session state for logs if not exists
if "global_logs" not in st.session_state:
    st.session_state.global_logs = ["Snapshots page initialized."]

st.title("Snapshots")

# Section 1: Create Snapshot
st.header("Create Snapshot")

# Get all uploads for selection
datasets = Upload.objects.all().order_by("-uploaded_at")
dataset_names = [u.name for u in datasets]
selected_upload_name = st.selectbox(
    "Select Dataset",
    dataset_names,
    help="Choose a dataset to create a snapshot from"
) if dataset_names else None

snapshot_name = st.text_input(
    "Snapshot Name",
    help="Enter a name for this snapshot"
)

description = st.text_area(
    "Description",
    help="Enter a description for this snapshot"
)

# HOOK: Save snapshot to DB and link to selected Upload
if st.button("Create Snapshot"):
    if not snapshot_name:
        st.error("Please enter a snapshot name")
    elif not selected_upload_name:
        st.error("Please select a dataset")
    elif Snapshot.objects.filter(name=snapshot_name).exists():
        st.warning("Snapshot with this name already exists.")
    else:
        upload_obj = Upload.objects.get(name=selected_upload_name)
        # Create snapshot with description
        snapshot = Snapshot.objects.create(
            name=snapshot_name,
            linked_upload=upload_obj,
            description=description
        )
        
        try:
            import pandas as pd
            from components.file_utils import save_snapshot_file
            
            if upload_obj.file.name.endswith('.csv'):
                df = pd.read_csv(upload_obj.file.path)
            else:  # xlsx
                df = pd.read_excel(upload_obj.file.path)
                
            snapshot_path = save_snapshot_file(snapshot.id, df)
            st.session_state.global_logs.append(f"Snapshot file created at: {snapshot_path}")
        except Exception as e:
            st.warning(f"Could not create physical snapshot file: {str(e)}")
            st.session_state.global_logs.append(f"Error creating snapshot file: {str(e)}")
            
        st.success(f"Snapshot '{snapshot_name}' created successfully.")
        st.session_state.global_logs.append(f"Snapshot '{snapshot_name}' created.")

# Section 2: Snapshots & Scenarios
st.header("Snapshots & Scenarios")
snapshots = Snapshot.objects.select_related("linked_upload").order_by("-created_at")
for snap in snapshots:
    with st.expander(f"📦 {snap.name}"):
        # Snapshot info section
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**Linked Dataset:** {snap.linked_upload.name if snap.linked_upload else 'N/A'}")
            st.markdown(f"**Created At:** {snap.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            st.markdown(f"**Description:** {snap.description or 'No description provided'}")
        
        with col2:
            # Add "Create Scenario" button for this snapshot
            if st.button(f"➕ Create Scenario", key=f"create_scenario_{snap.name}", help=f"Create a new scenario for snapshot '{snap.name}'"):
                # Set the selected snapshot in session state and redirect to scenario builder
                st.session_state["selected_snapshot_for_scenario_builder"] = snap.name
                st.session_state.global_logs.append(f"Redirecting to scenario builder with snapshot: {snap.name}")
                st.switch_page("pages/scenario_builder.py")
        
        # List real scenarios for this snapshot
        scenarios = snap.scenario_set.all().order_by("-created_at")
        if scenarios:
            st.markdown("### Scenarios")
            for scenario in scenarios:
                col1, col2, col3 = st.columns([3, 1, 2])
                with col1:
                    st.markdown(f"**{scenario.name}**")
                with col2:
                    st.markdown(f"Status: `{scenario.status}`")
                with col3:
                    if scenario.status == "solved":
                        if st.button(f"View Results ({snap.name} - {scenario.name})", key=f"view_{snap.name}_{scenario.name}"):
                            st.session_state["selected_snapshot_for_results"] = snap.name
                            st.session_state["selected_scenario_for_results"] = scenario.name
                            st.session_state.global_logs.append(f"View Results for {snap.name} - {scenario.name}")
                            st.write("Selected Snapshot:", snap.name)
                            st.write("Selected Scenario:", scenario.name)
                            st.switch_page("pages/view_results.py")
                    elif scenario.status == "failed":
                        st.button("Failed", disabled=True, help=scenario.reason or "No reason provided", key=f"fail_{snap.name}_{scenario.name}")
                        st.write("Selected Snapshot:", snap.name)
                        st.write("Selected Scenario:", scenario.name)
                    else:
                        st.button("Not Solved", disabled=True, help="Scenario not yet solved", key=f"not_solved_{snap.name}_{scenario.name}")
                        st.write("Selected Snapshot:", snap.name)
                        st.write("Selected Scenario:", scenario.name)

# Debug Panel Toggle
if st.sidebar.checkbox("Show Debug Info", value=False):
    with st.expander("🔍 Debug Panel", expanded=True):
        st.markdown("### Session State")
        st.json(st.session_state)

from components.right_log_panel import show_right_log_panel
show_right_log_panel(["Snapshots page loaded."])    