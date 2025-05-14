import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import datetime
import streamlit as st
from backend.db_utils import get_session
from backend.db_models import UploadedDataset

def handle_file_upload():
    uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])
    custom_name = st.text_input("Optional Dataset Name (leave blank to use file name)")
    submit = st.button("Upload")

    if uploaded_file and submit:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        file_type = "CSV" if file_ext == "csv" else "XLSX"
        dataset_name = custom_name.strip() or uploaded_file.name.rsplit(".", 1)[0]

        session = get_session()

        # Check for duplicate dataset name
        if session.query(UploadedDataset).filter_by(name=dataset_name).first():
            st.warning("Dataset name already exists. Choose a different name.")
            return

        # Save file
        os.makedirs("media/uploads", exist_ok=True)
        saved_path = f"media/uploads/{dataset_name}.{file_ext}"
        with open(saved_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Save metadata
        new_dataset = UploadedDataset(
            name=dataset_name,
            file_path=saved_path,
            file_type=file_type,
            upload_time=datetime.datetime.now()
        )
        session.add(new_dataset)
        session.commit()

        st.success(f"Upload successful. Dataset '{dataset_name}' saved.")

def main():
    st.title("Upload Dataset")
    st.write("Upload your CSV or Excel file for analysis")
    handle_file_upload()

if __name__ == "__main__":
    main() 