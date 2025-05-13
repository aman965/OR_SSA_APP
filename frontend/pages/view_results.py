import streamlit as st
st.set_page_config(page_title="View Results", page_icon="📊")  # must stay first

import io
import pandas as pd
import plotly.express as px

# ────────────── Page heading & context ──────────────
st.title("📊 View Results")

snapshot = st.session_state.get("selected_snapshot_for_results")
scenario = st.session_state.get("selected_scenario_for_results")

if not snapshot or not scenario:
    st.warning("No snapshot or scenario selected. Please go to the Snapshots page and click 'View Results'.")
    st.stop()

st.success(f"Viewing results for {scenario} under {snapshot}")

# ────────────── Dummy data for demo ──────────────
routes_data = pd.DataFrame({
    "Route": ["R1", "R2", "R3"],
    "Distance": [120, 95, 110],
    "Stops": [5, 4, 6],
    "Duration": ["2h 15m", "1h 45m", "2h 00m"]
})

utilization_data = pd.DataFrame({
    "Vehicle": ["V1", "V2", "V3"],
    "Capacity": [100, 80, 90],
    "Used": [85, 65, 75],
    "Utilization %": [85, 81, 83]
})

# ────────────── Tabs layout ──────────────
tabs = st.tabs(["Tabular Output", "KPI Summary", "Plots", "Ask GPT"])

# == Tab 0: Tables & downloads ==
with tabs[0]:
    st.subheader("Tabular Output")

    # ----- Routes table -----
    st.markdown("### Routes")
    st.dataframe(routes_data)

    # Prepare Excel buffer for Routes
    routes_buffer = io.BytesIO()
    with pd.ExcelWriter(routes_buffer, engine="xlsxwriter") as writer:
        routes_data.to_excel(writer, index=False, sheet_name="Routes")
    routes_buffer.seek(0)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Download Routes (XLSX)",
            data=routes_buffer,
            file_name="routes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with col2:
        st.download_button(
            "⬇️ Download Routes (CSV)",
            data=routes_data.to_csv(index=False).encode("utf-8"),
            file_name="routes.csv",
            mime="text/csv"
        )

    # ----- Vehicle Utilization table -----
    st.markdown("### Vehicle Utilization")
    st.dataframe(utilization_data)

    # Prepare Excel buffer for Utilization
    util_buffer = io.BytesIO()
    with pd.ExcelWriter(util_buffer, engine="xlsxwriter") as writer:
        utilization_data.to_excel(writer, index=False, sheet_name="Utilization")
    util_buffer.seek(0)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Download Utilization (XLSX)",
            data=util_buffer,
            file_name="utilization.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with col2:
        st.download_button(
            "⬇️ Download Utilization (CSV)",
            data=utilization_data.to_csv(index=False).encode("utf-8"),
            file_name="utilization.csv",
            mime="text/csv"
        )

# == Tab 1: KPI Summary ==
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

# == Tab 2: Plots ==
with tabs[2]:
    st.subheader("Plots")

    fig_bar = px.bar(
        routes_data,
        x="Route",
        y="Distance",
        title="Route vs Distance",
        labels={"Distance": "Distance (km)"}
    )
    st.plotly_chart(fig_bar)

    fig_pie = px.pie(
        utilization_data,
        values="Used",
        names="Vehicle",
        title="Vehicle Utilization",
        hole=0.4
    )
    st.plotly_chart(fig_pie)

# == Tab 3: Ask GPT ==
with tabs[3]:
    st.subheader("Ask GPT")
    user_q = st.text_input("Ask a question about this result")
    if st.button("Ask GPT"):
        st.session_state.global_logs.append(f"Asked GPT: {user_q}")
        st.info("GPT understood your question as: 'What is the most efficient route?'")
        st.success(
            "Route R2 is the most efficient with:\n"
            "- Distance: 95 km\n"
            "- Stops: 4\n"
            "- Duration: 1h 45m\n"
            "- Utilization: 81%"
        )

# ────────────── Right‑hand log panel / debug toggle ──────────────
from frontend.components.right_log_panel import show_right_log_panel  # noqa: E402
show_right_log_panel(st.session_state.global_logs)

if st.sidebar.checkbox("Show Debug Info", value=False):
    with st.expander("🔍 Debug Panel", expanded=True):
        st.markdown("### Session State")
        st.json(st.session_state)
