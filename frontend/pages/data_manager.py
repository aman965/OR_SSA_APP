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

# File uploader with type restriction
uploaded_file = st.file_uploader(
    "Choose a file",
    type=['csv', 'xlsx'],
    help="Upload .csv or .xlsx files"
)

# Dataset name input
dataset_name = st.text_input(
    "Dataset Name (optional)",
    help="Enter a custom name for your dataset. If left blank, will use the file name."
)

# Upload button and processing
if st.button("Upload Dataset"):
    if uploaded_file is not None:
        # Get file extension and determine type
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        # Use custom name or file name without extension
        final_name = dataset_name.strip() if dataset_name else uploaded_file.name.rsplit(".", 1)[0]
        
        # Prevent duplicate names
        if Upload.objects.filter(name=final_name).exists():
            st.warning(f"Dataset name '{final_name}' already exists. Please choose a different name.")
        else:
            try:
                # Create upload directory if it doesn't exist
                upload_dir = os.path.join('media', 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Save file with original extension
                file_path = os.path.join(upload_dir, f"{final_name}.{file_ext}")
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Save to database using Django ORM
                rel_path = os.path.relpath(file_path, 'media')
                Upload.objects.create(
                    name=final_name,
                    file=rel_path
                )
                
                st.success(f"✅ Dataset '{final_name}' uploaded successfully!")
                st.session_state.global_logs.append(f"Uploaded dataset: {final_name}")
                
                # Preview uploaded data
                if file_ext == 'csv':
                    df = pd.read_csv(file_path)
                else:  # xlsx
                    df = pd.read_excel(file_path)
                st.write("Preview of uploaded data:")
                st.dataframe(df.head(), use_container_width=True)
                
            except Exception as e:
                st.error(f"Error uploading file: {str(e)}")
                st.session_state.global_logs.append(f"Upload failed: {str(e)}")
    else:
        st.error("Please select a file to upload")

# Dataset Listing Section
st.header("Uploaded Datasets")
uploads = Upload.objects.all().order_by("-uploaded_at")
if uploads.exists():
    df = pd.DataFrame([
        {
            "Name": u.name,
            "File Type": u.file.name.split('.')[-1].upper(),
            "Uploaded At": u.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
            "File Path": u.file.name
        } for u in uploads
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No datasets uploaded yet.")

# Data Management Section
st.header("Data Management")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Refresh List"):
        st.session_state.global_logs.append("Dataset list refreshed")
        st.rerun()

with col2:
    if st.button("Export List"):
        if uploads.exists():
            export_df = pd.DataFrame([
                {
                    "Name": u.name,
                    "File Type": u.file.name.split('.')[-1].upper(),
                    "Uploaded At": u.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "File Path": u.file.name
                } for u in uploads
            ])
            st.session_state.global_logs.append("Dataset list exported")
            st.download_button(
                "Download Dataset List",
                export_df.to_csv(index=False).encode('utf-8'),
                "dataset_list.csv",
                "text/csv"
            )
        else:
            st.info("No datasets to export")

with col3:
    if st.button("Delete Selected"):
        st.warning("Delete functionality will be implemented in future updates")
        st.session_state.global_logs.append("Delete operation requested (not implemented)")

# Show the right log panel
show_right_log_panel(st.session_state.global_logs)

# Debug Panel
if st.sidebar.checkbox("Show Debug Info", value=False):
    with st.expander("🔍 Debug Panel", expanded=True):
        st.markdown("### Session State")
        st.json(st.session_state) 