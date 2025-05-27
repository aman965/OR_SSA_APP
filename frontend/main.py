# -*- coding: utf-8 -*-
# Run this app from the frontend directory using: streamlit run main_hybrid.py
import streamlit as st

# Note: st.set_page_config() is now handled in streamlit_app.py to avoid conflicts

import sys
import os
import pandas as pd
from pathlib import Path

# Add project root to Python path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

# Import backend components
try:
    from backend.db_utils import init_db
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False
    st.warning("⚠️ Backend components not fully available. Some features may be limited.")

def main():
    # More robust Streamlit Cloud detection
    def is_streamlit_cloud():
        """Detect if running in Streamlit Cloud environment"""
        # Check multiple indicators
        cloud_indicators = [
            os.environ.get('STREAMLIT_SHARING_MODE') == 'true',
            os.environ.get('STREAMLIT_SERVER_HEADLESS') == 'true',
            'streamlit.io' in os.environ.get('HOSTNAME', ''),
            not os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'backend', 'manage.py')),
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
        # In Streamlit Cloud, redirect to simplified interface
        st.sidebar.info("🌐 Streamlit Cloud Mode")
        
        # Sidebar navigation
        st.sidebar.title("🔧 OR SaaS Applications")
        st.sidebar.markdown("---")
        
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
                st.rerun()
        else:
            st.title(f"{app_choice}")
            st.info("🚧 This module is under development.")
        return
    
    # Original main() code for full deployment
    # Initialize database on first run
    if BACKEND_AVAILABLE and 'db_initialized' not in st.session_state:
        try:
            with st.spinner("Initializing database..."):
                init_db()
            st.session_state.db_initialized = True
            st.sidebar.success("✅ Database initialized successfully")
        except Exception as e:
            st.sidebar.error("❌ Database initialization failed")
            st.sidebar.exception(e)

    # Sidebar navigation with both model selection and page navigation
    st.sidebar.title("🔧 OR SaaS Applications")
    st.sidebar.markdown("---")

    # Main application selection dropdown
    app_choice = st.sidebar.selectbox(
        "Choose Optimization Model:",
        [
            "🏠 Home",
            "🚛 Vehicle Routing Problem",
            "📅 Scheduling", 
            "📦 Inventory Optimization",
            "🌐 Network Flow"
        ]
    )

    # Show VRP sub-navigation when VRP is selected
    if app_choice == "🚛 Vehicle Routing Problem":
        # Remove the radio buttons and direct access buttons since we have horizontal tabs now
        pass

    # Route to appropriate page
    if app_choice == "🏠 Home":
        show_home_page()
    elif app_choice == "🚛 Vehicle Routing Problem":
        show_vrp_function()
    elif app_choice in ["📅 Scheduling", "📦 Inventory Optimization", "🌐 Network Flow"]:
        show_placeholder_application(app_choice)

def show_home_page():
    """Enhanced home page"""
    st.title("🚀 Operations Research SaaS Platform")
    st.write("Welcome to your comprehensive OR solution platform with natural language constraint processing!")

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Models", "4")
    with col2:
        st.metric("VRP Problems", "Available")
    with col3:
        st.metric("Solvers", "Multiple")
    with col4:
        st.metric("Status", "🟢 Online")

    st.markdown("---")

    # Feature overview
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🚛 Vehicle Routing Problem")
        st.write("• Natural language constraints")
        st.write("• Advanced constraint parsing")
        st.write("• Multiple solver options")
        st.write("• Comprehensive data management")
        if st.button("🚛 Go to VRP"):
            st.rerun()

    with col2:
        st.markdown("### 📊 Integrated Features")
        st.write("• Data Manager - Upload & manage datasets")
        st.write("• Snapshots - Data versioning")
        st.write("• Scenario Builder - Problem setup")
        st.write("• Results Analysis - Solution insights")

    with col3:
        st.markdown("### 🔮 Coming Soon")
        st.write("• Scheduling optimization")
        st.write("• Inventory management")
        st.write("• Network flow problems")
        st.write("• Advanced analytics")

    # Available Models
    st.markdown("---")
    st.subheader("🎯 Available Optimization Models")
    
    models = [
        {"name": "🚛 Vehicle Routing Problem", "status": "✅ Fully Functional", "desc": "Complete VRP solver with natural language constraints"},
        {"name": "📅 Scheduling", "status": "🚧 Coming Soon", "desc": "Resource and task scheduling optimization"},
        {"name": "📦 Inventory Optimization", "status": "🚧 Coming Soon", "desc": "Inventory level and ordering optimization"},
        {"name": "🌐 Network Flow", "status": "🚧 Coming Soon", "desc": "Network flow and transportation problems"}
    ]
    
    for model in models:
        with st.expander(f"{model['name']} - {model['status']}"):
            st.write(model['desc'])

def show_vrp_function():
    """Show VRP function with horizontal tabs"""
    st.title("🚛 Vehicle Routing Problem Solver")
    st.write("Solve complex vehicle routing problems with natural language constraints")
    
    # Get current tab from URL query parameters
    query_params = st.query_params
    current_tab = query_params.get("tab", "snapshots")  # Default to snapshots
    
    # Map tab names to indices
    tab_mapping = {
        "data_manager": 0,
        "snapshots": 1,
        "scenario_builder": 2,
        "view_results": 3,
        "compare_outputs": 4
    }
    
    # Set active tab based on URL or session state
    if current_tab in tab_mapping:
        st.session_state.active_vrp_tab = tab_mapping[current_tab]
    elif 'active_vrp_tab' not in st.session_state:
        st.session_state.active_vrp_tab = 1  # Default to Snapshots tab
    
    # Check for tab switching requests
    if 'switch_to_tab' in st.session_state:
        if st.session_state.switch_to_tab == 'scenario_builder':
            st.session_state.active_vrp_tab = 2
            st.query_params.tab = "scenario_builder"
        elif st.session_state.switch_to_tab == 'view_results':
            st.session_state.active_vrp_tab = 3
            st.query_params.tab = "view_results"
        del st.session_state.switch_to_tab
    
    # Create custom tab buttons
    tab_cols = st.columns(5)
    tab_names = ["📊 Data Manager", "📸 Snapshots", "🏗️ Scenario Builder", "📈 View Results", "⚖️ Compare Outputs"]
    tab_keys = ["data_manager", "snapshots", "scenario_builder", "view_results", "compare_outputs"]
    
    for i, (col, tab_name, tab_key) in enumerate(zip(tab_cols, tab_names, tab_keys)):
        with col:
            if st.session_state.active_vrp_tab == i:
                st.markdown(f"**🔹 {tab_name}**")
            else:
                if st.button(tab_name, key=f"tab_{i}"):
                    st.session_state.active_vrp_tab = i
                    st.query_params.tab = tab_key
                    st.rerun()
    
    st.markdown("---")
    
    # Show content based on active tab
    if st.session_state.active_vrp_tab == 0:
        show_embedded_data_manager()
    elif st.session_state.active_vrp_tab == 1:
        show_embedded_snapshots()
    elif st.session_state.active_vrp_tab == 2:
        show_embedded_scenario_builder()
    elif st.session_state.active_vrp_tab == 3:
        show_embedded_view_results()
    elif st.session_state.active_vrp_tab == 4:
        show_embedded_compare_outputs()

