import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.right_log_panel import show_right_log_panel

st.set_page_config(page_title="1. Data Manager", page_icon="📊")

# Initialize session state for logs if not exists
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

# HOOK: This is where uploaded file should be saved to disk and entry pushed to Django Upload model.
if st.button("Upload File"):
    if uploaded_file is not None:
        # Use file name if no custom name provided
        name = dataset_name if dataset_name else uploaded_file.name
        
        # Mock duplicate check
        if name in ["delivery_data.csv", "order_batch.xlsx"]:
            st.warning("File with this name already exists.")
        else:
            st.success(f"Uploaded successfully as {name}")
    else:
        st.error("Please select a file to upload")

# Dataset Listing Section
st.header("Uploaded Datasets")

# HOOK: Replace mock table below with actual DB-driven upload listing
# Mock data for the table
mock_data = pd.DataFrame([
    {"Name": "delivery_data.csv", "Uploaded At": "2024-05-11 12:34"},
    {"Name": "order_batch.xlsx", "Uploaded At": "2024-05-11 13:21"}
])

# Display the table
st.dataframe(
    mock_data,
    use_container_width=True,
    hide_index=True
)

# Section 1: Upload Data
st.header("Upload Data")

# File uploader
uploaded_file = st.file_uploader(
    "Upload your data file",
    type=["csv", "xlsx"],
    help="Upload a CSV or Excel file containing your data"
)

if uploaded_file is not None:
    st.session_state.global_logs.append(f"File uploaded: {uploaded_file.name}")
    # HOOK: Send file to backend for processing
    st.success(f"File {uploaded_file.name} uploaded successfully!")

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