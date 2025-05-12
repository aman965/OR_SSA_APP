import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="View Results", page_icon="📊")

# Read session state
snapshot = st.session_state.get("selected_snapshot_for_results")
scenario = st.session_state.get("selected_scenario_for_results")

st.title("📊 View Results")

if not snapshot or not scenario:
    st.warning("No snapshot or scenario selected. Please go to the Snapshots page and click 'View Results'.")
    st.stop()

st.success(f"Viewing results for {scenario} under {snapshot}")

# Tabs
tabs = st.tabs(["Tabular Output", "KPI Summary", "Plots", "Ask GPT"])

with tabs[0]:
    st.subheader("Tabular Output")
    
    # Routes Table
    st.markdown("### Routes")
    routes_data = pd.DataFrame({
        "Route": ["R1", "R2", "R3"],
        "Distance": [120, 95, 110],
        "Stops": [5, 4, 6],
        "Duration": ["2h 15m", "1h 45m", "2h 00m"]
    })
    st.dataframe(routes_data)
    
    # Download buttons for Routes
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download Routes (XLSX)",
            routes_data.to_excel(index=False).encode('utf-8'),
            "routes.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with col2:
        st.download_button(
            "Download Routes (CSV)",
            routes_data.to_csv(index=False).encode('utf-8'),
            "routes.csv",
            "text/csv"
        )
    
    # Vehicle Utilization Table
    st.markdown("### Vehicle Utilization")
    utilization_data = pd.DataFrame({
        "Vehicle": ["V1", "V2", "V3"],
        "Capacity": [100, 80, 90],
        "Used": [85, 65, 75],
        "Utilization %": [85, 81, 83]
    })
    st.dataframe(utilization_data)
    
    # Download buttons for Utilization
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download Utilization (XLSX)",
            utilization_data.to_excel(index=False).encode('utf-8'),
            "utilization.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with col2:
        st.download_button(
            "Download Utilization (CSV)",
            utilization_data.to_csv(index=False).encode('utf-8'),
            "utilization.csv",
            "text/csv"
        )

with tabs[1]:
    st.subheader("KPI Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Distance", "325 km")
    with col2:
        st.metric("Total Routes", "3")
    with col3:
        st.metric("Max Route Length", "120 km")
    with col4:
        st.metric("Avg. Utilization", "83%")

with tabs[2]:
    st.subheader("Plots")
    
    # Route vs Distance Bar Chart
    fig_bar = px.bar(
        routes_data,
        x="Route",
        y="Distance",
        title="Route vs Distance",
        labels={"Distance": "Distance (km)"}
    )
    st.plotly_chart(fig_bar)
    
    # Vehicle Utilization Pie Chart
    fig_pie = px.pie(
        utilization_data,
        values="Used",
        names="Vehicle",
        title="Vehicle Utilization",
        hole=0.4
    )
    st.plotly_chart(fig_pie)

with tabs[3]:
    st.subheader("Ask GPT")
    user_q = st.text_input("Ask a question about this result")
    if st.button("Ask GPT"):
        st.session_state.global_logs.append(f"Asked GPT: {user_q}")
        st.info("GPT understood your question as: 'What is the most efficient route?'")
        st.success("""
        Route R2 is the most efficient with:
        - Distance: 95 km
        - Stops: 4
        - Duration: 1h 45m
        - Utilization: 81%
        """)

# Right log panel and debug toggle
from components.right_log_panel import show_right_log_panel
show_right_log_panel(st.session_state.global_logs)

if st.sidebar.checkbox("Show Debug Info", value=False):
    with st.expander("🔍 Debug Panel", expanded=True):
        st.markdown("### Session State")
        st.json(st.session_state) 