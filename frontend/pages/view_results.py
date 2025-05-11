import streamlit as st
st.set_page_config(page_title="View Results", page_icon="📊")
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.right_log_panel import show_right_log_panel

# --- Handle session state for navigation ---
snapshot = st.session_state.get("selected_snapshot_for_results")
scenario = st.session_state.get("selected_scenario_for_results")

if not snapshot or not scenario:
    snapshot = "snap_2024_05_11"
    scenario = "Scenario 1"
    st.info("No session state found. Showing sample result for testing.")

st.success(f"Viewing results for {scenario} under {snapshot}")

# Initialize session state for logs if not exists
if "global_logs" not in st.session_state:
    st.session_state.global_logs = ["View Results page initialized."]

st.title("View Results")

# Section 1: Scenario Selection
st.header("Select Scenario")

# Mock data for snapshots and scenarios
snapshots = ["snap_2024_05_11", "order_batch_snap"]
scenarios = {
    "snap_2024_05_11": ["scenario_1", "scenario_2"],
    "order_batch_snap": ["scenario_3", "scenario_4"]
}

# Dropdowns for selection
selected_snapshot = st.selectbox(
    "Select Snapshot",
    snapshots,
    help="Choose a snapshot to view results from",
    index=snapshots.index(snapshot) if snapshot in snapshots else 0
)

selected_scenario = st.selectbox(
    "Select Scenario",
    scenarios[selected_snapshot],
    help="Choose a scenario to view",
    index=scenarios[selected_snapshot].index(scenario) if scenario in scenarios[selected_snapshot] else 0
)

# Section 2: Result Tabs
tabs = st.tabs(["📊 Tabular Output", "📈 KPI Summary", "📉 Plots", "🤖 Ask GPT"])

# Tab 1: Tabular Output
with tabs[0]:
    st.subheader("Solution Tables")
    
    # Mock data for routes
    routes_data = {
        'Route ID': ['R1', 'R2', 'R3'],
        'Vehicle': ['V1', 'V2', 'V3'],
        'Stops': [5, 4, 6],
        'Distance (km)': [45.2, 38.7, 52.1],
        'Duration (min)': [120, 95, 145]
    }
    routes_df = pd.DataFrame(routes_data)
    
    # Mock data for vehicle utilization
    utilization_data = {
        'Vehicle': ['V1', 'V2', 'V3'],
        'Total Distance': [45.2, 38.7, 52.1],
        'Total Time': [120, 95, 145],
        'Utilization %': [85, 75, 90]
    }
    utilization_df = pd.DataFrame(utilization_data)
    
    # Display tables
    st.markdown("### Routes")
    st.dataframe(routes_df, hide_index=True)
    
    st.markdown("### Vehicle Utilization")
    st.dataframe(utilization_df, hide_index=True)
    
    # Download buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Download All as XLSX"):
            st.session_state.global_logs.append("Downloading all tables as XLSX")
            st.info("Would download combined Excel file")
    
    with col2:
        if st.button("Download This Table as CSV"):
            st.session_state.global_logs.append("Downloading current table as CSV")
            st.info("Would download current table as CSV")

# Tab 2: KPI Summary
with tabs[1]:
    st.subheader("Key Performance Indicators")
    
    # KPI metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Distance",
            "136.0 km",
            delta="2.5%"
        )
    
    with col2:
        st.metric(
            "Total Routes",
            "3",
            delta="1"
        )
    
    with col3:
        st.metric(
            "Max Route Length",
            "52.1 km",
            delta="-5.2%"
        )
    
    with col4:
        st.metric(
            "Avg. Utilization",
            "83.3%",
            delta="3.1%"
        )

# Tab 3: Plots
with tabs[2]:
    st.subheader("Solution Visualization")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Mock bar chart
        fig1 = px.bar(
            routes_df,
            x='Route ID',
            y='Distance (km)',
            title='Route Distances'
        )
        st.plotly_chart(fig1, use_container_width=True)
        st.caption("Distribution of route distances across vehicles")
    
    with col2:
        # Mock pie chart
        fig2 = px.pie(
            utilization_df,
            values='Utilization %',
            names='Vehicle',
            title='Vehicle Utilization'
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("Vehicle utilization percentage breakdown")

# Tab 4: Ask GPT
with tabs[3]:
    st.subheader("Ask Questions About Results")
    
    # Question input
    question = st.text_area(
        "Ask a question about this result",
        help="Enter your question about the solution"
    )
    
    if st.button("Ask GPT"):
        if question:
            st.session_state.global_logs.append(f"GPT question asked: {question[:50]}...")
            st.info("GPT understood your question as: 'What is the most efficient route in terms of distance per stop?'")
            st.success("""
            Based on the solution data, Route R2 is the most efficient with an average of 9.68 km per stop. 
            This route serves 4 stops over 38.7 km, making it more efficient than R1 (9.04 km/stop) and R3 (8.68 km/stop).
            """)
        else:
            st.warning("Please enter a question")

# Debug Panel Toggle
if st.sidebar.checkbox("Show Debug Info", value=False):
    with st.expander("🔍 Debug Panel", expanded=True):
        st.markdown("### Session State")
        st.json(st.session_state)

from components.right_log_panel import show_right_log_panel
show_right_log_panel(["Entered View Results page."]) 