import streamlit as st

def show_right_log_panel(logs: list[str]):
    """
    Display a floating, collapsible right-side log panel.
    
    Args:
        logs (list[str]): List of log messages to display
    """
    # Initialize session state for panel visibility if not exists
    if "show_log_panel" not in st.session_state:
        st.session_state.show_log_panel = False
    
    # Toggle button in sidebar
    if st.sidebar.button("📋 Logs", key="toggle_logs", help="Toggle right log panel"):
        st.session_state.show_log_panel = not st.session_state.show_log_panel
    
    # Show panel if enabled
    if st.session_state.show_log_panel:
        st.markdown(
            f'''
            <style>
            .log-panel {{
                position: fixed;
                top: 60px;
                right: 0;
                width: 300px;
                height: calc(100vh - 60px);
                overflow-y: auto;
                background-color: #f1f3f5;
                border-left: 2px solid #ccc;
                padding: 1rem;
                z-index: 1001;
                font-family: monospace;
                box-shadow: -2px 0 5px rgba(0,0,0,0.1);
            }}
            .log-header {{
                font-size: 1.2em;
                font-weight: bold;
                margin-bottom: 1rem;
                color: #262730;
                border-bottom: 1px solid #ccc;
                padding-bottom: 0.5rem;
            }}
            .log-line {{
                margin: 5px 0;
                font-size: 0.9em;
                color: #262730;
            }}
            </style>
            <div class="log-panel">
                <div class="log-header">🧾 Global Logs</div>
                {"".join([f'<div class="log-line">{line}</div>' for line in logs])}
            </div>
            ''',
            unsafe_allow_html=True
        ) 