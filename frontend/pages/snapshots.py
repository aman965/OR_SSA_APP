import streamlit as st
from frontend.components.api_client import get_snapshots, create_snapshot, get_scenarios, get_uploads
from collections import defaultdict

st.set_page_config(page_title="Snapshots", page_icon="📸")
st.header("📸 Snapshots")

# --- Add Scenario Redirect (instant) ---
if 'add_scenario_redirect' in st.session_state:
    snap_id = st.session_state.pop('add_scenario_redirect')
    st.session_state['selected_snapshot_for_new_scenario'] = snap_id
    st.switch_page("pages/scenario_builder.py")
    st.stop()

# --- Create New Snapshot Section ---
if 'show_create_snapshot_form' not in st.session_state:
    st.session_state['show_create_snapshot_form'] = False

if not st.session_state['show_create_snapshot_form']:
    if st.button("Create New Snapshot", key="open_create_snapshot_form"):
        st.session_state['show_create_snapshot_form'] = True
        st.rerun()
else:
    st.subheader("Create New Snapshot")
    # Fetch datasets (uploads) for dropdown
    uploads = get_uploads()
    dataset_options = [(u['name'], u['id']) for u in uploads] if uploads else []
    with st.form("create_snapshot_form"):
        name = st.text_input("Snapshot Name")
        if dataset_options:
            dataset_idx = st.selectbox(
                "Dataset",
                options=range(len(dataset_options)),
                format_func=lambda i: dataset_options[i][0],
                help="Select a dataset to associate with this snapshot."
            )
            dataset_id = dataset_options[dataset_idx][1]
        else:
            st.warning("No datasets found. Please upload a dataset first.")
            dataset_id = None
        description = st.text_area("Description")
        col1, col2 = st.columns([1,1])
        submitted = col1.form_submit_button("Create Snapshot")
        cancel = col2.form_submit_button("Cancel")
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
        if cancel:
            st.session_state['show_create_snapshot_form'] = False
            st.rerun()

# --- Caching API calls for 30 seconds ---
@st.cache_data(ttl=30)
def cached_get_snapshots():
    return get_snapshots()

@st.cache_data(ttl=30)
def cached_get_scenarios():
    return get_scenarios()

# --- Fetch all snapshots and scenarios (efficient) ---
st.subheader("Existing Snapshots")
with st.spinner("Loading snapshots and scenarios..."):
    snapshots = cached_get_snapshots()
    all_scenarios = cached_get_scenarios()
    scenarios_by_snapshot = defaultdict(list)
    for scenario in all_scenarios:
        scenarios_by_snapshot[scenario.get('snapshot')].append(scenario)

if snapshots:
    for snap in snapshots:
        with st.expander(f"📸 {snap['name']} (ID: {snap['id']})", expanded=False):
            st.write(f"**Dataset:** {snap.get('dataset', 'N/A')}")
            # Description preview and toggle
            desc = snap.get('description')
            if desc:
                preview_len = 100
                show_full_key = f"show_full_desc_{snap['id']}"
                if show_full_key not in st.session_state:
                    st.session_state[show_full_key] = False
                is_long = len(desc) > preview_len or '\n' in desc
                if not st.session_state[show_full_key] and is_long:
                    # Show preview
                    preview = desc.split('\n', 1)[0][:preview_len]
                    st.markdown(f"**Description:** {preview}... ")
                    if st.button("Show more", key=f"showmore_{snap['id']}"):
                        st.session_state[show_full_key] = True
                        st.rerun()
                else:
                    st.markdown(f"**Description:** {desc}")
                    if is_long and st.button("Show less", key=f"showless_{snap['id']}"):
                        st.session_state[show_full_key] = False
                        st.rerun()
            st.write(f"**Owner:** {snap.get('owner', 'N/A')}")
            st.write(f"**Created At:** {snap.get('created_at', '')}")
            st.write(f"**Updated At:** {snap.get('updated_at', '')}")

            # --- List Scenarios for this Snapshot ---
            st.markdown("**Scenarios:**")
            scenarios = scenarios_by_snapshot.get(snap['id'], [])
            if scenarios:
                for scenario in scenarios:
                    st.write(f"- {scenario['name']} (Status: {scenario.get('status', 'N/A')})")
            else:
                st.info("No scenarios found for this snapshot.")

            # --- Add New Scenario Action (instant redirect) ---
            if st.button("Add Scenario", key=f"open_scenario_builder_{snap['id']}"):
                st.session_state['add_scenario_redirect'] = snap['id']
                st.rerun()
else:
    st.info("No snapshots found.")

# Debug Panel Toggle
if st.sidebar.checkbox("Show Debug Info", value=False):
    with st.expander("🔍 Debug Panel", expanded=True):
        st.markdown("### Session State")
        st.json(st.session_state)

from components.right_log_panel import show_right_log_panel
show_right_log_panel(["Snapshots page loaded."])    