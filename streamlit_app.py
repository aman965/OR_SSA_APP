#!/usr/bin/env python3
"""
Streamlit App Entry Point for OR SaaS Platform
This file is required for Streamlit Cloud deployment
"""

import sys
import os
from pathlib import Path
import streamlit as st

# Set page config FIRST - before any other Streamlit commands
st.set_page_config(
    page_title="OR SaaS Application",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add the frontend directory to the Python path
frontend_dir = Path(__file__).resolve().parent / "frontend"
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(frontend_dir))
sys.path.insert(0, str(backend_dir))

# Check if we're in Streamlit Cloud (no Django available)
STREAMLIT_CLOUD_MODE = os.environ.get('STREAMLIT_SHARING_MODE') or not os.path.exists(backend_dir / "manage.py")

if STREAMLIT_CLOUD_MODE:
    # Streamlit Cloud mode - no Django, simplified functionality
    st.sidebar.warning("🌐 Running in Streamlit Cloud mode - Some features may be limited")
    
    # Import streamlit-only components
    try:
        from main import show_home_page, show_inventory_optimization_streamlit
        
        def main():
            # Sidebar navigation
            st.sidebar.title("🔧 OR SaaS Applications")
            st.sidebar.markdown("---")

            # Main application selection dropdown
            app_choice = st.sidebar.selectbox(
                "Choose Optimization Model:",
                [
                    "🏠 Home",
                    "📦 Inventory Optimization",
                    "🚛 Vehicle Routing Problem (Limited)",
                    "📅 Scheduling (Coming Soon)", 
                    "🌐 Network Flow (Coming Soon)"
                ]
            )

            # Route to appropriate page
            if app_choice == "🏠 Home":
                show_home_page()
            elif app_choice == "📦 Inventory Optimization":
                show_inventory_optimization_streamlit()
            elif app_choice == "🚛 Vehicle Routing Problem (Limited)":
                st.title("🚛 Vehicle Routing Problem")
                st.info("🌐 VRP functionality requires full backend. Please use the full deployment for complete VRP features.")
                st.write("In Streamlit Cloud mode, only basic optimization models are available.")
            else:
                st.title(f"{app_choice}")
                st.info("🚧 This module is under development and will be available in future updates.")

    except ImportError as e:
        st.error(f"Error importing streamlit components: {e}")
        st.write("Basic interface mode")
        
        def main():
            st.title("🚀 OR SaaS Platform")
            st.write("Welcome to the Operations Research SaaS Platform!")
            st.info("Some components are not available in this deployment mode.")

else:
    # Full mode with Django backend
    try:
        from main import main
    except ImportError:
        st.error("Could not import main application")
        def main():
            st.title("🚀 OR SaaS Platform")
            st.error("Application components not available")

if __name__ == "__main__":
    main() 