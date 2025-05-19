"""
Streamlit page 0 – Data Manager

• Saves the file with Django’s default storage (core.models.Upload).
• Immediately mirrors that record into SQLAlchemy’s UploadedDataset table.
• Creates an initial Snapshot pointing at the new dataset.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from datetime import datetime as _dt
from typing import List

# ── Django bootstrap ──────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]           # project root
sys.path.append(str(BASE_DIR / "backend"))               # for db_utils

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "orsaas_backend.settings")
import django  # noqa: E402

django.setup()

# ──  3-rd-party imports ──────────────────────────────────────────────────
import streamlit as st
import pandas as pd
from django.conf import settings
from django.core.files.base import ContentFile

# ──  Project imports  (Django + SQLAlchemy)  ─────────────────────────────
from core.models import Upload                       # Django model
from backend.db import get_session                   # SQLAlchemy session helper
from backend.db_models import UploadedDataset        # SQLAlchemy models
from backend.db_utils import create_snapshot         # helper we wrote earlier
from components.right_log_panel import show_right_log_panel

# ─────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="1. Data Manager", page_icon="📊")
st.title("Data Manager")

# Session-wide log panel
if "global_logs" not in st.session_state:
    st.session_state.global_logs: List[str] = ["Data Manager initialized ."]

# ── Mock-upload toggle (dev convenience) ─────────────────────────────────
if st.checkbox("Simulate upload success", value=True):
    st.success("Mock upload triggered successfully.")

# ── Upload widget ────────────────────────────────────────────────────────
st.header("Upload Dataset")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["csv", "xlsx"],
    help="Upload .csv or .xlsx files",
)
dataset_name_input = st.text_input(
    "Dataset Name (optional)",
    help="If left blank, the file name (without extension) is used.",
)

# ── Upload handler ───────────────────────────────────────────────────────
if st.button("Upload Dataset"):
    if uploaded_file is None:
        st.error("Please select a file to upload.")
        st.stop()

    file_ext = uploaded_file.name.split(".")[-1].lower()
    if file_ext not in ("csv", "xlsx"):
        st.error("Unsupported file type.")
        st.stop()

    final_name = (
        dataset_name_input.strip()
        if dataset_name_input
        else uploaded_file.name.rsplit(".", 1)[0]
    )

    # Prevent duplicate names at the Django layer
    if Upload.objects.filter(name=final_name).exists():
        st.warning(f"Dataset name '{final_name}' already exists.")
        st.stop()

    try:
        # ---- 1.  Save with Django storage ---------------------------------
        upload_dir = Path(settings.MEDIA_ROOT) / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_content = ContentFile(uploaded_file.getbuffer())
        upload_rec = Upload.objects.create(name=final_name)
        upload_rec.file.save(f"{final_name}.{file_ext}", file_content, save=True)

        rel_path = Path(upload_rec.file.path).relative_to(settings.MEDIA_ROOT)

        # ---- 2.  Mirror into SQLAlchemy tables ----------------------------
        with get_session() as db:
            # 2-A  Insert into UploadedDataset
            ud = UploadedDataset(
                name=final_name,
                file_path=str(rel_path).replace("\\", "/"),
                file_type=file_ext.upper(),
            )
            db.add(ud)
            db.commit()
            db.refresh(ud)

            # 2-B  Create an initial Snapshot for this dataset
            create_snapshot(
                db,
                name=f"{final_name}_snap",
                dataset_id=ud.id,
                file_path=ud.file_path,
            )

        # ---- 3.  UI feedback & preview ------------------------------------
        st.success(f"✅ Dataset '{final_name}' uploaded successfully!")
        st.session_state.global_logs.extend(
            [
                f"Uploaded dataset: {final_name}",
                f"File saved to: {upload_rec.file.path}",
            ]
        )

        if file_ext == "csv":
            df_preview = pd.read_csv(upload_rec.file.path, nrows=200)
        else:
            df_preview = pd.read_excel(upload_rec.file.path, nrows=200)

        st.write("Preview of uploaded data (first 200 rows):")
        st.dataframe(df_preview, use_container_width=True)

    except Exception as e:  # pylint: disable=broad-except
        st.error(f"Error uploading file: {e}")
        st.session_state.global_logs.append(f"Upload failed: {e}")

# ── Dataset listing (from SQLAlchemy, so Snapshots see the same data) ───
st.header("Uploaded Datasets")

with get_session() as db:
    uds = db.query(UploadedDataset).order_by(UploadedDataset.id.desc()).all()

if uds:
    df_list = pd.DataFrame(
        [
            {
                "Name": ud.name,
                "File Type": ud.file_type,
                "Uploaded At": ud.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if hasattr(ud, "created_at")
                else "—",
                "File Path": ud.file_path,
            }
            for ud in uds
        ]
    )
    st.dataframe(df_list, use_container_width=True, hide_index=True)
else:
    st.info("No datasets uploaded yet.")

# ── Management buttons ---------------------------------------------------
st.header("Data Management")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Refresh List"):
        st.session_state.global_logs.append("Dataset list refreshed")
        st.rerun()

with col2:
    if st.button("Export List"):
        if uds:
            csv_bytes = df_list.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Dataset List",
                csv_bytes,
                "dataset_list.csv",
                "text/csv",
            )
            st.session_state.global_logs.append("Dataset list exported")
        else:
            st.info("No datasets to export")

with col3:
    st.button(  # placeholder for future delete feature
        "Delete Selected",
        disabled=True,
        help="Delete functionality coming soon.",
    )

# ── Right-hand log panel + optional debug panel ──────────────────────────
show_right_log_panel(st.session_state.global_logs)

if st.sidebar.checkbox("Show Debug Info", value=False):
    with st.expander("🔍 Debug Panel", expanded=True):
        st.markdown("### Session State")
        st.json(dict(st.session_state))
