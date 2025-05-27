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

# More robust Streamlit Cloud detection
def is_streamlit_cloud():
    """Detect if running in Streamlit Cloud environment"""
    # Check multiple indicators
    cloud_indicators = [
        os.environ.get('STREAMLIT_SHARING_MODE') == 'true',
        os.environ.get('STREAMLIT_SERVER_HEADLESS') == 'true',
        'streamlit.io' in os.environ.get('HOSTNAME', ''),
        not os.path.exists(backend_dir / "manage.py"),
        'STREAMLIT_CLOUD' in os.environ
    ]
    
    # Also try to import Django to see if it's available
    try:
        import django
        django_available = True
    except ImportError:
        django_available = False
    
    # If Django is not available, we're likely in Streamlit Cloud
    return any(cloud_indicators) or not django_available

STREAMLIT_CLOUD_MODE = is_streamlit_cloud()

if STREAMLIT_CLOUD_MODE:
    # Streamlit Cloud mode - no Django, simplified functionality
    st.sidebar.info("🌐 Streamlit Cloud Mode")
    
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
                    "🚛 Vehicle Routing Problem (Demo)",
                    "📅 Scheduling (Coming Soon)", 
                    "🌐 Network Flow (Coming Soon)"
                ],
                index=1  # Default to Inventory Optimization
            )

            # Route to appropriate page
            if app_choice == "🏠 Home":
                show_home_page()
            elif app_choice == "📦 Inventory Optimization":
                show_inventory_optimization_streamlit()
            elif app_choice == "🚛 Vehicle Routing Problem (Demo)":
                st.title("🚛 Vehicle Routing Problem")
                st.warning("⚠️ VRP functionality requires Django backend which is not available in Streamlit Cloud.")
                st.info("💡 **Try our Inventory Optimization instead!** It's fully functional in Streamlit Cloud mode.")
                
                if st.button("Go to Inventory Optimization", type="primary"):
                    st.session_state.page = "inventory"
                    st.rerun()
                    
                st.markdown("---")
                st.markdown("### About VRP")
                st.write("""
                The Vehicle Routing Problem (VRP) solver includes:
                - Natural language constraint processing
                - Multi-vehicle route optimization
                - Real-time scenario management
                - Advanced visualization
                
                **Note:** Full VRP functionality requires a complete deployment with Django backend.
                """)
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