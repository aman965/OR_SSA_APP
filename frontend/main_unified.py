# frontend/main_unified.py - Complete VRP SaaS Application with existing components

import streamlit as st

# Set page config FIRST - before any other Streamlit commands
st.set_page_config(
    page_title="OR SaaS Application",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

import sys
import os
import pandas as pd
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import your backend components
try:
    from backend.db_utils import initialize_database, vrp_db
    from backend.applications.vehicle_routing.vrp_solver import VRPSolverPuLP
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False
    st.warning("⚠️ Backend components not fully available. Some features may be limited.")


def main():
    # Initialize database on first run
    if BACKEND_AVAILABLE and 'db_initialized' not in st.session_state:
        with st.spinner("Initializing database..."):
            initialize_database()
        st.session_state.db_initialized = True

    # Sidebar navigation
    st.sidebar.title("🔧 OR SaaS Applications")
    st.sidebar.markdown("---")

    # Main application selection
    app_choice = st.sidebar.selectbox(
        "Choose Application:",
        [
            "🏠 Home",
            "🚛 Vehicle Routing Problem",  # Featured VRP app
            "📊 Use Existing Data Manager",  # Redirect to your existing system
            "📅 Scheduling", 
            "📦 Inventory Optimization",
            "🌐 Network Flow"
        ]
    )

    # Route to appropriate page
    if app_choice == "🏠 Home":
        show_home_page()
    elif app_choice == "📊 Use Existing Data Manager":
        show_data_manager_redirect()
    elif app_choice == "🚛 Vehicle Routing Problem":
        show_vrp_application()  # This has multiple tabs
    elif app_choice in ["📅 Scheduling", "📦 Inventory Optimization", "🌐 Network Flow"]:
        st.info(f"{app_choice} - Coming Soon!")
        st.write("These modules will be available in future updates.")


def show_home_page():
    """Enhanced home page with VRP integration"""
    st.title("🚀 Operations Research SaaS Platform")
    st.write("Welcome to your comprehensive OR solution platform with natural language constraint processing!")

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("VRP Problems", "3")
    with col2:
        st.metric("Applications", "6")
    with col3:
        st.metric("Solvers", "2")
    with col4:
        st.metric("Status", "🟢 Online")

    st.markdown("---")

    # Feature overview
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🚛 Vehicle Routing Problem")
        st.write("• Natural language constraints")
        st.write("• Confidence-based parsing")
        st.write("• OpenAI integration")
        st.write("• Multiple solver options")
        if st.button("🚛 Go to VRP Solver"):
            st.session_state.page = "Vehicle Routing Problem"
            st.rerun()

    with col2:
        st.markdown("### 📊 Data Management")
        st.write("• Comprehensive upload system")
        st.write("• Dataset tracking & metadata")
        st.write("• Django integration")
        st.write("• File management operations")
        
        st.info("Use the comprehensive **'data manager'** link in the left sidebar for full functionality")

    with col3:
        st.markdown("### 🔮 Coming Soon")
        st.write("• Scheduling optimization")
        st.write("• Inventory management")
        st.write("• Network flow problems")

    # Show existing components availability
    st.markdown("---")
    st.subheader("🔗 Available Components")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📊 Data & Management:**")
        st.write("• data manager - Full upload system")
        st.write("• scenario builder - Problem setup")
        st.write("• snapshots - Data versioning")
    
    with col2:
        st.markdown("**🚛 VRP & Constraints:**")
        st.write("• constraint manager - NL parsing")
        st.write("• VRP Problem Solver - Integrated")
        st.write("• confidence-based routing")
        
    with col3:
        st.markdown("**📈 Analysis & Results:**")
        st.write("• view results - Solution analysis")
        st.write("• compare outputs - Comparison")
        st.write("• Interactive visualizations")


def show_data_manager_redirect():
    """Redirect to existing data manager"""
    st.title("📊 Data Management")
    
    st.info("🔄 **Redirecting to Comprehensive Data Manager**")
    
    st.markdown("""
    Your **existing data manager** has full functionality:
    
    ✅ **Upload datasets** (CSV, XLSX)  
    ✅ **Track uploaded files** with metadata  
    ✅ **Django database integration**  
    ✅ **File management operations**  
    ✅ **Export and delete capabilities**  
    
    **To access your full data manager:**
    1. 🔗 Click **"data manager"** in the left sidebar
    2. Or navigate directly to: `localhost:8504/data_manager`
    """)
    
    # Show current URL and navigation options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Quick Navigation")
        st.markdown("""
        - **data manager** ← Use this for uploads
        - **constraint manager** ← For VRP constraints  
        - **scenario builder** ← For problem setup
        - **view results** ← For solution analysis
        """)
    
    with col2:
        st.markdown("### 📊 Current Datasets")
        try:
            # Try to show basic info about existing datasets
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            uploads_dir = os.path.join(BASE_DIR, '..', 'media', 'uploads')
            
            if os.path.exists(uploads_dir):
                files = [f for f in os.listdir(uploads_dir) if f.endswith(('.csv', '.xlsx'))]
                if files:
                    st.write("**Found uploaded files:**")
                    for file in files[:5]:  # Show first 5
                        st.write(f"• {file}")
                else:
                    st.write("No uploaded files found")
            else:
                st.write("Upload directory not found")
        except Exception as e:
            st.write("Unable to check uploads directory")


def show_vrp_application():
    """Complete VRP application with multiple tabs"""
    st.title("🚛 Vehicle Routing Problem Solver")
    st.write("Solve complex vehicle routing problems with natural language constraints")

    # Sub-navigation for VRP features
    vrp_tabs = st.tabs([
        "🚛 Problem Setup",
        "✍️ Constraint Manager", 
        "🔍 Solve & Results",
        "📊 Analysis",
        "💾 Saved Problems"
    ])

    with vrp_tabs[0]:
        show_vrp_problem_setup()

    with vrp_tabs[1]:
        show_vrp_constraint_manager()

    with vrp_tabs[2]:
        show_vrp_solver()

    with vrp_tabs[3]:
        show_vrp_analysis()

    with vrp_tabs[4]:
        show_saved_problems()


def show_vrp_problem_setup():
    """VRP problem data setup with integration to existing data manager"""
    st.subheader("📍 Problem Setup")

    # Problem configuration
    col1, col2 = st.columns(2)

    with col1:
        problem_name = st.text_input("Problem Name", value="My VRP Problem")
        num_vehicles = st.number_input("Number of Vehicles", min_value=1, value=3)
        depot_location = st.text_input("Depot Location", value="Main Warehouse")

    with col2:
        solver_type = st.selectbox("Solver", ["PuLP + CBC", "OR-Tools (Future)"])
        time_limit = st.number_input("Time Limit (seconds)", min_value=10, value=300)

    st.markdown("---")

    # Data input options
    st.subheader("📊 Problem Data")

    data_input_method = st.radio(
        "How would you like to input your data?",
        ["📁 Use Existing Datasets", "🆕 Upload New Data", "🎲 Generate Sample"]
    )

    if data_input_method == "📁 Use Existing Datasets":
        st.info("💡 **Use your existing data manager for the most comprehensive upload system!**")
        
        # Try to show existing datasets
        try:
            # Basic integration - show available files
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            uploads_dir = os.path.join(BASE_DIR, '..', 'media', 'uploads')
            
            if os.path.exists(uploads_dir):
                files = [f for f in os.listdir(uploads_dir) if f.endswith(('.csv', '.xlsx'))]
                if files:
                    selected_file = st.selectbox("Select Dataset:", files)
                    if st.button("🔄 Load Selected Dataset"):
                        file_path = os.path.join(uploads_dir, selected_file)
                        try:
                            if selected_file.endswith('.csv'):
                                df = pd.read_csv(file_path)
                            else:
                                df = pd.read_excel(file_path)
                            
                            st.success(f"✅ Loaded dataset: {selected_file}")
                            st.dataframe(df.head(), use_container_width=True)
                            
                            # Process for VRP
                            problem_data = process_uploaded_data(df, problem_name, num_vehicles)
                            st.session_state.current_problem_data = problem_data
                            st.success("✅ Problem data processed and ready for VRP!")
                            
                        except Exception as e:
                            st.error(f"Error loading file: {e}")
                else:
                    st.warning("No datasets found. Use the **'data manager'** to upload datasets first.")
            else:
                st.warning("Upload directory not found. Use the **'data manager'** to set up data storage.")
                
        except Exception as e:
            st.error(f"Could not access existing datasets: {e}")
        
        st.markdown("""
        **📌 For full dataset management:**  
        👈 Click **"data manager"** in the left sidebar
        """)

    elif data_input_method == "🆕 Upload New Data":
        st.info("💡 **For comprehensive upload features, use the 'data manager' in the left sidebar**")
        
        # Simple upload for quick testing
        uploaded_file = st.file_uploader(
            "Quick Upload (For testing only)",
            type=['csv', 'xlsx'],
            help="For full upload features, use the comprehensive 'data manager'"
        )

        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                st.success("✅ File uploaded successfully!")
                st.dataframe(df.head(), use_container_width=True)

                if st.button("🔄 Process Data for VRP"):
                    with st.spinner("Processing uploaded data..."):
                        problem_data = process_uploaded_data(df, problem_name, num_vehicles)
                        st.session_state.current_problem_data = problem_data
                    st.success("✅ Problem data processed and saved!")

            except Exception as e:
                st.error(f"Error processing file: {e}")

    elif data_input_method == "🎲 Generate Sample":
        if st.button("🎲 Generate Sample Problem"):
            sample_data = generate_sample_problem(problem_name, num_vehicles)
            st.session_state.current_problem_data = sample_data
            st.success("✅ Sample problem generated!")
            st.json(sample_data)


def show_vrp_constraint_manager():
    """Enhanced constraint manager using the confidence-based system"""
    if 'current_problem_data' not in st.session_state:
        st.warning("⚠️ Please set up a problem first in the 'Problem Setup' tab")
        st.info("💡 **Tip:** You can also use the existing **'constraint manager'** in the left sidebar for advanced features!")
        return

    st.subheader("✍️ Constraint Manager")
    st.write("Add constraints using natural language with intelligent parsing")
    
    # Import the constraint parsing components
    try:
        from backend.applications.vehicle_routing.constraint_patterns import VRPConstraintMatcher, ConstraintConverter
        from backend.applications.vehicle_routing.llm_parser import LLMConstraintParser
        
        matcher = VRPConstraintMatcher()
        converter = ConstraintConverter()
        llm_parser = LLMConstraintParser()
        
        # Initialize session state for constraints
        if 'constraints' not in st.session_state:
            st.session_state.constraints = []
            
        # Configuration
        col1, col2, col3 = st.columns(3)
        
        with col1:
            confidence_threshold = st.slider(
                "Confidence Threshold", 
                min_value=0.1, 
                max_value=1.0, 
                value=0.85, 
                step=0.05
            )
        
        with col2:
            use_llm = st.checkbox("Use AI Fallback", value=True)
            
        with col3:
            api_status = "✅ Available" if llm_parser.is_available() else "❌ Not Available"
            st.metric("LLM Status", api_status)
        
        # Examples
        with st.expander("💡 Example Constraints"):
            st.write("**Try these examples:**")
            examples = [
                "at max 30 capacity should be used",
                "mimimum 2 vehicles should be used",
                "each vehicle can carry maximum 500kg",
                "need at least 3 vehicles"
            ]
            
            for example in examples:
                if st.button(f"📝 {example}", key=f"example_{example}"):
                    st.session_state.test_constraint = example
        
        # Constraint input
        constraint_prompt = st.text_area(
            "Enter your constraint:",
            value=st.session_state.get('test_constraint', ''),
            height=100,
            placeholder="e.g., at max 30 capacity should be used"
        )
        
        if st.button("🔍 Process Constraint", type="primary"):
            if constraint_prompt.strip():
                process_constraint_ui(constraint_prompt, matcher, converter, llm_parser, confidence_threshold, use_llm)
        
        # Display existing constraints
        if st.session_state.constraints:
            st.subheader("📋 Added Constraints")
            for i, constraint in enumerate(st.session_state.constraints):
                with st.expander(f"Constraint {i+1}: {constraint.get('constraint_type', 'Unknown')}"):
                    st.write(f"**Original:** {constraint.get('original_prompt', 'N/A')}")
                    st.write(f"**Type:** {constraint.get('constraint_type', 'N/A')}")
                    st.write(f"**Method:** {constraint.get('parsing_method', 'N/A')}")
                    st.write(f"**Confidence:** {constraint.get('confidence', 0):.1%}")
        
        # Link to existing constraint manager
        st.markdown("---")
        st.info("💡 **For advanced constraint features, use the 'constraint manager' in the left sidebar**")
        
    except ImportError as e:
        st.error(f"Could not load constraint processing components: {e}")
        st.info("💡 **Try using the existing 'constraint manager' in the left sidebar**")


# Copy the rest of the functions from main_fixed.py
def process_constraint_ui(prompt, matcher, converter, llm_parser, confidence_threshold, use_llm):
    """Process constraint with UI feedback"""
    
    # Calculate confidence like in the demo
    def calculate_pattern_confidence(pattern_result, prompt: str) -> float:
        if not pattern_result:
            return 0.0
        
        constraint_type, match_info = pattern_result
        confidence = 0.6
        
        # Boost for numeric values
        params = match_info.get('parameters', {})
        for key, value in params.items():
            if value and str(value).replace('.', '').isdigit():
                confidence += 0.15
        
        # Boost for keywords
        high_confidence_words = ['maximum', 'minimum', 'exceed', 'capacity', 'vehicle']
        words_found = sum(1 for word in high_confidence_words if word in prompt.lower())
        confidence += min(0.2, words_found * 0.05)
        
        # Handle known typos
        if 'mimimum' in prompt.lower():
            confidence = max(confidence, 0.8)
        
        return min(1.0, max(0.0, confidence))
    
    with st.spinner("Processing constraint..."):
        # Try pattern matching
        pattern_result = matcher.match_constraint(prompt)
        
        if pattern_result:
            confidence = calculate_pattern_confidence(pattern_result, prompt)
            constraint_type, match_info = pattern_result
            
            st.info(f"📊 Pattern match found: **{constraint_type}** (Confidence: {confidence:.1%})")
            
            if confidence >= confidence_threshold:
                st.success("✅ HIGH CONFIDENCE - Using pattern matching")
                
                # Convert constraint
                converter_func = getattr(converter, match_info['conversion_function'])
                mathematical_constraint = converter_func(match_info['parameters'], {})
                
                parsed_constraint = {
                    'original_prompt': prompt,
                    'constraint_type': constraint_type,
                    'parameters': match_info['parameters'],
                    'mathematical_format': mathematical_constraint,
                    'parsing_method': 'pattern_matching',
                    'confidence': confidence
                }
                
            else:
                st.warning(f"⚠️ LOW CONFIDENCE ({confidence:.1%}) - Using LLM fallback")
                
                if use_llm and llm_parser.is_available():
                    llm_result = llm_parser.parse_constraint(prompt, {})
                    if llm_result:
                        parsed_constraint = llm_result
                        parsed_constraint['original_prompt'] = prompt
                        st.success("✅ LLM parsing successful")
                    else:
                        st.error("❌ LLM parsing failed")
                        return
                else:
                    st.warning("Using enhanced fallback...")
                    parsed_constraint = llm_parser._fallback_parse(prompt)
                    parsed_constraint['original_prompt'] = prompt
                    
        else:
            st.info("No pattern match - using LLM/fallback")
            if use_llm and llm_parser.is_available():
                llm_result = llm_parser.parse_constraint(prompt, {})
                if llm_result:
                    parsed_constraint = llm_result
                    parsed_constraint['original_prompt'] = prompt
                    st.success("✅ LLM parsing successful")
                else:
                    st.error("❌ LLM parsing failed")
                    return
            else:
                parsed_constraint = llm_parser._fallback_parse(prompt)
                parsed_constraint['original_prompt'] = prompt
        
        # Display result and add option
        st.json(parsed_constraint)
        
        if st.button("➕ Add This Constraint"):
            st.session_state.constraints.append(parsed_constraint)
            st.success("Constraint added successfully!")
            st.rerun()


def show_vrp_solver():
    """VRP solving interface"""
    if 'current_problem_data' not in st.session_state:
        st.warning("⚠️ Please set up a problem first in the 'Problem Setup' tab")
        return

    st.subheader("🔍 Solve VRP")

    # Show problem summary
    problem_data = st.session_state.current_problem_data
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Customers", len(problem_data.get('customers', [])) - 1)
    with col2:
        st.metric("Vehicles", problem_data.get('num_vehicles', 0))
    with col3:
        st.metric("Constraints", len(st.session_state.get('constraints', [])))

    # Solve button
    if st.button("🚀 Solve Vehicle Routing Problem", type="primary"):
        solve_vrp_ui(problem_data)


def solve_vrp_ui(problem_data):
    """Solve VRP with UI feedback"""
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        status_text.text("🔧 Initializing solver...")
        progress_bar.progress(20)

        if BACKEND_AVAILABLE:
            solver = VRPSolverPuLP(use_llm=False)
            solver.setup_problem(problem_data)
        else:
            st.error("Backend not available for solving")
            return

        status_text.text("✍️ Adding constraints...")
        progress_bar.progress(40)

        # Add constraints from session state
        constraints = st.session_state.get('constraints', [])
        for constraint in constraints:
            # Simple constraint addition - could be enhanced
            if constraint.get('constraint_type') == 'vehicle_capacity_max':
                solver.add_constraint_from_prompt(constraint['original_prompt'])

        status_text.text("🔍 Solving...")
        progress_bar.progress(70)

        solution = solver.solve(time_limit=60, verbose=False)
        progress_bar.progress(100)

        if solution['success']:
            status_text.text("✅ Solution found!")
            display_solution_ui(solution)
        else:
            status_text.text("❌ No solution found")
            st.error(f"Solving failed: {solution.get('error', 'Unknown error')}")

    except Exception as e:
        status_text.text("❌ Solving failed")
        st.error(f"Error: {e}")


def display_solution_ui(solution):
    """Display VRP solution"""
    st.subheader("🎉 Solution Found!")

    # Key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Distance", f"{solution['total_distance']:.2f}")
    with col2:
        st.metric("Vehicles Used", f"{solution['vehicles_used']}/{solution['total_vehicles']}")
    with col3:
        st.metric("Solve Time", f"{solution.get('solve_time', 0):.2f}s")

    # Routes
    st.subheader("📍 Vehicle Routes")
    for route in solution['routes']:
        if len(route['route']) > 2:
            with st.expander(f"🚛 Vehicle {route['vehicle_id']} - Distance: {route['distance']:.2f}"):
                route_sequence = ' → '.join([f"Location {loc}" for loc in route['route']])
                st.write(f"**Route:** {route_sequence}")
                
                if route.get('customers'):
                    customer_df = []
                    for customer in route['customers']:
                        customer_df.append({
                            'Customer': customer.get('name', customer.get('id', 'Unknown')),
                            'Demand': customer.get('demand', 0)
                        })
                    if customer_df:
                        st.dataframe(pd.DataFrame(customer_df), use_container_width=True)


def show_vrp_analysis():
    """VRP analysis section"""
    st.subheader("📊 Solution Analysis")
    st.info("Analysis features coming soon - route visualization, performance metrics, etc.")
    
    st.markdown("💡 **Also check out 'view results' in the left sidebar for existing result analysis!**")


def show_saved_problems():
    """Saved problems section"""
    st.subheader("💾 Saved Problems")
    st.info("Saved problems management coming soon")


def process_uploaded_data(df, problem_name, num_vehicles):
    """Process uploaded CSV/Excel data"""
    customers = []
    for _, row in df.iterrows():
        customer = {
            'id': str(row.get('customer_id', len(customers))),
            'name': str(row.get('name', f'Customer {len(customers)}')),
            'demand': float(row.get('demand', 1)) if pd.notna(row.get('demand')) else 1
        }
        customers.append(customer)

    # Simple distance matrix
    n = len(customers)
    distance_matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                distance_matrix[i][j] = abs(i - j) * 10  # Simple distance

    return {
        'name': problem_name,
        'num_vehicles': num_vehicles,
        'depot': 0,
        'customers': customers,
        'distance_matrix': distance_matrix
    }


def generate_sample_problem(problem_name, num_vehicles):
    """Generate a sample VRP problem"""
    import random

    customers = [{'id': '0', 'name': 'Depot', 'demand': 0}]
    for i in range(1, 6):
        customers.append({
            'id': str(i),
            'name': f'Customer {i}',
            'demand': random.randint(1, 10)
        })

    # Simple distance matrix
    n = len(customers)
    distance_matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                distance_matrix[i][j] = random.randint(10, 50)

    return {
        'name': problem_name,
        'num_vehicles': num_vehicles,
        'depot': 0,
        'customers': customers,
        'distance_matrix': distance_matrix
    }


if __name__ == "__main__":
    main() 