def show_embedded_data_manager():
    """Embedded data manager functionality"""
    try:
        # Setup Django
        import django
        import os
        import sys
        from datetime import datetime
        
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        BACKEND_PATH = os.path.abspath(os.path.join(BASE_DIR, "backend"))
        sys.path.append(BACKEND_PATH)
        
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "orsaas_backend.settings")
        django.setup()
        
        from core.models import Upload
        from django.conf import settings
        from django.core.files.base import ContentFile
        import pandas as pd
        
        # Initialize logs
        if "global_logs" not in st.session_state:
            st.session_state.global_logs = ["Data Manager initialized."]

        # Test Simulation Toggle
        if st.checkbox("Simulate upload success", value=True, key="embedded_simulate_upload"):
            st.success("Mock upload triggered successfully.")

        st.header("Upload Dataset")

        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['csv', 'xlsx'],
            help="Upload .csv or .xlsx files",
            key="embedded_data_manager_uploader"
        )

        # Dataset name input
        dataset_name = st.text_input(
            "Dataset Name (optional)",
            help="Enter a custom name for your dataset. If left blank, will use the file name.",
            key="embedded_data_manager_name"
        )

        # Upload button and processing
        if st.button("Upload Dataset", key="embedded_data_manager_upload"):
            if uploaded_file is not None:
                file_ext = uploaded_file.name.split('.')[-1].lower()
                final_name = dataset_name.strip() if dataset_name else uploaded_file.name.rsplit(".", 1)[0]
                
                if Upload.objects.filter(name=final_name).exists():
                    st.warning(f"Dataset name '{final_name}' already exists. Please choose a different name.")
                else:
                    try:
                        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
                        os.makedirs(upload_dir, exist_ok=True)
                        
                        file_content = ContentFile(uploaded_file.getbuffer())
                        upload = Upload.objects.create(name=final_name)
                        upload.file.save(f"{final_name}.{file_ext}", file_content, save=True)
                        
                        st.success(f"✅ Dataset '{final_name}' uploaded successfully!")
                        st.session_state.global_logs.append(f"Uploaded dataset: {final_name}")
                        st.session_state.global_logs.append(f"File saved to: {upload.file.path}")
                        
                        # Preview uploaded data
                        if file_ext == 'csv':
                            df = pd.read_csv(upload.file.path)
                        else:
                            df = pd.read_excel(upload.file.path)
                        st.write("Preview of uploaded data:")
                        st.dataframe(df.head(), use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"Error uploading file: {str(e)}")
                        st.session_state.global_logs.append(f"Upload failed: {str(e)}")
            else:
                st.error("Please select a file to upload")

        # Dataset Listing Section
        st.header("Uploaded Datasets")
        uploads = Upload.objects.all().order_by("-uploaded_at")
        if uploads.exists():
            df = pd.DataFrame([
                {
                    "Name": u.name,
                    "File Type": u.file.name.split('.')[-1].upper(),
                    "Uploaded At": u.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "File Path": u.file.name
                } for u in uploads
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No datasets uploaded yet.")

        # Data Management Section
        st.header("Data Management")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Refresh List", key="embedded_data_manager_refresh"):
                st.session_state.global_logs.append("Dataset list refreshed")
                st.rerun()

        with col2:
            if st.button("Export List", key="embedded_data_manager_export"):
                if uploads.exists():
                    export_df = pd.DataFrame([
                        {
                            "Name": u.name,
                            "File Type": u.file.name.split('.')[-1].upper(),
                            "Uploaded At": u.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
                            "File Path": u.file.name
                        } for u in uploads
                    ])
                    st.session_state.global_logs.append("Dataset list exported")
                    st.download_button(
                        "Download Dataset List",
                        export_df.to_csv(index=False).encode('utf-8'),
                        "dataset_list.csv",
                        "text/csv",
                        key="embedded_data_manager_download"
                    )
                else:
                    st.info("No datasets to export")

        with col3:
            if st.button("Delete Selected", key="embedded_data_manager_delete"):
                st.warning("Delete functionality will be implemented in future updates")
                st.session_state.global_logs.append("Delete operation requested (not implemented)")

        # Right log panel
        try:
            from components.right_log_panel import show_right_log_panel
            show_right_log_panel(st.session_state.global_logs)
        except ImportError:
            with st.expander("📋 Activity Logs"):
                for log in st.session_state.global_logs[-10:]:  # Show last 10 logs
                    st.text(log)

        # Debug Panel
        if st.checkbox("Show Debug Info", value=False, key="embedded_data_debug"):
            with st.expander("🔍 Debug Panel", expanded=True):
                st.markdown("### Session State")
                debug_state = {k: v for k, v in st.session_state.items() if not k.startswith('embedded_')}
                st.json(debug_state)
                
    except Exception as e:
        st.error(f"Error loading data manager: {e}")
        st.write("Basic data manager interface")

def show_embedded_snapshots():
    """Embedded snapshots functionality"""
    try:
        # Setup Django
        import django
        import os
        import sys
        from datetime import datetime
        
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        BACKEND_PATH = os.path.abspath(os.path.join(BASE_DIR, "backend"))
        sys.path.append(BACKEND_PATH)
        
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "orsaas_backend.settings")
        django.setup()
        
        from core.models import Snapshot, Upload
        
        # Initialize logs
        if "global_logs" not in st.session_state:
            st.session_state.global_logs = ["Snapshots initialized."]

        # Create Snapshot Section
        st.header("Create Snapshot")
        
        uploads = Upload.objects.all().order_by("-uploaded_at")
        dataset_names = [u.name for u in uploads]
        
        if dataset_names:
            selected_upload_name = st.selectbox(
                "Select Dataset",
                dataset_names,
                help="Choose a dataset to create a snapshot from",
                key="embedded_snapshot_dataset"
            )
            
            snapshot_name = st.text_input(
                "Snapshot Name",
                help="Enter a name for this snapshot",
                key="embedded_snapshot_name"
            )
            
            description = st.text_area(
                "Description",
                help="Enter a description for this snapshot",
                key="embedded_snapshot_description"
            )
            
            if st.button("Create Snapshot", key="embedded_create_snapshot"):
                if not snapshot_name:
                    st.error("Please enter a snapshot name")
                elif Snapshot.objects.filter(name=snapshot_name).exists():
                    st.warning("Snapshot with this name already exists.")
                else:
                    upload_obj = Upload.objects.get(name=selected_upload_name)
                    snapshot = Snapshot.objects.create(
                        name=snapshot_name,
                        linked_upload=upload_obj,
                        description=description
                    )
                    
                    try:
                        import pandas as pd
                        try:
                            from components.file_utils import save_snapshot_file
                            
                            if upload_obj.file.name.endswith('.csv'):
                                df = pd.read_csv(upload_obj.file.path)
                            else:
                                df = pd.read_excel(upload_obj.file.path)
                                
                            snapshot_path = save_snapshot_file(snapshot.id, df)
                            st.session_state.global_logs.append(f"Snapshot file created at: {snapshot_path}")
                        except ImportError:
                            st.session_state.global_logs.append("File utils not available - snapshot created without file copy")
                        except Exception as e:
                            st.warning(f"Could not create physical snapshot file: {str(e)}")
                            st.session_state.global_logs.append(f"Error creating snapshot file: {str(e)}")
                    except Exception as e:
                        st.session_state.global_logs.append(f"Error in snapshot file creation: {str(e)}")
                        
                    st.success(f"Snapshot '{snapshot_name}' created successfully.")
                    st.session_state.global_logs.append(f"Snapshot '{snapshot_name}' created.")
                    st.rerun()
        else:
            st.warning("No datasets available. Please upload a dataset first in the Data Manager tab.")

        # List Existing Snapshots
        st.header("Snapshots & Scenarios")
        snapshots = Snapshot.objects.select_related("linked_upload").order_by("-created_at")
        
        for snap in snapshots:
            with st.expander(f"📦 {snap.name}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Linked Dataset:** {snap.linked_upload.name if snap.linked_upload else 'N/A'}")
                    st.markdown(f"**Created At:** {snap.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.markdown(f"**Description:** {snap.description or 'No description provided'}")
                
                with col2:
                    if st.button(f"➕ Create Scenario", key=f"embedded_create_scenario_{snap.id}"):
                        st.session_state.selected_snapshot_id = snap.id
                        st.session_state.selected_snapshot_name = snap.name
                        st.session_state.selected_snapshot_for_scenario_builder = snap.name
                        st.session_state.global_logs.append(f"Selected snapshot for scenario creation: {snap.name}")
                        st.session_state.active_vrp_tab = 2  # Trigger automatic tab switch
                        st.query_params.tab = "scenario_builder"
                        st.success(f"✅ Switching to Scenario Builder...")
                        st.rerun()
                
                # List scenarios for this snapshot
                scenarios = snap.scenario_set.all().order_by("-created_at")
                if scenarios:
                    st.markdown("### Scenarios")
                    for scenario in scenarios:
                        col1, col2, col3 = st.columns([3, 1, 2])
                        with col1:
                            st.markdown(f"**{scenario.name}**")
                        with col2:
                            st.markdown(f"Status: `{scenario.status}`")
                        with col3:
                            if scenario.status == "solved":
                                if st.button(f"View Results", key=f"embedded_view_{snap.id}_{scenario.id}"):
                                    st.session_state.selected_snapshot_for_results = snap.name
                                    st.session_state.selected_scenario_for_results = scenario.name
                                    st.session_state.global_logs.append(f"Selected for results: {snap.name} - {scenario.name}")
                                    st.session_state.active_vrp_tab = 3  # Switch to View Results tab
                                    st.query_params.tab = "view_results"
                                    st.success(f"✅ Switching to View Results for {scenario.name}...")
                                    st.rerun()
                            elif scenario.status == "failed":
                                st.button("Failed", disabled=True, help=scenario.reason or "No reason provided", key=f"embedded_fail_{snap.id}_{scenario.id}")
                            else:
                                st.button("Not Solved", disabled=True, help="Scenario not yet solved", key=f"embedded_not_solved_{snap.id}_{scenario.id}")

        # Right log panel
        try:
            from components.right_log_panel import show_right_log_panel
            show_right_log_panel(st.session_state.global_logs)
        except ImportError:
            with st.expander("📋 Activity Logs"):
                for log in st.session_state.global_logs[-10:]:
                    st.text(log)

        # Debug Panel
        if st.checkbox("Show Debug Info", value=False, key="embedded_snapshots_debug"):
            with st.expander("🔍 Debug Panel", expanded=True):
                st.markdown("### Session State")
                debug_state = {k: v for k, v in st.session_state.items() if not k.startswith('embedded_')}
                st.json(debug_state)
            
    except Exception as e:
        st.error(f"Error loading snapshots: {e}")
        st.write("Basic snapshots interface")

def show_embedded_scenario_builder():
    """Embedded scenario builder functionality"""
    try:
        # Setup Django
        import django
        import os
        import sys
        import json
        import subprocess
        import time
        from datetime import datetime
        
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        BACKEND_PATH = os.path.abspath(os.path.join(BASE_DIR, "backend"))
        MEDIA_ROOT = os.path.abspath(os.path.join(BASE_DIR, "media"))
        sys.path.append(BACKEND_PATH)
        
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "orsaas_backend.settings")
        django.setup()
        
        from core.models import Snapshot, Scenario
        
        # Initialize logs
        if "global_logs" not in st.session_state:
            st.session_state.global_logs = ["Scenario Builder initialized."]

        # Initialize running scenario state
        if "running_scenario" not in st.session_state:
            st.session_state.running_scenario = None

        # Try to import infeasibility explainer
        try:
            from services.gpt_services.infeasibility_explainer import analyze_infeasibility
            INFEASIBILITY_EXPLAINER_AVAILABLE = True
            st.session_state.global_logs.append("Infeasibility explainer service loaded successfully")
        except ImportError:
            INFEASIBILITY_EXPLAINER_AVAILABLE = False
            st.session_state.global_logs.append("Infeasibility explainer service not available")

        # Helper function to run model
        def run_model_for_scenario(scenario_id):
            st.session_state.running_scenario = scenario_id
            st.session_state[f"scenario_solve_start_time_{scenario_id}"] = datetime.now()
            redirect_to_results = False
            snapshot_name_for_redirect = None
            scenario_name_for_redirect = None

            try:
                scenario = Scenario.objects.select_related('snapshot').get(id=scenario_id)
                st.info(f"Starting model run for scenario: {scenario.name} (ID: {scenario.id})...")
                st.session_state.global_logs.append(f"Model run initiated for Scenario ID: {scenario.id} ({scenario.name}).")

                scenario.status = "solving"
                scenario.reason = ""
                scenario.save()

                scenario_dir = os.path.join(MEDIA_ROOT, "scenarios", str(scenario.id))
                output_dir = os.path.join(scenario_dir, "outputs")
                os.makedirs(scenario_dir, exist_ok=True)
                os.makedirs(output_dir, exist_ok=True)
                st.session_state.global_logs.append(f"Created directories: {scenario_dir} and {output_dir}")
                
                # Initialize paths for solution and failure files
                solution_path = os.path.join(output_dir, "solution_summary.json")
                failure_path = os.path.join(output_dir, "failure_summary.json")
                model_lp_path = os.path.join(output_dir, "model.lp")

                scenario_data = {
                    "scenario_id": scenario.id,
                    "scenario_name": scenario.name,
                    "snapshot_id": scenario.snapshot.id,
                    "snapshot_name": scenario.snapshot.name,
                    "params": {
                        "param1": scenario.param1,
                        "param2": scenario.param2,
                        "param3": scenario.param3,
                        "param4": scenario.param4,
                        "param5": scenario.param5,
                    },
                    "gpt_prompt": scenario.gpt_prompt,
                    "dataset_file_path": os.path.join(MEDIA_ROOT, scenario.snapshot.linked_upload.file.name)
                }
                scenario_json_path = os.path.join(scenario_dir, "scenario.json")
                with open(scenario_json_path, 'w') as f:
                    json.dump(scenario_data, f, indent=4)
                st.session_state.global_logs.append(f"Created scenario.json at {scenario_json_path}")

                progress_bar = st.progress(0, text="Model solving in progress...")

                # Run the ENHANCED VRP solver with intelligent constraint parsing
                try:
                    # Determine which solver to use based on model type
                    model_type = scenario.model_type if hasattr(scenario, 'model_type') else 'vrp'
                    
                    if model_type == 'inventory':
                        solver_path = os.path.join(BACKEND_PATH, "solver", "inventory_solver.py")
                        st.session_state.global_logs.append("Using inventory optimization solver")
                    else:
                        # Default to VRP solver
                        solver_path = os.path.join(BACKEND_PATH, "solver", "vrp_solver_enhanced.py")
                        
                        # Fallback to original solver if enhanced version not available
                        if not os.path.exists(solver_path):
                            solver_path = os.path.join(BACKEND_PATH, "solver", "vrp_solver.py")
                            st.session_state.global_logs.append("Using standard VRP solver (enhanced solver not found)")
                        else:
                            st.session_state.global_logs.append("Using enhanced VRP solver with intelligent constraint parsing")
                    
                    # Prepare environment variables, including OpenAI API key if available
                    env = os.environ.copy()
                    
                    # Try to get OpenAI API key from Streamlit secrets
                    try:
                        api_key = None
                        if hasattr(st, 'secrets'):
                            # Try the nested format first
                            if 'openai' in st.secrets and 'api_key' in st.secrets['openai']:
                                api_key = st.secrets['openai']['api_key']
                                st.session_state.global_logs.append(f"OpenAI API key found in secrets (openai.api_key) - length: {len(api_key)}")
                            # Try the direct format
                            elif 'OPENAI_API_KEY' in st.secrets:
                                api_key = st.secrets['OPENAI_API_KEY']
                                st.session_state.global_logs.append(f"OpenAI API key found in secrets (OPENAI_API_KEY) - length: {len(api_key)}")
                            else:
                                st.session_state.global_logs.append("No OpenAI API key found in secrets - solver will use fallback parsing")
                        
                        if api_key:
                            env['OPENAI_API_KEY'] = api_key
                            st.session_state.global_logs.append(f"OpenAI API key passed to enhanced solver (length: {len(api_key)})")
                        else:
                            st.session_state.global_logs.append("No OpenAI API key found in secrets - solver will use fallback parsing")
                    except Exception as e:
                        st.session_state.global_logs.append(f"Could not access OpenAI API key: {e}")
                    
                    result = subprocess.run(
                        [sys.executable, solver_path, "--scenario-path", scenario_json_path],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=180,
                        env=env
                    )
                    st.session_state.global_logs.append(f"VRP solver output: {result.stdout}")
                    
                    # Check for solution or failure files in both output_dir and scenario_dir
                    alt_solution_path = os.path.join(scenario_dir, "solution_summary.json")
                    alt_failure_path = os.path.join(scenario_dir, "failure_summary.json")
                    
                    # Check for solution file in both locations
                    if os.path.exists(solution_path):
                        with open(solution_path, 'r') as f:
                            solution = json.load(f)
                        scenario.status = "solved"
                        scenario.reason = ""
                        progress_bar.empty()
                        st.success(f"✅ Model for scenario '{scenario.name}' solved successfully!")
                        st.session_state.global_logs.append(f"Scenario {scenario.id} solved successfully.")

                        # KPI Calculation and Save compare_metrics.json
                        try:
                            routes = solution.get('routes', [])
                            total_routes = len(routes)
                            total_distance = float(solution.get('total_distance', 0))
                            avg_route_distance = total_distance / total_routes if total_routes else 0
                            customers_served = sum(len(r) - 2 for r in routes if isinstance(r, list) and len(r) > 2)
                            max_route_length = max((len(r) - 2 for r in routes if isinstance(r, list)), default=0)
                            avg_utilization = customers_served / total_routes if total_routes else 0
                            kpis = {
                                "total_distance": total_distance,
                                "total_routes": total_routes,
                                "avg_route_distance": avg_route_distance,
                                "customers_served": customers_served,
                                "max_route_length": max_route_length,
                                "avg_utilization": round(avg_utilization, 2)
                            }
                            compare_metrics = {
                                "scenario_id": scenario.id,
                                "scenario_name": scenario.name,
                                "snapshot_name": scenario.snapshot.name,
                                "kpis": kpis,
                                "status": solution.get("status", "solved")
                            }
                            compare_metrics_path = os.path.join(scenario_dir, "compare_metrics.json")
                            with open(compare_metrics_path, 'w') as f:
                                json.dump(compare_metrics, f, indent=2)
                            st.session_state.global_logs.append(f"compare_metrics.json written for scenario {scenario.id}")
                        except Exception as e:
                            st.session_state.global_logs.append(f"Error writing compare_metrics.json for scenario {scenario.id}: {str(e)}")

                        # Prepare for redirect
                        redirect_to_results = True
                        snapshot_name_for_redirect = scenario.snapshot.name
                        scenario_name_for_redirect = scenario.name
                    elif os.path.exists(alt_solution_path):
                        import shutil
                        shutil.copy2(alt_solution_path, solution_path)
                        st.session_state.global_logs.append(f"Copied solution file from {alt_solution_path} to {solution_path}")
                        
                        with open(solution_path, 'r') as f:
                            solution = json.load(f)
                        scenario.status = "solved"
                        scenario.reason = ""
                        progress_bar.empty()
                        st.success(f"✅ Model for scenario '{scenario.name}' solved successfully!")
                        st.session_state.global_logs.append(f"Scenario {scenario.id} solved successfully.")
                        
                        # Prepare for redirect
                        redirect_to_results = True
                        snapshot_name_for_redirect = scenario.snapshot.name
                        scenario_name_for_redirect = scenario.name
                    elif os.path.exists(failure_path) or os.path.exists(alt_failure_path):
                        failure_file = failure_path if os.path.exists(failure_path) else alt_failure_path
                        with open(failure_file, 'r') as f:
                            failure = json.load(f)
                        scenario.status = "failed"
                        scenario.reason = failure.get("message", "Unknown failure")
                        progress_bar.empty()
                        st.error(f"Model for scenario '{scenario.name}' failed. Reason: {scenario.reason}")
                        st.session_state.global_logs.append(f"Scenario {scenario.id} failed. Reason: {scenario.reason}")
                        
                        # Check if model.lp exists and analyze infeasibility
                        model_lp_path = os.path.join(scenario_dir, "model.lp")
                        alt_model_lp_path = os.path.join(output_dir, "model.lp")
                        
                        if os.path.exists(model_lp_path):
                            lp_file_path = model_lp_path
                        elif os.path.exists(alt_model_lp_path):
                            lp_file_path = alt_model_lp_path
                            import shutil
                            shutil.copy2(alt_model_lp_path, model_lp_path)
                            st.session_state.global_logs.append(f"Copied model.lp from {alt_model_lp_path} to {model_lp_path}")
                        else:
                            lp_file_path = None
                            st.session_state.global_logs.append(f"No model.lp file found for scenario {scenario.id}")
                        
                        # Check for infeasibility keywords in the error message
                        infeasibility_keywords = ["infeasible", "no solution", "not solved to optimality", "no feasible solution"]
                        is_infeasible = any(keyword in scenario.reason.lower() for keyword in infeasibility_keywords)
                        
                        if INFEASIBILITY_EXPLAINER_AVAILABLE and lp_file_path and is_infeasible:
                            st.session_state.global_logs.append(f"Analyzing infeasibility for scenario {scenario.id}")
                            with st.spinner("Analyzing infeasibility with ChatGPT..."):
                                try:
                                    analysis_result = analyze_infeasibility(scenario.id)
                                    if analysis_result.get("success", False):
                                        explanation_path = os.path.join(scenario_dir, "gpt_error_explanation.txt")
                                        if os.path.exists(explanation_path):
                                            st.session_state.global_logs.append(f"Infeasibility analysis saved to {explanation_path}")
                                            st.info("✅ Infeasibility analyzed with ChatGPT. See details in the 'Show Details' section.")
                                            
                                            # Update the scenario reason with the GPT explanation
                                            reason = analysis_result.get("reason", "")
                                            suggestion = analysis_result.get("suggestion", "")
                                            if reason and suggestion:
                                                scenario.reason = f"Model not solved to optimality. {reason} Suggestion: {suggestion}"
                                                scenario.save()
                                    else:
                                        st.session_state.global_logs.append(f"Infeasibility analysis failed: {analysis_result.get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.session_state.global_logs.append(f"Error analyzing infeasibility: {str(e)}")
                    else:
                        raise FileNotFoundError("Neither solution nor failure file was created")
                        
                except subprocess.CalledProcessError as e:
                    scenario.status = "failed"
                    error_msg = f"Solver error: {e.stderr}"
                    scenario.reason = error_msg
                    progress_bar.empty()
                    st.error(f"Model for scenario '{scenario.name}' failed. Reason: {error_msg}")
                    st.session_state.global_logs.append(f"Scenario {scenario.id} failed. Reason: {error_msg}")
                    
                    # Check if model.lp exists and analyze infeasibility
                    model_lp_path = os.path.join(scenario_dir, "model.lp")
                    if INFEASIBILITY_EXPLAINER_AVAILABLE and os.path.exists(model_lp_path) and "infeasible" in error_msg.lower():
                        st.session_state.global_logs.append(f"Analyzing infeasibility for scenario {scenario.id}")
                        with st.spinner("Analyzing infeasibility with ChatGPT..."):
                            try:
                                analysis_result = analyze_infeasibility(scenario.id)
                                if analysis_result.get("success", False):
                                    explanation_path = os.path.join(scenario_dir, "gpt_error_explanation.txt")
                                    if os.path.exists(explanation_path):
                                        st.session_state.global_logs.append(f"Infeasibility analysis saved to {explanation_path}")
                                        st.info("✅ Infeasibility analyzed with ChatGPT. See details in the 'Show Details' section.")
                                else:
                                    st.session_state.global_logs.append(f"Infeasibility analysis failed: {analysis_result.get('error', 'Unknown error')}")
                            except Exception as e:
                                st.session_state.global_logs.append(f"Error analyzing infeasibility: {str(e)}")
                except Exception as e:
                    scenario.status = "failed"
                    scenario.reason = f"Error running solver: {str(e)}"
                    progress_bar.empty()
                    st.error(f"Model for scenario '{scenario.name}' failed. Reason: {scenario.reason}")
                    st.session_state.global_logs.append(f"Scenario {scenario.id} failed. Reason: {scenario.reason}")

                scenario.save()

            except Scenario.DoesNotExist:
                st.error(f"Scenario with ID {scenario_id} not found.")
                st.session_state.global_logs.append(f"Attempted to run non-existent Scenario ID: {scenario_id}")
            except Exception as e:
                st.error(f"An error occurred while running the model for scenario ID {scenario_id}: {str(e)}")
                st.session_state.global_logs.append(f"Error running model for Scenario ID {scenario_id}: {str(e)}")
                try:
                    scenario_obj = Scenario.objects.get(id=scenario_id)
                    scenario_obj.status = "failed"
                    scenario_obj.reason = f"Execution error: {str(e)}"
                    scenario_obj.save()
                except:
                    pass
            finally:
                st.session_state.running_scenario = None
                if f"scenario_solve_start_time_{scenario_id}" in st.session_state:
                    del st.session_state[f"scenario_solve_start_time_{scenario_id}"]
                
                if redirect_to_results:
                    st.session_state["selected_snapshot_for_results"] = snapshot_name_for_redirect
                    st.session_state["selected_scenario_for_results"] = scenario_name_for_redirect
                    st.session_state.active_vrp_tab = 3  # Switch to View Results tab
                    st.query_params.tab = "view_results"
                    st.info("✅ Scenario solved! Switching to View Results...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.rerun()

        # Create New Scenario Section
        with st.expander("Create New Scenario", expanded=True):
            st.header("Scenario Configuration")
            
            # Check if snapshot was pre-selected from Snapshots tab
            if 'selected_snapshot_for_scenario_builder' in st.session_state:
                st.success(f"🎯 **Ready to create scenario for snapshot: '{st.session_state.selected_snapshot_for_scenario_builder}'**")
                st.info("The snapshot has been pre-selected for you. Fill in the details below to create your scenario.")
            
            try:
                snapshots_qs = Snapshot.objects.order_by("-created_at")
                snapshot_names = [s.name for s in snapshots_qs]
                if not snapshot_names:
                    st.warning("No snapshots found. Please create a snapshot first in the Snapshots tab.")
                    selected_snapshot_name_form = None
                    snapshot_obj_form = None
                else:
                    # Check for pre-selected snapshot
                    preselected_snapshot = st.session_state.get("selected_snapshot_for_scenario_builder")
                    default_index = 0
                    if preselected_snapshot and preselected_snapshot in snapshot_names:
                        default_index = snapshot_names.index(preselected_snapshot)
                        st.session_state.global_logs.append(f"Pre-selected snapshot found: {preselected_snapshot}")
                        # Clear after using
                        if 'selected_snapshot_for_scenario_builder' in st.session_state:
                            del st.session_state["selected_snapshot_for_scenario_builder"]
                    
                    # Check for selected snapshot from snapshots tab
                    if 'selected_snapshot_id' in st.session_state:
                        try:
                            selected_snap = Snapshot.objects.get(id=st.session_state.selected_snapshot_id)
                            if selected_snap.name in snapshot_names:
                                default_index = snapshot_names.index(selected_snap.name)
                                st.session_state.global_logs.append(f"Using selected snapshot: {selected_snap.name}")
                        except:
                            pass
                    
                    # Snapshot selection
                    st.subheader("Select Snapshot")
                    selected_snapshot_name_form = st.selectbox(
                        "Select Snapshot", 
                        snapshot_names, 
                        index=default_index,
                        help="Choose an existing snapshot to link this scenario to.", 
                        key="embedded_scenario_snapshot_select"
                    )
                    snapshot_obj_form = Snapshot.objects.get(name=selected_snapshot_name_form) if selected_snapshot_name_form else None
                    
                    # Scenario name
                    scenario_name_form = st.text_input(
                        "Scenario Name",
                        help="Enter a unique name for this scenario within the selected snapshot",
                        key="embedded_scenario_name"
                    )

                    st.subheader("Parameters")
                    
                    # Determine if we're in inventory mode
                    is_inventory_mode = 'active_inventory_tab' in st.session_state
                    
                    cols_params = st.columns(3)
                    with cols_params[0]:
                        if is_inventory_mode:
                            param1_form = st.number_input("Holding Cost Rate (%)", min_value=0.01, value=20.0, step=0.1, format="%.2f", help="Annual holding cost as percentage of item value", key="embedded_p1_form")
                            param4_form = st.toggle("Apply Max Inventory Constraint", value=False, help="Enable maximum inventory value constraint", key="embedded_p4_form")
                        else:
                            param1_form = st.number_input("Capacity (Float > 0)", min_value=0.01, value=100.0, step=0.1, format="%.2f", help="Vehicle Capacity", key="embedded_p1_form")
                            param4_form = st.toggle("P4 (Toggle)", value=False, help="Parameter 4", key="embedded_p4_form")
                    with cols_params[1]:
                        if is_inventory_mode:
                            param2_form = st.number_input("Ordering Cost ($)", min_value=0, value=50, step=1, help="Fixed cost per order", key="embedded_p2_form")
                            param5_form = st.checkbox("Use Safety Stock", value=True, help="Calculate and maintain safety stock", key="embedded_p5_form")
                        else:
                            param2_form = st.number_input("Available Vehicles (Int ≥ 0)", min_value=0, value=3, step=1, help="Number of Available Vehicles", key="embedded_p2_form")
                            param5_form = st.checkbox("P5 (Checkbox)", value=False, help="Parameter 5", key="embedded_p5_form")
                    with cols_params[2]:
                        if is_inventory_mode:
                            param3_form = st.slider("Service Level (%)", min_value=0, max_value=100, value=95, help="Target service level percentage", key="embedded_p3_form")
                        else:
                            param3_form = st.slider("P3 (0-100)", min_value=0, max_value=100, value=50, help="Parameter 3", key="embedded_p3_form")

                    st.subheader("GPT-based Constraint Tweak")
                    gpt_prompt_tweak_form = st.text_area(
                        "Describe any custom model tweak (optional)",
                        height=100,
                        help="Enter any specific modifications or constraints for the model using natural language.",
                        key="embedded_gpt_tweak_form"
                    )

                    if st.button("Create Scenario", type="primary", key="embedded_create_scenario_btn"):
                        if not scenario_name_form:
                            st.error("Scenario Name cannot be empty.")
                        elif not snapshot_obj_form:
                            st.error("Please select a Snapshot.")
                        else:
                            if Scenario.objects.filter(name=scenario_name_form, snapshot=snapshot_obj_form).exists():
                                st.warning(f"A scenario named '{scenario_name_form}' already exists for snapshot '{snapshot_obj_form.name}'. Please choose a different name.")
                            else:
                                try:
                                    # Determine model type based on current context
                                    model_type = 'vrp'  # Default
                                    if 'active_inventory_tab' in st.session_state:
                                        model_type = 'inventory'
                                    
                                    new_scenario = Scenario.objects.create(
                                        name=scenario_name_form,
                                        snapshot=snapshot_obj_form,
                                        model_type=model_type,
                                        param1=param1_form,
                                        param2=param2_form,
                                        param3=param3_form,
                                        param4=param4_form,
                                        param5=param5_form,
                                        gpt_prompt=gpt_prompt_tweak_form,
                                        status="created"
                                    )
                                    st.success(f"✅ Scenario '{scenario_name_form}' created successfully!")
                                    st.session_state.global_logs.append(f"Created {model_type} scenario: {scenario_name_form}")
                                    
                                    # Clear selected snapshot
                                    if 'selected_snapshot_id' in st.session_state:
                                        del st.session_state.selected_snapshot_id
                                    
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error creating scenario: {str(e)}")
                                    st.session_state.global_logs.append(f"Scenario creation failed: {str(e)}")
            except Exception as e:
                st.error(f"Error loading snapshots: {e}")
                st.session_state.global_logs.append(f"Error loading snapshots: {e}")
                snapshot_names = []
                selected_snapshot_name_form = None
                snapshot_obj_form = None
                
        # List Existing Scenarios
        st.header("Manage and Run Scenarios")
        
        # Filter dropdowns
        col1, col2 = st.columns(2)
        
        with col1:
            # Filter by Snapshot
            snapshots_for_filter = Snapshot.objects.all().order_by("-created_at")
            snapshot_filter_options = ["All Snapshots"] + [snap.name for snap in snapshots_for_filter]
            selected_snapshot_filter = st.selectbox(
                "Filter by Snapshot",
                options=snapshot_filter_options,
                key="scenario_builder_snapshot_filter"
            )
        
        with col2:
            # Filter by Status
            status_filter_options = ["All Statuses", "created", "solving", "solved", "failed"]
            selected_status_filter = st.selectbox(
                "Filter by Status", 
                options=status_filter_options,
                key="scenario_builder_status_filter"
            )

        # Get filtered scenarios
        scenarios_query = Scenario.objects.all()
        
        if selected_snapshot_filter != "All Snapshots":
            scenarios_query = scenarios_query.filter(snapshot__name=selected_snapshot_filter)
        
        if selected_status_filter != "All Statuses":
            scenarios_query = scenarios_query.filter(status=selected_status_filter)
        
        scenarios = scenarios_query.order_by("-created_at")
        
        st.subheader(f"Found {scenarios.count()} Scenarios")
        
        if scenarios.exists():
            # Create scenario table headers
            header_cols = st.columns([3, 2, 1.5, 2, 2])
            with header_cols[0]:
                st.markdown("**Scenario Name**")
            with header_cols[1]:
                st.markdown("**Snapshot**")
            with header_cols[2]:
                st.markdown("**Status**")
            with header_cols[3]:
                st.markdown("**Actions**")
            with header_cols[4]:
                st.markdown("**Details**")
            
            st.markdown("---")
            
            # Display scenarios
            for scenario in scenarios:
                cols = st.columns([3, 2, 1.5, 2, 2])
                
                with cols[0]:
                    st.write(scenario.name)
                with cols[1]:
                    st.write(scenario.snapshot.name)
                with cols[2]:
                    if scenario.status == "solved":
                        st.success("● solved")
                    elif scenario.status == "failed":
                        st.error("● failed")
                    elif scenario.status == "solving":
                        st.warning("● solving")
                    else:
                        st.info("● created")
                with cols[3]:
                    # Actions column
                    action_col1, action_col2 = st.columns(2)
                    with action_col1:
                        if scenario.status in ["created", "failed"]:
                            if st.button("🚀 Run Model", key=f"sb_run_{scenario.id}"):
                                # Call the run model function
                                run_model_for_scenario(scenario.id)
                        elif scenario.status == "solving":
                            st.button("⏳ Running", disabled=True, key=f"sb_running_{scenario.id}")
                        else:
                            st.button("✅ Solved", disabled=True, key=f"sb_solved_{scenario.id}")
                    
                    with action_col2:
                        if scenario.status == "solved":
                            if st.button("📊 View Results", key=f"sb_view_{scenario.id}"):
                                st.session_state.selected_snapshot_for_results = scenario.snapshot.name
                                st.session_state.selected_scenario_for_results = scenario.name
                                st.session_state.active_vrp_tab = 3  # Switch to View Results tab
                                st.query_params.tab = "view_results"
                                st.success(f"✅ Switching to View Results for {scenario.name}...")
                                st.rerun()
                        else:
                            st.button("📊 View Results", disabled=True, key=f"sb_view_disabled_{scenario.id}")
                
                with cols[4]:
                    # Details dropdown
                    details_options = ["Show Details", "Parameters", "Constraints", "Logs"]
                    selected_detail = st.selectbox(
                        "Details",
                        options=details_options,
                        key=f"sb_details_{scenario.id}"
                    )
                    
                    if selected_detail == "Parameters":
                        st.info(f"P1: {scenario.param1}, P2: {scenario.param2}, P3: {scenario.param3}")
                    elif selected_detail == "Constraints":
                        if scenario.gpt_prompt:
                            st.info(f"Constraints: {scenario.gpt_prompt}")
                        else:
                            st.info("No constraints specified")
                    elif selected_detail == "Logs":
                        st.info(f"Created: {scenario.created_at.strftime('%Y-%m-%d %H:%M')}")
                        if scenario.reason:
                            st.warning(f"Reason: {scenario.reason}")
                
                st.divider()
        else:
            st.info("No scenarios found matching the selected filters.")

        # Right log panel
        try:
            from components.right_log_panel import show_right_log_panel
            show_right_log_panel(st.session_state.global_logs)
        except ImportError:
            with st.expander("📋 Activity Logs"):
                for log in st.session_state.global_logs[-10:]:
                    st.text(log)

        # Debug Panel
        if st.checkbox("Show Debug Info", value=False, key="embedded_scenario_debug"):
            with st.expander("🔍 Debug Panel", expanded=True):
                st.markdown("### Session State")
                debug_state = {k: v for k, v in st.session_state.items() if not k.startswith('embedded_')}
                st.json(debug_state)
            
    except Exception as e:
        st.error(f"Error loading scenario builder: {e}")
        st.write("Basic scenario builder interface")

def show_embedded_view_results():
    """Embedded view results functionality"""
    try:
        # Setup Django
        import django
        import os
        import sys
        import json
        import pandas as pd
        import plotly.express as px
        import plotly.graph_objects as go
        from datetime import datetime
        
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        BACKEND_PATH = os.path.abspath(os.path.join(BASE_DIR, "backend"))
        MEDIA_ROOT = os.path.abspath(os.path.join(BASE_DIR, "media"))
        sys.path.append(BACKEND_PATH)
        
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "orsaas_backend.settings")
        django.setup()
        
        from core.models import Scenario
        
        # Initialize logs
        if "global_logs" not in st.session_state:
            st.session_state.global_logs = ["View Results initialized."]

        # Initialize session state for GPT analysis
        if "gpt_analysis_result" not in st.session_state:
            st.session_state.gpt_analysis_result = None
        if "gpt_analysis_loading" not in st.session_state:
            st.session_state.gpt_analysis_loading = False

        # Get selected scenario info from session state
        selected_snapshot = st.session_state.get("selected_snapshot_for_results")
        selected_scenario = st.session_state.get("selected_scenario_for_results")

        if not selected_snapshot or not selected_scenario:
            st.header("Select Scenario to View Results")
            
            # Two horizontal dropdowns for snapshot and scenario selection
            col1, col2 = st.columns(2)
            
            with col1:
                # Snapshot selection dropdown
                snapshots = Snapshot.objects.all().order_by("-created_at")
                if snapshots.exists():
                    snapshot_choices = {snap.name: snap.id for snap in snapshots}
                    selected_snapshot_name = st.selectbox(
                        "Select Snapshot",
                        options=list(snapshot_choices.keys()),
                        key="embedded_results_snapshot_select"
                    )
                else:
                    st.warning("No snapshots available.")
                    return
            
            with col2:
                # Scenario selection dropdown (filtered by selected snapshot)
                if selected_snapshot_name:
                    selected_snapshot_obj = Snapshot.objects.get(name=selected_snapshot_name)
                    scenarios = Scenario.objects.filter(
                        snapshot=selected_snapshot_obj, 
                        status="solved"
                    ).order_by("-created_at")
                    
                    if scenarios.exists():
                        scenario_choices = {scen.name: scen.id for scen in scenarios}
                        selected_scenario_name = st.selectbox(
                            "Select Scenario",
                            options=list(scenario_choices.keys()),
                            key="embedded_results_scenario_select"
                        )
                    else:
                        st.warning(f"No solved scenarios available for snapshot '{selected_snapshot_name}'.")
                        return
                else:
                    st.selectbox("Select Scenario", options=[], disabled=True, key="embedded_results_scenario_disabled")
                    return
            
            # Load Results button
            if st.button("Load Results", key="embedded_load_results"):
                st.session_state.selected_snapshot_for_results = selected_snapshot_name
                st.session_state.selected_scenario_for_results = selected_scenario_name
                st.rerun()
            return

        try:
            # Fetch scenario from database
            scenario = Scenario.objects.select_related('snapshot').get(
                name=selected_scenario,
                snapshot__name=selected_snapshot
            )
            
            if scenario.status != "solved":
                st.error(f"Scenario '{scenario.name}' is not solved. Current status: {scenario.status}")
                if st.button("← Back to Scenario Selection", key="embedded_back_button"):
                    if 'selected_snapshot_for_results' in st.session_state:
                        del st.session_state.selected_snapshot_for_results
                    if 'selected_scenario_for_results' in st.session_state:
                        del st.session_state.selected_scenario_for_results
                    st.session_state.active_vrp_tab = 2  # Switch to Scenario Builder tab
                    st.query_params.tab = "scenario_builder"
                    st.rerun()
                return

            # Load solution data
            solution_path = os.path.join(MEDIA_ROOT, "scenarios", str(scenario.id), "outputs", "solution_summary.json")
            if not os.path.exists(solution_path):
                alt_solution_path = os.path.join(MEDIA_ROOT, "scenarios", str(scenario.id), "solution_summary.json")
                if os.path.exists(alt_solution_path):
                    solution_path = alt_solution_path
                else:
                    st.error(f"Solution file not found for scenario '{scenario.name}'")
                    if st.button("← Back to Scenario Selection", key="embedded_back_no_solution"):
                        if 'selected_snapshot_for_results' in st.session_state:
                            del st.session_state.selected_snapshot_for_results
                        if 'selected_scenario_for_results' in st.session_state:
                            del st.session_state.selected_scenario_for_results
                        st.rerun()
                    return

            with open(solution_path, 'r') as f:
                solution = json.load(f)

            # Page Header
            st.title("📊 Solution Results")
            
            # Back button
            if st.button("← Back to Scenario Selection", key="embedded_back_button"):
                if 'selected_snapshot_for_results' in st.session_state:
                    del st.session_state.selected_snapshot_for_results
                if 'selected_scenario_for_results' in st.session_state:
                    del st.session_state.selected_scenario_for_results
                st.session_state.active_vrp_tab = 2  # Switch to Scenario Builder tab
                st.query_params.tab = "scenario_builder"
                st.rerun()

            # Scenario Info
            st.subheader("Scenario Information")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Scenario", scenario.name)
                st.metric("Snapshot", scenario.snapshot.name)
            with col2:
                st.metric("Created", scenario.created_at.strftime("%Y-%m-%d %H:%M"))
                st.metric("Parameters", f"P1: {scenario.param1}, P2: {scenario.param2}, P3: {scenario.param3}")

            # Applied Constraints Section
            if 'applied_constraints' in solution and solution['applied_constraints']:
                st.subheader("🎯 Applied Constraints")
                
                for i, constraint in enumerate(solution['applied_constraints']):
                    with st.expander(f"Constraint {i+1}: {constraint.get('type', 'Unknown')}", expanded=True):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write("**Original Prompt:**")
                            st.code(constraint.get('original', 'N/A'))
                        with col2:
                            st.write("**Constraint Type:**")
                            st.info(constraint.get('type', 'Unknown'))
                        with col3:
                            st.write("**Parsing Method:**")
                            method = constraint.get('method', 'unknown')
                            if method == 'pattern_matching':
                                st.success("🎯 Pattern Matching")
                                st.caption("Confidence: ≥85% (High)")
                            elif method == 'llm':
                                st.warning("🤖 LLM Parsing")  
                                st.caption("Confidence: <85% (Used OpenAI)")
                            elif method == 'fallback':
                                st.info("🔄 Fallback Parsing")
                                st.caption("No pattern match, OpenAI unavailable")
                            elif method == 'fallback_pattern':
                                st.success("🔍 Fallback Pattern Match")
                                st.caption("Matched improved pattern rules")
                            else:
                                st.error("❓ Unknown Method")
                                st.caption(f"Method: {method}")
            else:
                st.subheader("🎯 Applied Constraints")
                st.info("No custom constraints were applied to this scenario.")

            # GPT Constraint Prompt Display
            if scenario.gpt_prompt and scenario.gpt_prompt.strip():
                st.subheader("🗣️ User Constraint Prompt")
                st.info(f"💬 **Original Request:** {scenario.gpt_prompt}")
                if 'applied_constraints' not in solution or not solution['applied_constraints']:
                    st.warning("⚠️ Constraint prompt was provided but no constraints were successfully applied.")

            # KPI Cards
            st.subheader("Key Performance Indicators")
            
            # Determine model type from scenario
            model_type = scenario.model_type if hasattr(scenario, 'model_type') else 'vrp'
            
            if model_type == 'inventory':
                # Inventory KPIs
                kpi_cols = st.columns(4)
                with kpi_cols[0]:
                    st.metric("Total Annual Cost", f"${solution.get('total_cost', 0):,.2f}")
                with kpi_cols[1]:
                    st.metric("Total Inventory Value", f"${solution.get('total_inventory_value', 0):,.2f}")
                with kpi_cols[2]:
                    st.metric("Items Optimized", str(solution.get('num_items', 0)))
                with kpi_cols[3]:
                    st.metric("Service Level", f"{solution.get('service_level', 0)*100:.1f}%")
            else:
                # VRP KPIs
                kpi_cols = st.columns(4)
                with kpi_cols[0]:
                    st.metric("Total Distance", f"{solution['total_distance']:.2f} km")
                with kpi_cols[1]:
                    st.metric("Vehicles Used", str(solution['vehicle_count']))
                with kpi_cols[2]:
                    total_stops = sum(len(route) - 2 for route in solution['routes'])
                    st.metric("Total Stops", str(total_stops))
                with kpi_cols[3]:
                    avg_route_length = solution['total_distance'] / len(solution['routes'])
                    st.metric("Avg Route Length", f"{avg_route_length:.2f} km")

            # Model-specific detailed results
            if model_type == 'inventory':
                # Inventory-specific results
                st.subheader("Inventory Policy Details")
                
                # Load inventory items
                if 'items' in solution:
                    items_df = pd.DataFrame(solution['items'])
                    
                    # Display key metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Items", len(items_df))
                    with col2:
                        total_ordering_cost = items_df['ordering_cost'].sum()
                        st.metric("Total Ordering Cost", f"${total_ordering_cost:,.2f}")
                    with col3:
                        total_holding_cost = items_df['holding_cost'].sum()
                        st.metric("Total Holding Cost", f"${total_holding_cost:,.2f}")
                    
                    # Display policy table
                    st.dataframe(items_df[['item_id', 'demand', 'unit_cost', 'eoq', 'safety_stock', 'reorder_point', 'total_cost']], use_container_width=True)
                    
                    # Visualizations
                    st.subheader("Cost Analysis")
                    viz_cols = st.columns(2)
                    
                    with viz_cols[0]:
                        # Cost breakdown by item
                        fig_cost = px.bar(
                            items_df.head(20),
                            x='item_id',
                            y='total_cost',
                            title="Total Cost by Item (Top 20)",
                            color='total_cost',
                            color_continuous_scale="Viridis"
                        )
                        fig_cost.update_xaxes(tickangle=45)
                        st.plotly_chart(fig_cost, use_container_width=True)
                    
                    with viz_cols[1]:
                        # EOQ vs Demand scatter
                        fig_eoq = px.scatter(
                            items_df,
                            x='demand',
                            y='eoq',
                            size='total_cost',
                            color='category' if 'category' in items_df.columns else None,
                            title="EOQ vs Demand",
                            hover_data=['item_id']
                        )
                        st.plotly_chart(fig_eoq, use_container_width=True)
                else:
                    st.warning("No detailed item data available in solution")
                    
            else:
                # VRP-specific results (existing code)
                # Load demand data for route calculations
                try:
                    dataset_path = os.path.join(MEDIA_ROOT, scenario.snapshot.linked_upload.file.name)
                    demand_df = pd.read_csv(dataset_path)
                    demand_dict = {}
                    if 'demand' in demand_df.columns:
                        demand_dict = dict(zip(demand_df.index, demand_df['demand']))
                    else:
                        st.warning("No demand column found in dataset")
                except Exception as e:
                    st.warning(f"Could not load demand data: {e}")
                    demand_dict = {}

                # Enhanced Routes Table with Load/Demand
                st.subheader("Route Details")
                try:
                    route_rows = []
                    for i, route in enumerate(solution.get("routes", []), 1):
                        route_id = f"R{i}"
                        if isinstance(route, dict):
                            stops = len(route.get("stops", [])) - 2 if len(route.get("stops", [])) > 2 else 0
                            distance = round(route.get("distance", 0), 2)
                            duration = round(route.get("duration", 0), 2)
                            stop_sequence = route.get("stops", [])
                            sequence = " → ".join(str(node) for node in stop_sequence)
                        else:
                            stops = len(route) - 2 if len(route) > 2 else 0
                            distance = None
                            duration = None
                            stop_sequence = route
                            sequence = " → ".join(str(node) for node in route)
                        
                        # Calculate total load/demand for this route
                        total_load = 0
                        if demand_dict:
                            customer_stops = [stop for stop in stop_sequence if stop != 0]
                            total_load = sum(demand_dict.get(stop, 0) for stop in customer_stops)
                        
                        route_rows.append({
                            "Route ID": route_id,
                            "Stops": stops,
                            "Total Load": total_load if demand_dict else "N/A",
                            "Distance (km)": distance,
                            "Duration (min)": duration,
                            "Sequence": sequence
                        })
                    
                    route_df = pd.DataFrame(route_rows)
                    st.dataframe(route_df, use_container_width=True)
                    
                    # Load utilization metrics
                    if demand_dict:
                        total_demand = sum(demand_dict.get(i, 0) for i in demand_dict.keys() if i != 0)
                        vehicle_capacity = scenario.param1
                        
                        st.subheader("📊 Load Analysis")
                        load_cols = st.columns(3)
                        with load_cols[0]:
                            st.metric("Total Demand", f"{total_demand} units")
                        with load_cols[1]:
                            max_load_per_route = max([row["Total Load"] for row in route_rows if row["Total Load"] != "N/A"], default=0)
                            st.metric("Max Route Load", f"{max_load_per_route} units")
                        with load_cols[2]:
                            if vehicle_capacity and max_load_per_route:
                                utilization = (max_load_per_route / vehicle_capacity) * 100
                                st.metric("Max Utilization", f"{utilization:.1f}%")
                            else:
                                st.metric("Max Utilization", "N/A")
                                
                except Exception as e:
                    st.error(f"⚠️ Error loading Route Details: {e}")

                # Enhanced Visualizations
                st.subheader("Route Analysis")
                viz_cols = st.columns(2)
                
                with viz_cols[0]:
                    # Distance per Route Bar Chart
                    fig_distance = px.bar(
                        pd.DataFrame(route_rows),
                        x="Route ID",
                        y="Distance (km)",
                        title="Distance per Route",
                        color="Distance (km)",
                        color_continuous_scale="Viridis"
                    )
                    st.plotly_chart(fig_distance, use_container_width=True)
                
                with viz_cols[1]:
                    # Load per Route Bar Chart (if demand data available)
                    if demand_dict:
                        fig_load = px.bar(
                            pd.DataFrame(route_rows),
                            x="Route ID", 
                            y="Total Load",
                            title="Load per Route",
                            color="Total Load",
                            color_continuous_scale="Plasma"
                        )
                        st.plotly_chart(fig_load, use_container_width=True)
                    else:
                        # Fallback to stops per route
                        fig_stops = px.bar(
                            pd.DataFrame(route_rows),
                            x="Route ID",
                            y="Stops",
                            title="Stops per Route",
                            color="Stops",
                            color_continuous_scale="Plasma"
                        )
                        st.plotly_chart(fig_stops, use_container_width=True)

            # GPT-powered Solution Analysis
            st.subheader("🤖 GPT-powered Solution Analysis")
            st.write("Ask questions about this solution in natural language. Examples:")
            st.info("""
            - "What is the average utilization by vehicle?"
            - "Show a table of stops per route"
            - "Plot the distance distribution across routes"
            - "Which route has the highest demand?"
            """)
            
            # User input for GPT analysis
            user_question = st.text_input("Enter your question about the solution:", key="embedded_gpt_question")
            
            # Function to run GPT analysis
            def run_gpt_analysis():
                st.session_state.gpt_analysis_loading = True
                st.session_state.global_logs.append(f"Starting GPT analysis for scenario {scenario.id} with question: {user_question}")
                try:
                    sys.path.append(os.path.join(BACKEND_PATH, "services"))
                    try:
                        from gpt_output_analysis_new import analyze_output
                        st.session_state.global_logs.append(f"Using new gpt_output_analysis_new module")
                    except ImportError:
                        from gpt_output_analysis import analyze_output
                        st.session_state.global_logs.append(f"Using original gpt_output_analysis module")
                    
                    st.session_state.global_logs.append(f"Calling analyze_output with question: {user_question} and scenario_id: {scenario.id}")
                    result = analyze_output(user_question, scenario.id)
                    st.session_state.global_logs.append(f"Got result from analyze_output: {result}")
                    
                    if not isinstance(result, dict) or 'type' not in result or 'data' not in result:
                        st.session_state.global_logs.append(f"Invalid result format: {result}")
                        result = {"type": "error", "data": "Invalid response format from analysis service"}
                    
                    st.session_state.gpt_analysis_result = result
                    st.session_state.global_logs.append(f"GPT analysis completed with result type: {st.session_state.gpt_analysis_result.get('type', 'unknown')}")
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    st.session_state.global_logs.append(f"Error in GPT analysis: {str(e)}")
                    st.session_state.global_logs.append(f"Error details: {error_details}")
                    st.session_state.gpt_analysis_result = {"type": "error", "data": f"Error: {str(e)}"}
                
                st.session_state.gpt_analysis_loading = False
            
            # Submit button for GPT analysis
            analyze_col1, analyze_col2 = st.columns([3, 1])
            
            with analyze_col2:
                if st.button("Analyze", key="embedded_analyze_button", use_container_width=True):
                    if user_question:
                        st.session_state.global_logs.append("Analyze button clicked")
                        with analyze_col1:
                            st.write("Starting analysis...")
                        run_gpt_analysis()
                        try:
                            st.rerun()
                        except:
                            pass
                    else:
                        st.warning("Please enter a question first")
                        st.session_state.global_logs.append("Analyze button clicked but no question entered")
            
            if st.session_state.gpt_analysis_loading:
                with st.spinner("Analyzing solution..."):
                    st.empty()
            
            # Display GPT analysis results
            if st.session_state.gpt_analysis_result:
                result = st.session_state.gpt_analysis_result
                result_type = result.get("type", "")
                result_data = result.get("data", "")
                
                if result_type == "error":
                    st.error(f"Error: {result_data}")
                elif result_type == "value":
                    st.success(f"Answer: {result_data}")
                elif result_type == "table":
                    try:
                        if len(result_data) > 1:
                            headers = result_data[0]
                            rows = result_data[1:]
                            df = pd.DataFrame(rows, columns=headers)
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.warning("Table data is empty or invalid")
                    except Exception as e:
                        st.error(f"Error displaying table: {str(e)}")
                        st.json(result_data)
                elif result_type == "chart":
                    try:
                        st.session_state.global_logs.append(f"Chart data: {result_data}")
                        
                        chart_type = result_data.get("chart_type", "bar")
                        title = result_data.get("title", "Chart")
                        labels = result_data.get("labels", [])
                        values = result_data.get("values", [])
                        
                        if not isinstance(labels, list):
                            labels = [str(labels)]
                        if not isinstance(values, list):
                            try:
                                values = [float(values)]
                            except (ValueError, TypeError):
                                values = [0]
                        
                        if len(labels) != len(values):
                            if len(labels) < len(values):
                                labels.extend([f"Item {i+1}" for i in range(len(labels), len(values))])
                            else:
                                values.extend([0] * (len(labels) - len(values)))
                        
                        chart_df = pd.DataFrame({"labels": labels, "values": values})
                        
                        if chart_type == "bar":
                            fig = px.bar(chart_df, x="labels", y="values", title=title)
                        elif chart_type == "line":
                            fig = px.line(chart_df, x="labels", y="values", title=title)
                        elif chart_type == "pie":
                            fig = px.pie(chart_df, names="labels", values="values", title=title)
                        else:
                            fig = px.bar(chart_df, x="labels", y="values", title=f"{title} (Fallback Bar Chart)")
                        
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating chart: {str(e)}")
                        st.dataframe(pd.DataFrame({"labels": labels, "values": values}))
                else:
                    st.json(result_data)

            # Raw Solution Data
            with st.expander("View Raw Solution Data"):
                st.json(solution)

        except Scenario.DoesNotExist:
            st.error(f"Scenario '{selected_scenario}' not found in snapshot '{selected_snapshot}'")
        except Exception as e:
            st.error(f"Error loading results: {str(e)}")
            st.session_state.global_logs.append(f"Error loading results: {str(e)}")

        # Right log panel
        try:
            from components.right_log_panel import show_right_log_panel
            show_right_log_panel(st.session_state.global_logs)
        except ImportError:
            with st.expander("📋 Activity Logs"):
                for log in st.session_state.global_logs[-10:]:
                    st.text(log)

        # Debug Panel
        if st.checkbox("Show Debug Info", value=False, key="embedded_results_debug"):
            with st.expander("🔍 Debug Panel", expanded=True):
                st.markdown("### Session State")
                debug_state = {k: v for k, v in st.session_state.items() if not k.startswith('embedded_')}
                st.json(debug_state)
            
    except Exception as e:
        st.error(f"Error loading view results: {e}")
        st.write("Basic results interface")

def show_embedded_compare_outputs():
    """Embedded compare outputs functionality"""
    try:
        # Setup Django
        import django
        import os
        import sys
        import pandas as pd
        import plotly.express as px
        import plotly.graph_objects as go
        import json
        from datetime import datetime
        
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        BACKEND_PATH = os.path.abspath(os.path.join(BASE_DIR, "backend"))
        MEDIA_ROOT = os.path.abspath(os.path.join(BASE_DIR, "media"))
        sys.path.append(BACKEND_PATH)
        
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "orsaas_backend.settings")
        django.setup()
        
        from core.models import Scenario, Snapshot
        
        # Initialize logs
        if "global_logs" not in st.session_state:
            st.session_state.global_logs = ["Compare Outputs initialized."]

        st.title("Compare Scenario Outputs")

        # Main comparison interface
        st.header("Select Scenarios to Compare")
        
        # Select Snapshot dropdown
        snapshots = Snapshot.objects.all().order_by("-created_at")
        if snapshots.exists():
            snapshot_choices = [""] + [snap.name for snap in snapshots]
            selected_snapshot_name = st.selectbox(
                "Select Snapshot",
                options=snapshot_choices,
                key="compare_snapshot_select",
                help="Choose a snapshot to compare scenarios from"
            )
            
            if selected_snapshot_name:
                # Get solved scenarios for the selected snapshot
                selected_snapshot_obj = Snapshot.objects.get(name=selected_snapshot_name)
                solved_scenarios = Scenario.objects.filter(
                    snapshot=selected_snapshot_obj, 
                    status="solved"
                ).order_by("-created_at")
                
                if solved_scenarios.exists():
                    scenario_choices = [f"{scen.name}" for scen in solved_scenarios]
                    
                    # Multi-select for scenarios (2 to 4)
                    selected_scenarios = st.multiselect(
                        "Select 2 to 4 Scenarios",
                        options=scenario_choices,
                        key="compare_scenarios_multiselect",
                        help="Choose 2-4 scenarios to compare their performance"
                    )
                    
                    # Validation and comparison
                    if len(selected_scenarios) < 2:
                        st.info("Please select at least 2 scenarios to compare.")
                    elif len(selected_scenarios) > 4:
                        st.warning("Please select maximum 4 scenarios for comparison.")
                    else:
                        # Compare button
                        if st.button("Compare Scenarios", type="primary", key="compare_scenarios_btn"):
                            st.success(f"Comparing {len(selected_scenarios)} scenarios...")
                            
                            # Load and compare scenario data
                            comparison_data = []
                            model_type = None  # Will be determined from first scenario
                            
                            for scenario_name in selected_scenarios:
                                try:
                                    scenario = Scenario.objects.get(name=scenario_name, snapshot=selected_snapshot_obj)
                                    
                                    # Determine model type from first scenario
                                    if model_type is None:
                                        model_type = scenario.model_type if hasattr(scenario, 'model_type') else 'vrp'
                                    
                                    # Load solution data
                                    solution_path = os.path.join(MEDIA_ROOT, "scenarios", str(scenario.id), "outputs", "solution_summary.json")
                                    if not os.path.exists(solution_path):
                                        solution_path = os.path.join(MEDIA_ROOT, "scenarios", str(scenario.id), "solution_summary.json")
                                    
                                    if os.path.exists(solution_path):
                                        with open(solution_path, 'r') as f:
                                            solution = json.load(f)
                                        
                                        if model_type == 'inventory':
                                            # Extract inventory KPIs
                                            comparison_data.append({
                                                "Scenario": scenario_name,
                                                "Total Annual Cost": f"${solution.get('total_cost', 0):,.2f}",
                                                "Inventory Value": f"${solution.get('total_inventory_value', 0):,.2f}",
                                                "Items Optimized": solution.get('num_items', 0),
                                                "Service Level": f"{solution.get('service_level', 0)*100:.1f}%",
                                                "Parameters": f"Hold:{scenario.param1}%, Order:${scenario.param2}, SL:{scenario.param3}%",
                                                "Constraints": scenario.gpt_prompt if scenario.gpt_prompt else "None"
                                            })
                                        else:
                                            # Extract VRP KPIs
                                            routes = solution.get('routes', [])
                                            total_routes = len(routes)
                                            total_distance = float(solution.get('total_distance', 0))
                                            customers_served = sum(len(r.get('stops', r)) - 2 for r in routes if isinstance(r, (dict, list)))
                                            
                                            comparison_data.append({
                                                "Scenario": scenario_name,
                                                "Total Distance (km)": round(total_distance, 2),
                                                "Vehicles Used": total_routes,
                                                "Customers Served": customers_served,
                                                "Avg Route Length (km)": round(total_distance / total_routes, 2) if total_routes > 0 else 0,
                                                "Parameters": f"P1:{scenario.param1}, P2:{scenario.param2}, P3:{scenario.param3}",
                                                "Constraints": scenario.gpt_prompt if scenario.gpt_prompt else "None"
                                            })
                                    else:
                                        st.warning(f"Solution file not found for scenario '{scenario_name}'")
                                        
                                except Exception as e:
                                    st.error(f"Error loading scenario '{scenario_name}': {str(e)}")
                            
                            if comparison_data:
                                # Display comparison table
                                st.subheader("📊 Scenario Comparison")
                                comparison_df = pd.DataFrame(comparison_data)
                                st.dataframe(comparison_df, use_container_width=True, hide_index=True)
                                
                                # Visualization charts
                                st.subheader("📈 Performance Comparison")
                                
                                # Create comparison charts based on model type
                                col1, col2 = st.columns(2)
                                
                                if model_type == 'inventory':
                                    # Inventory-specific charts
                                    with col1:
                                        # Extract numeric values for plotting
                                        cost_values = []
                                        for row in comparison_data:
                                            cost_str = row["Total Annual Cost"].replace('$', '').replace(',', '')
                                            cost_values.append(float(cost_str))
                                        
                                        # Total Cost comparison
                                        fig_cost = px.bar(
                                            x=[row["Scenario"] for row in comparison_data],
                                            y=cost_values,
                                            title="Total Annual Cost Comparison",
                                            labels={'x': 'Scenario', 'y': 'Total Annual Cost ($)'},
                                            color=cost_values,
                                            color_continuous_scale="Viridis"
                                        )
                                        fig_cost.update_layout(showlegend=False)
                                        st.plotly_chart(fig_cost, use_container_width=True)
                                    
                                    with col2:
                                        # Extract inventory values
                                        inv_values = []
                                        for row in comparison_data:
                                            inv_str = row["Inventory Value"].replace('$', '').replace(',', '')
                                            inv_values.append(float(inv_str))
                                        
                                        # Inventory Value comparison
                                        fig_inventory = px.bar(
                                            x=[row["Scenario"] for row in comparison_data],
                                            y=inv_values,
                                            title="Total Inventory Value Comparison",
                                            labels={'x': 'Scenario', 'y': 'Inventory Value ($)'},
                                            color=inv_values,
                                            color_continuous_scale="Plasma"
                                        )
                                        fig_inventory.update_layout(showlegend=False)
                                        st.plotly_chart(fig_inventory, use_container_width=True)
                                    
                                    # Radar chart for inventory metrics
                                    st.subheader("🎯 Multi-Dimensional Performance Radar")
                                    
                                    # Prepare data for radar chart
                                    fig_radar = go.Figure()
                                    
                                    for row in comparison_data:
                                        # Extract numeric values
                                        cost = float(row["Total Annual Cost"].replace('$', '').replace(',', ''))
                                        inv_value = float(row["Inventory Value"].replace('$', '').replace(',', ''))
                                        service_level = float(row["Service Level"].replace('%', ''))
                                        items = row["Items Optimized"]
                                        
                                        # Normalize values (inverse for cost - lower is better)
                                        max_cost = max(float(r["Total Annual Cost"].replace('$', '').replace(',', '')) for r in comparison_data)
                                        max_inv = max(float(r["Inventory Value"].replace('$', '').replace(',', '')) for r in comparison_data)
                                        max_items = max(r["Items Optimized"] for r in comparison_data)
                                        
                                        normalized_cost = 100 - (cost / max_cost * 100) if max_cost > 0 else 100
                                        normalized_inv = 100 - (inv_value / max_inv * 100) if max_inv > 0 else 100
                                        normalized_service = service_level
                                        normalized_items = (items / max_items * 100) if max_items > 0 else 0
                                        
                                        values = [normalized_cost, normalized_inv, normalized_service, normalized_items]
                                        categories = ['Cost Efficiency', 'Inventory Efficiency', 'Service Level', 'Items Coverage']
                                        
                                        fig_radar.add_trace(go.Scatterpolar(
                                            r=values + [values[0]],
                                            theta=categories + [categories[0]],
                                            fill='toself',
                                            name=row["Scenario"]
                                        ))
                                    
                                    fig_radar.update_layout(
                                        polar=dict(
                                            radialaxis=dict(
                                                visible=True,
                                                range=[0, 100]
                                            )),
                                        showlegend=True,
                                        title="Inventory Performance Radar (Higher is Better)"
                                    )
                                    
                                    st.plotly_chart(fig_radar, use_container_width=True)
                                    
                                    # Best performer analysis for inventory
                                    st.subheader("🏆 Performance Analysis")
                                    
                                    # Find best performers
                                    costs = [float(row["Total Annual Cost"].replace('$', '').replace(',', '')) for row in comparison_data]
                                    inv_values = [float(row["Inventory Value"].replace('$', '').replace(',', '')) for row in comparison_data]
                                    service_levels = [float(row["Service Level"].replace('%', '')) for row in comparison_data]
                                    
                                    best_cost_idx = costs.index(min(costs))
                                    best_inv_idx = inv_values.index(min(inv_values))
                                    best_service_idx = service_levels.index(max(service_levels))
                                    
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        st.metric(
                                            "💰 Lowest Cost",
                                            comparison_data[best_cost_idx]["Scenario"],
                                            comparison_data[best_cost_idx]["Total Annual Cost"]
                                        )
                                    
                                    with col2:
                                        st.metric(
                                            "📦 Lowest Inventory",
                                            comparison_data[best_inv_idx]["Scenario"],
                                            comparison_data[best_inv_idx]["Inventory Value"]
                                        )
                                    
                                    with col3:
                                        st.metric(
                                            "⭐ Best Service",
                                            comparison_data[best_service_idx]["Scenario"],
                                            comparison_data[best_service_idx]["Service Level"]
                                        )
                                    
                                else:
                                    # VRP-specific charts (existing code)
                                    with col1:
                                        # Total Distance comparison
                                        fig_distance = px.bar(
                                            comparison_df,
                                            x="Scenario",
                                            y="Total Distance (km)",
                                            title="Total Distance Comparison",
                                            color="Total Distance (km)",
                                            color_continuous_scale="Viridis"
                                        )
                                        fig_distance.update_layout(showlegend=False)
                                        st.plotly_chart(fig_distance, use_container_width=True)
                                    
                                    with col2:
                                        # Vehicles Used comparison
                                        fig_vehicles = px.bar(
                                            comparison_df,
                                            x="Scenario",
                                            y="Vehicles Used",
                                            title="Vehicles Used Comparison",
                                            color="Vehicles Used",
                                            color_continuous_scale="Plasma"
                                        )
                                        fig_vehicles.update_layout(showlegend=False)
                                        st.plotly_chart(fig_vehicles, use_container_width=True)
                                    
                                    # Radar chart for multi-dimensional comparison
                                    st.subheader("🎯 Multi-Dimensional Performance Radar")
                                    
                                    # Normalize metrics for radar chart
                                    metrics = ["Total Distance (km)", "Vehicles Used", "Customers Served"]
                                    
                                    fig_radar = go.Figure()
                                    
                                    for _, row in comparison_df.iterrows():
                                        values = []
                                        for metric in metrics:
                                            # Normalize to 0-100 scale (inverse for distance - lower is better)
                                            if metric == "Total Distance (km)":
                                                max_val = comparison_df[metric].max()
                                                normalized = 100 - (row[metric] / max_val * 100)
                                            else:
                                                max_val = comparison_df[metric].max()
                                                normalized = (row[metric] / max_val * 100) if max_val > 0 else 0
                                            values.append(normalized)
                                        
                                        fig_radar.add_trace(go.Scatterpolar(
                                            r=values + [values[0]],  # Close the polygon
                                            theta=metrics + [metrics[0]],
                                            fill='toself',
                                            name=row["Scenario"]
                                        ))
                                    
                                    fig_radar.update_layout(
                                        polar=dict(
                                            radialaxis=dict(
                                                visible=True,
                                                range=[0, 100]
                                            )),
                                        showlegend=True,
                                        title="Performance Radar Chart (Higher is Better)"
                                    )
                                    
                                    st.plotly_chart(fig_radar, use_container_width=True)
                                    
                                    # Best performer analysis
                                    st.subheader("🏆 Performance Analysis")
                                    
                                    # Find best performers
                                    best_distance = comparison_df.loc[comparison_df["Total Distance (km)"].idxmin()]
                                    best_efficiency = comparison_df.loc[comparison_df["Vehicles Used"].idxmin()]
                                    best_coverage = comparison_df.loc[comparison_df["Customers Served"].idxmax()]
                                    
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        st.metric(
                                            "🚗 Shortest Distance",
                                            f"{best_distance['Scenario']}",
                                            f"{best_distance['Total Distance (km)']} km"
                                        )
                                    
                                    with col2:
                                        st.metric(
                                            "⚡ Most Efficient",
                                            f"{best_efficiency['Scenario']}",
                                            f"{best_efficiency['Vehicles Used']} vehicles"
                                        )
                                    
                                    with col3:
                                        st.metric(
                                            "📈 Best Coverage",
                                            f"{best_coverage['Scenario']}",
                                            f"{best_coverage['Customers Served']} customers"
                                        )
                                
                                # Export comparison data
                                st.subheader("💾 Export Results")
                                csv_data = comparison_df.to_csv(index=False)
                                st.download_button(
                                    label="📥 Download Comparison as CSV",
                                    data=csv_data,
                                    file_name=f"scenario_comparison_{selected_snapshot_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv"
                                )
                                
                else:
                    st.warning(f"No solved scenarios found for snapshot '{selected_snapshot_name}'. Please solve some scenarios first.")
            else:
                st.info("Please select a snapshot to view available scenarios.")
        else:
            st.warning("No snapshots available. Please create snapshots and scenarios first.")

        # Right log panel
        try:
            from components.right_log_panel import show_right_log_panel
            show_right_log_panel(st.session_state.global_logs)
        except ImportError:
            with st.expander("📋 Activity Logs"):
                for log in st.session_state.global_logs[-10:]:
                    st.text(log)

        # Debug Panel
        if st.checkbox("Show Debug Info", value=False, key="embedded_compare_debug"):
            with st.expander("🔍 Debug Panel", expanded=True):
                st.markdown("### Session State")
                debug_state = {k: v for k, v in st.session_state.items() if not k.startswith('embedded_')}
                st.json(debug_state)
            
    except Exception as e:
        st.error(f"Error loading compare outputs: {e}")
        st.write("Basic comparison interface")

def show_placeholder_application(app_name):
    """Show optimization applications - now with full inventory support"""
    if app_name == "📦 Inventory Optimization":
        show_inventory_function()  # Changed to use same workflow as VRP
    else:
        # Keep placeholder for other models
        st.title(f"{app_name}")
        st.write(f"Welcome to the {app_name} optimization module")
        
        st.info("🚧 This module is under development and will be available in future updates.")
        
        # Show similar structure but non-functional
        st.markdown("### 📋 Planned Features")
        
        features = {
            "📅 Scheduling": [
                "Resource scheduling optimization",
                "Task assignment and sequencing", 
                "Capacity planning",
                "Timeline optimization"
            ],
            "🌐 Network Flow": [
                "Network flow optimization",
                "Transportation problems",
                "Supply chain optimization",
                "Distribution planning"
            ]
        }
        
        if app_name in features:
            for feature in features[app_name]:
                st.write(f"• {feature}")

def show_inventory_function():
    """Show inventory optimization with same workflow as VRP"""
    st.title("📦 Inventory Optimization")
    st.write("Optimize inventory levels, ordering policies, and safety stock to minimize costs while maintaining service levels")
    
    # Get current tab from URL query parameters
    query_params = st.query_params
    current_tab = query_params.get("tab", "snapshots")  # Default to snapshots
    
    # Map tab names to indices
    tab_mapping = {
        "data_manager": 0,
        "snapshots": 1,
        "scenario_builder": 2,
        "view_results": 3,
        "compare_outputs": 4
    }
    
    # Set active tab based on URL or session state
    if current_tab in tab_mapping:
        st.session_state.active_inventory_tab = tab_mapping[current_tab]
    elif 'active_inventory_tab' not in st.session_state:
        st.session_state.active_inventory_tab = 1  # Default to Snapshots tab
    
    # Check for tab switching requests
    if 'switch_to_tab' in st.session_state:
        if st.session_state.switch_to_tab == 'scenario_builder':
            st.session_state.active_inventory_tab = 2
            st.query_params.tab = "scenario_builder"
        elif st.session_state.switch_to_tab == 'view_results':
            st.session_state.active_inventory_tab = 3
            st.query_params.tab = "view_results"
        del st.session_state.switch_to_tab
    
    # Create custom tab buttons
    tab_cols = st.columns(5)
    tab_names = ["📊 Data Manager", "📸 Snapshots", "🏗️ Scenario Builder", "📈 View Results", "⚖️ Compare Outputs"]
    tab_keys = ["data_manager", "snapshots", "scenario_builder", "view_results", "compare_outputs"]
    
    for i, (col, tab_name, tab_key) in enumerate(zip(tab_cols, tab_names, tab_keys)):
        with col:
            if st.session_state.active_inventory_tab == i:
                st.markdown(f"**🔹 {tab_name}**")
            else:
                if st.button(tab_name, key=f"inv_tab_{i}"):
                    st.session_state.active_inventory_tab = i
                    st.query_params.tab = tab_key
                    st.rerun()
    
    st.markdown("---")
    
    # Show content based on active tab
    if st.session_state.active_inventory_tab == 0:
        show_embedded_data_manager()  # Reuse the same data manager
    elif st.session_state.active_inventory_tab == 1:
        show_embedded_snapshots()  # Reuse the same snapshots
    elif st.session_state.active_inventory_tab == 2:
        show_embedded_scenario_builder()  # Reuse the same scenario builder
    elif st.session_state.active_inventory_tab == 3:
        show_embedded_view_results()  # Reuse the same view results
    elif st.session_state.active_inventory_tab == 4:
        show_embedded_compare_outputs()  # Reuse the same compare outputs

def show_inventory_optimization_streamlit():
    """Streamlit-only inventory optimization without Django backend"""
    st.title("📦 Inventory Optimization")
    st.write("Optimize inventory levels, ordering policies, and costs")
    
    # Create tabs for streamlit-only mode
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Data Input", "⚙️ Parameters", "🚀 Optimize", "📈 Results"])
    
    with tab1:
        st.header("📊 Data Input")
        
        # Sample data option
        if st.button("Load Sample Data"):
            sample_data = {
                'item_id': ['ITEM_001', 'ITEM_002', 'ITEM_003', 'ITEM_004', 'ITEM_005'],
                'annual_demand': [1200, 800, 1500, 600, 2000],
                'unit_cost': [25.0, 15.0, 40.0, 10.0, 30.0],
                'lead_time_days': [7, 5, 10, 3, 14],
                'category': ['A', 'B', 'A', 'C', 'A'],
                'supplier': ['SUP_001', 'SUP_002', 'SUP_001', 'SUP_003', 'SUP_002']
            }
            st.session_state.inventory_data = pd.DataFrame(sample_data)
            st.success("✅ Sample data loaded!")
        
        # File upload
        uploaded_file = st.file_uploader("Upload Inventory Data", type=['csv', 'xlsx'])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                st.session_state.inventory_data = df
                st.success("✅ Data uploaded successfully!")
            except Exception as e:
                st.error(f"Error loading file: {e}")
        
        # Display current data
        if 'inventory_data' in st.session_state:
            st.subheader("Current Data")
            st.dataframe(st.session_state.inventory_data, use_container_width=True)
            
            # Data validation
            required_cols = ['item_id', 'annual_demand', 'unit_cost', 'lead_time_days']
            missing_cols = [col for col in required_cols if col not in st.session_state.inventory_data.columns]
            if missing_cols:
                st.error(f"Missing required columns: {missing_cols}")
            else:
                st.success("✅ Data validation passed!")
    
    with tab2:
        st.header("⚙️ Optimization Parameters")
        
        col1, col2 = st.columns(2)
        with col1:
            holding_cost_rate = st.number_input("Holding Cost Rate (%)", min_value=0.1, max_value=50.0, value=20.0, step=0.1)
            ordering_cost = st.number_input("Ordering Cost per Order ($)", min_value=1.0, value=50.0, step=1.0)
            service_level = st.slider("Service Level (%)", min_value=80, max_value=99, value=95)
        
        with col2:
            max_inventory_budget = st.number_input("Max Inventory Budget ($)", min_value=0, value=100000, step=1000)
            demand_variability = st.selectbox("Demand Variability", ["Low", "Medium", "High"])
            optimization_objective = st.selectbox("Optimization Objective", 
                                                ["Minimize Total Cost", "Maximize Service Level", "Balance Cost & Service"])
        
        # Store parameters in session state
        st.session_state.inventory_params = {
            'holding_cost_rate': holding_cost_rate / 100,
            'ordering_cost': ordering_cost,
            'service_level': service_level / 100,
            'max_inventory_budget': max_inventory_budget,
            'demand_variability': demand_variability,
            'optimization_objective': optimization_objective
        }
    
    with tab3:
        st.header("🚀 Run Optimization")
        
        if 'inventory_data' not in st.session_state:
            st.warning("Please load data first in the Data Input tab")
        else:
            if st.button("🚀 Optimize Inventory", type="primary"):
                with st.spinner("Running inventory optimization..."):
                    try:
                        # Run the optimization
                        results = run_inventory_optimization_streamlit(
                            st.session_state.inventory_data, 
                            st.session_state.get('inventory_params', {})
                        )
                        st.session_state.inventory_results = results
                        st.success("✅ Optimization completed successfully!")
                        
                        # Show quick summary
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Annual Cost", f"${results['total_cost']:,.2f}")
                        with col2:
                            st.metric("Items Optimized", results['num_items'])
                        with col3:
                            st.metric("Avg Service Level", f"{results['avg_service_level']:.1%}")
                        with col4:
                            st.metric("Total Inventory Value", f"${results['total_inventory_value']:,.2f}")
                            
                    except Exception as e:
                        st.error(f"Optimization failed: {e}")
                        st.exception(e)
    
    with tab4:
        st.header("📈 Optimization Results")
        
        if 'inventory_results' not in st.session_state:
            st.info("Run optimization first to see results")
        else:
            results = st.session_state.inventory_results
            
            # KPI Dashboard
            st.subheader("📊 Key Performance Indicators")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Annual Cost", f"${results['total_cost']:,.2f}")
            with col2:
                st.metric("Holding Cost", f"${results['total_holding_cost']:,.2f}")
            with col3:
                st.metric("Ordering Cost", f"${results['total_ordering_cost']:,.2f}")
            with col4:
                st.metric("Service Level", f"{results['avg_service_level']:.1%}")
            
            # Detailed results tabs
            result_tab1, result_tab2, result_tab3 = st.tabs(["📋 Inventory Policy", "📊 Cost Analysis", "📈 Visualizations"])
            
            with result_tab1:
                st.subheader("Optimal Inventory Policy")
                if 'items' in results:
                    policy_df = pd.DataFrame(results['items'])
                    st.dataframe(policy_df, use_container_width=True)
                    
                    # Download option
                    csv = policy_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Policy",
                        csv,
                        "inventory_policy.csv",
                        "text/csv"
                    )
            
            with result_tab2:
                st.subheader("Cost Breakdown Analysis")
                
                # Cost breakdown chart
                cost_data = {
                    'Cost Type': ['Holding Cost', 'Ordering Cost'],
                    'Amount': [results['total_holding_cost'], results['total_ordering_cost']]
                }
                cost_df = pd.DataFrame(cost_data)
                
                import plotly.express as px
                fig = px.pie(cost_df, values='Amount', names='Cost Type', title='Cost Breakdown')
                st.plotly_chart(fig, use_container_width=True)
            
            with result_tab3:
                st.subheader("Inventory Analysis Charts")
                
                if 'items' in results:
                    items_df = pd.DataFrame(results['items'])
                    
                    # EOQ vs Demand scatter plot
                    fig1 = px.scatter(items_df, x='annual_demand', y='eoq', 
                                     title='EOQ vs Annual Demand', 
                                     labels={'annual_demand': 'Annual Demand', 'eoq': 'Economic Order Quantity'})
                    st.plotly_chart(fig1, use_container_width=True)
                    
                    # ABC Analysis
                    if 'category' in items_df.columns:
                        category_counts = items_df['category'].value_counts()
                        fig2 = px.bar(x=category_counts.index, y=category_counts.values,
                                     title='ABC Category Distribution',
                                     labels={'x': 'Category', 'y': 'Number of Items'})
                        st.plotly_chart(fig2, use_container_width=True)

