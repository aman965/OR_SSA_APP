import streamlit as st
import requests
import os
import datetime
import pandas as pd
from frontend.components.api_client import create_snapshot, get_datasets
from collections import defaultdict

API = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Snapshots", page_icon="📸")
st.header("📸 Snapshots")

# --- Add Scenario Redirect (instant) ---
if 'add_scenario_redirect' in st.session_state:
    snap_id = st.session_state.pop('add_scenario_redirect')
    st.session_state['selected_snapshot_for_new_scenario'] = snap_id
    st.switch_page("pages/scenario_builder.py")
    st.stop()

# --- Fast snapshot summary fetch ---
@st.cache_data(ttl=10, show_spinner=False)
def get_snapshot_summaries():
    token = st.session_state.get("token", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.get(f"{API}/api/snapshots/summary/", headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        st.error(f"Failed to fetch snapshot summaries: {r.status_code}")
        return []

# --- Shimmer loader (placeholder) ---
def shimmer_placeholder():
    for _ in range(3):
        with st.container():
            st.markdown(
                """
                <div style='background: #f6f6f6; border-radius: 8px; height: 60px; margin-bottom: 10px; width: 100%; animation: shimmer 1.5s infinite linear;'>
                </div>
                <style>
                @keyframes shimmer {
                  0% { background-position: -1000px 0; }
                  100% { background-position: 1000px 0; }
                }
                div[style*='animation: shimmer'] {
                  background: linear-gradient(90deg, #f6f6f6 25%, #e0e0e0 50%, #f6f6f6 75%);
                  background-size: 200% 100%;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

# --- Create New Snapshot Section ---
if 'show_create_snapshot_form' not in st.session_state:
    st.session_state['show_create_snapshot_form'] = False

if not st.session_state['show_create_snapshot_form']:
    if st.button("Create New Snapshot", key="show_create_snapshot_btn"):
        st.session_state['show_create_snapshot_form'] = True
        st.rerun()
else:
    with st.form("create_snapshot_form"):
        name = st.text_input("Snapshot Name")
        datasets = get_datasets()
        dataset_options = {d['name']: d['id'] for d in datasets} if datasets else {}
        dataset_id = st.selectbox("Dataset", options=list(dataset_options.values()), format_func=lambda x: next((k for k, v in dataset_options.items() if v == x), str(x))) if dataset_options else None
        description = st.text_area("Description (optional)")
        submitted = st.form_submit_button("Create")
        cancel = st.form_submit_button("Cancel")
        if cancel:
            st.session_state['show_create_snapshot_form'] = False
            st.rerun()
        if submitted:
            if not name or not dataset_id:
                st.error("Please provide both name and dataset.")
            else:
                result = create_snapshot(name, dataset_id, description)
                if isinstance(result, dict) and result.get("id"):
                    st.success(f"Snapshot '{name}' created successfully!")
                    st.session_state['show_create_snapshot_form'] = False
                    st.rerun()
                else:
                    st.error(f"Failed to create snapshot: {result}")

# --- Main snapshot list ---
with st.spinner("Loading snapshots..."):
    try:
        summaries = get_snapshot_summaries()
    except Exception:
        shimmer_placeholder()
        st.stop()

if summaries is None:
    shimmer_placeholder()
    st.stop()

if not summaries:
    st.info("No snapshots found.")
else:
    for snap in summaries:
        with st.expander(f"📸 {snap['name']} (ID: {snap['id']})", expanded=False):
            st.write(f"**Created At:** {snap.get('created_at', '')}")
            st.write(f"**Solution Status:** {snap.get('solution_status', 'N/A')}")
            # Description preview and toggle (if you want to show description, fetch full snapshot details as needed)
            # ... existing code for description preview/toggle ...

# Debug Panel Toggle
if st.sidebar.checkbox("Show Debug Info", value=False):
    with st.expander("🔍 Debug Panel", expanded=True):
        st.markdown("### Session State")
        st.json(st.session_state)

from components.right_log_panel import show_right_log_panel
show_right_log_panel(["Snapshots page loaded."])    