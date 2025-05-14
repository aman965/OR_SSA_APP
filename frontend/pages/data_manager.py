import os
import sys
import django
from components.right_log_panel import show_right_log_panel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_PATH = os.path.abspath(os.path.join(BASE_DIR, "../backend"))
sys.path.append(BACKEND_PATH)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "orsaas_backend.settings")
django.setup()

import streamlit as st
import pandas as pd
from datetime import datetime
from core.models import Upload

st.set_page_config(page_title="1. Data Manager", page_icon="📊")

if "global_logs" not in st.session_state:
    st.session_state.global_logs = ["Data Manager initialized."]

st.title("Data Manager")

# Test Simulation Toggle
if st.checkbox("Simulate upload success", value=True):
    st.success("Mock upload triggered successfully.")

# File Upload Section
st.header("Upload Dataset")
uploaded_file = st.file_uploader(
    "Choose a file",
    type=['csv', 'xlsx'],
    help="Upload .csv or .xlsx files"
)

dataset_name = st.text_input(
    "Dataset Name",
    help="Enter a custom name for your dataset"
)

# HOOK: Save uploaded file and record in Upload model
if st.button("Upload File"):
    if uploaded_file is not None:
        # Use custom name or file name
        final_name = dataset_name if dataset_name else uploaded_file.name
        # Prevent duplicate
        if Upload.objects.filter(name=final_name).exists():
            st.warning("File with this name already exists.")
        else:
            # Save file to media/uploads/
            upload_dir = os.path.join('media', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            # Save to DB
            rel_path = os.path.relpath(file_path, 'media')
            Upload.objects.create(name=final_name, file=rel_path)
            st.success(f"Uploaded successfully as {final_name}")
    else:
        st.error("Please select a file to upload")

# Dataset Listing Section
st.header("Uploaded Datasets")
uploads = Upload.objects.all().order_by("-uploaded_at")
if uploads.exists():
    df = pd.DataFrame([
        {"Name": u.name, "Uploaded At": u.uploaded_at.strftime("%Y-%m-%d %H:%M:%S")} for u in uploads
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No uploads yet.")

# Section 2: Data Preview
st.header("Data Preview")

# Mock data for preview
data = {
    'Date': pd.date_range(start='2024-01-01', periods=5),
    'Order ID': range(1001, 1006),
    'Customer': ['Customer A', 'Customer B', 'Customer C', 'Customer D', 'Customer E'],
    'Status': ['Pending', 'Completed', 'Pending', 'Completed', 'Pending']
}
df = pd.DataFrame(data)

# Display dataframe
st.dataframe(df)

# Section 3: Data Management
st.header("Data Management")

# Action buttons
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Refresh Data"):
        st.session_state.global_logs.append("Data refresh requested")
        st.info("Data refresh would be triggered here")

with col2:
    if st.button("Export Data"):
        st.session_state.global_logs.append("Data export requested")
        st.info("Data export would be triggered here")

with col3:
    if st.button("Clear Data"):
        st.session_state.global_logs.append("Data clear requested")
        st.info("Data clear would be triggered here")

# Show the right log panel
show_right_log_panel(st.session_state.global_logs)

# Debug Panel
if st.sidebar.checkbox("Show Debug Info", value=False):
    with st.expander("🔍 Debug Panel", expanded=True):
        st.markdown("### Session State")
        st.json(st.session_state) 