def run_inventory_optimization_streamlit(data, params):
    """Run inventory optimization without Django backend"""
    import numpy as np
    from scipy import stats
    
    # Default parameters
    holding_rate = params.get('holding_cost_rate', 0.20)
    ordering_cost = params.get('ordering_cost', 50.0)
    service_level = params.get('service_level', 0.95)
    
    results = {
        'items': [],
        'total_cost': 0,
        'total_holding_cost': 0,
        'total_ordering_cost': 0,
        'total_inventory_value': 0,
        'num_items': len(data),
        'avg_service_level': service_level
    }
    
    for _, item in data.iterrows():
        # Basic EOQ calculation
        annual_demand = item['annual_demand']
        unit_cost = item['unit_cost']
        lead_time = item.get('lead_time_days', 7)
        
        # Economic Order Quantity
        eoq = np.sqrt((2 * annual_demand * ordering_cost) / (holding_rate * unit_cost))
        
        # Safety stock (simplified)
        demand_std = annual_demand * 0.2  # Assume 20% variability
        z_score = stats.norm.ppf(service_level)
        safety_stock = z_score * demand_std * np.sqrt(lead_time / 365)
        
        # Reorder point
        avg_daily_demand = annual_demand / 365
        reorder_point = (avg_daily_demand * lead_time) + safety_stock
        
        # Costs
        holding_cost = (eoq / 2 + safety_stock) * unit_cost * holding_rate
        order_cost = (annual_demand / eoq) * ordering_cost
        total_item_cost = holding_cost + order_cost
        
        # Inventory value
        avg_inventory = eoq / 2 + safety_stock
        inventory_value = avg_inventory * unit_cost
        
        item_result = {
            'item_id': item['item_id'],
            'annual_demand': annual_demand,
            'unit_cost': unit_cost,
            'eoq': round(eoq, 2),
            'safety_stock': round(safety_stock, 2),
            'reorder_point': round(reorder_point, 2),
            'holding_cost': round(holding_cost, 2),
            'ordering_cost': round(order_cost, 2),
            'total_cost': round(total_item_cost, 2),
            'inventory_value': round(inventory_value, 2),
            'category': item.get('category', 'A')
        }
        
        results['items'].append(item_result)
        results['total_cost'] += total_item_cost
        results['total_holding_cost'] += holding_cost
        results['total_ordering_cost'] += order_cost
        results['total_inventory_value'] += inventory_value
    
    return results

if __name__ == "__main__":
    main() 