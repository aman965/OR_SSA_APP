import streamlit as st
from sqlalchemy.orm import Session

from backend.db_utils import get_session, create_scenario
from frontend.components.navigation import safe_switch_page

st.set_page_config(page_title="Scenario Builder", page_icon="📝")

# ------------------------------------------------------------------------
#  Snapshot context is forwarded from the “Add scenario” button
snapshot_id   = st.session_state.get("prefill_snapshot_id")
snapshot_name = st.session_state.get("prefill_snapshot_name")

if snapshot_id is None:
    st.error("Open this page via a snapshot ➔ *Add scenario* button.")
    st.stop()

st.header("📝  New Scenario")
st.success(f"Snapshot : **{snapshot_name}**")

name        = st.text_input("Scenario name")
description = st.text_area("Description", height=120)

if st.button("💾  Save", type="primary", disabled=not name.strip()):
    with get_session() as db:           # type: Session
        create_scenario(db,
                        name=name.strip(),
                        description=description.strip(),
                        snapshot_id=snapshot_id)
    st.toast("Scenario created ✅")
    st.session_state.pop("prefill_snapshot_id", None)
    st.session_state.pop("prefill_snapshot_name", None)
    safe_switch_page("snapshots")
