import streamlit as st
from frontend.components.navigation import safe_switch_page
from typing import Any, Dict

st.set_page_config(page_title="Snapshot Builder", page_icon="📸")

st.header("📸  New Snapshot")

# ── choose dataset -------------------------------------------------------
# TODO: Replace with new data layer once repository adapter is implemented
def get_session():
    """Temporary stub to maintain page functionality during refactor."""
    raise NotImplementedError("get_session is removed in Django refactor")

def create_snapshot(*args: Any, **kwargs: Any):
    raise NotImplementedError("create_snapshot is removed in Django refactor")

class UploadedDataset:  # type: ignore
    pass

with get_session() as db:                 # type: Session
    datasets = (
        db.query(UploadedDataset)
          .order_by(UploadedDataset.id.desc())
          .all()
    )

if not datasets:
    st.warning("No datasets available. Upload one first.")
    st.stop()

dataset_map = {f"{ds.name}  ({ds.file_type})": ds for ds in datasets}
sel_label = st.selectbox("Dataset *", options=list(dataset_map.keys()))
sel_dataset = dataset_map[sel_label]

# ── snapshot meta --------------------------------------------------------
name        = st.text_input("Snapshot name *")
description = st.text_area("Description")

# ── save -----------------------------------------------------------------
if st.button("💾  Save", type="primary",
             disabled=not (name.strip() and sel_dataset)):
    with get_session() as db:             # type: Session
        try:
            create_snapshot(
                db,
                name=name.strip(),
                dataset_id=sel_dataset.id,
                file_path=sel_dataset.file_path,
            )
            st.toast("Snapshot created ✅")
            safe_switch_page("1_📸_snapshots")
        except Exception:
            st.error("A snapshot with that name already exists.")
