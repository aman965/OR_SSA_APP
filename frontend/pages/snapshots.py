import streamlit as st
from sqlalchemy.orm import Session

from backend.db_utils import (
    get_session,                #  ← existing helper
    list_snapshots,
    list_scenarios_for_snapshot,
)
from frontend.components.navigation import safe_switch_page

st.set_page_config(page_title="Snapshots", page_icon="📸")
st.title("📸  Snapshots")

with get_session() as db:        # type: Session
    snapshots = list_snapshots(db)

if not snapshots:
    st.info("No snapshots yet. Upload a dataset first.")
    st.stop()

for snap in snapshots:
    with st.expander(f"📸  {snap.name}", expanded=False):
        st.caption(f"Created : {snap.created_at:%d-%b-%Y %H:%M}")

        cols = st.columns([4, 1])
        with cols[0]:
            scenarios = list_scenarios_for_snapshot(db, snap.id)
            if scenarios:
                for scn in scenarios:
                    st.markdown(
                        f"* **{scn.name}**  — _{scn.created_at:%d-%b-%Y}_"
                    )
            else:
                st.write("_(no scenarios yet)_")

        with cols[1]:
            if st.button("➕ Add scenario", key=f"add_scn_{snap.id}",
                         use_container_width=True):
                st.session_state["prefill_snapshot_id"] = snap.id
                st.session_state["prefill_snapshot_name"] = snap.name
                safe_switch_page("2_📝_scenario_builder")
