# frontend/pages/constraint_manager.py

import streamlit as st
import json
import pandas as pd
from typing import Dict, List, Optional
import sys
import os

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
sys.path.insert(0, project_root)

try:
    from backend.applications.vehicle_routing.constraint_patterns import VRPConstraintMatcher, ConstraintConverter
    from backend.applications.vehicle_routing.llm_parser import LLMConstraintParser, ConstraintValidator
    BACKEND_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Backend import error: {e}")
    BACKEND_AVAILABLE = False


class ConstraintManager:
    def __init__(self):
        if BACKEND_AVAILABLE:
            self.matcher = VRPConstraintMatcher()
            self.converter = ConstraintConverter()
            self.llm_parser = LLMConstraintParser()
        
        # Initialize session state
        if 'constraints' not in st.session_state:
            st.session_state.constraints = []
        if 'problem_context' not in st.session_state:
            st.session_state.problem_context = {}


def main():
    if not BACKEND_AVAILABLE:
        st.error("❌ Backend components not available. Please check your installation.")
        return
        
    st.title("🚛 VRP Constraint Manager")
    st.write("Add constraints using natural language prompts with intelligent parsing")

    manager = ConstraintManager()

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Add Constraints", "Review Constraints", "Export Constraints"])

    with tab1:
        add_constraint_interface(manager)

    with tab2:
        review_constraints_interface()

    with tab3:
        export_constraints_interface()


def add_constraint_interface(manager: ConstraintManager):
    """Interface for adding new constraints with improved confidence logic"""

    st.subheader("✍️ Add New Constraint")

    # Examples section
    with st.expander("💡 Example Prompts", expanded=False):
        st.write("**Capacity Constraints:**")
        st.write("• Each vehicle can carry maximum 500kg")
        st.write("• At max 30 capacity should be used")
        st.write("• Vehicle capacity should not exceed 100 units")
        
        st.write("**Vehicle Count Constraints:**")
        st.write("• Minimum 2 vehicles should be used")
        st.write("• Need at least 3 vehicles")
        st.write("• Use at most 5 vehicles")
        st.write("• mimimum 2 vehicles should be used (handles typos)")
        
        st.write("**Time Constraints:**")
        st.write("• Deliver to customer A before 2 PM")
        st.write("• Customer B must be visited between 9:00 AM and 5:00 PM")
        
        st.write("**Distance Constraints:**")
        st.write("• Total route distance should not exceed 200 km")
        st.write("• Driver should not work more than 8 hours")
        
        st.write("**Vehicle Restrictions:**")
        st.write("• Vehicle 1 cannot visit location X")
        st.write("• Only vehicle A can visit customer C")
        
        st.write("**Priority Constraints:**")
        st.write("• Customer A has high priority")
        st.write("• Visit customer B first")

    # Processing settings
    st.subheader("🔧 Processing Settings")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        confidence_threshold = st.slider(
            "Pattern Matching Confidence Threshold",
            min_value=0.1,
            max_value=1.0,
            value=0.85,  # High confidence required
            step=0.05,
            help="Only use pattern matching if confidence is above this threshold"
        )
    
    with col2:
        use_llm_fallback = st.checkbox(
            "Use AI Fallback", 
            value=True,
            help="Use LLM when pattern matching confidence is low"
        )
    
    with col3:
        auto_validate = st.checkbox(
            "Auto-validate", 
            value=True, 
            help="Automatically validate constraints"
        )

    # OpenAI API configuration
    with st.expander("🤖 AI Configuration", expanded=False):
        api_key_source = st.radio(
            "API Key Source:",
            ["Environment Variable", "Streamlit Secrets", "Manual Input"]
        )
        
        if api_key_source == "Manual Input":
            api_key = st.text_input(
                "OpenAI API Key:",
                type="password",
                help="Enter your OpenAI API key for LLM parsing"
            )
            if api_key:
                os.environ['OPENAI_API_KEY'] = api_key
        
        # Show current API key status
        current_key = get_openai_api_key()
        if current_key:
            st.success("✅ OpenAI API key is configured")
        else:
            st.warning("⚠️ OpenAI API key not found")
            st.info("💡 **Setup Instructions:**")
            st.code("""
# Option 1: Environment Variable
set OPENAI_API_KEY=your_api_key_here

# Option 2: Streamlit Secrets (.streamlit/secrets.toml)
[secrets]
OPENAI_API_KEY = "your_api_key_here"

# Option 3: Use manual input above
""")

    st.markdown("---")

    # Constraint input
    constraint_prompt = st.text_area(
        "Enter your constraint in natural language:",
        placeholder="e.g., At max 30 capacity should be used",
        height=100
    )

    # Process constraint button
    if st.button("🔍 Process Constraint", type="primary"):
        if constraint_prompt.strip():
            process_constraint_with_confidence(
                manager, 
                constraint_prompt, 
                confidence_threshold,
                use_llm_fallback, 
                auto_validate
            )
        else:
            st.error("Please enter a constraint prompt")


def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from various sources"""
    try:
        # Try Streamlit secrets first - both formats
        if hasattr(st, 'secrets'):
            # Try the nested format first
            if 'openai' in st.secrets and 'api_key' in st.secrets['openai']:
                return st.secrets['openai']['api_key']
            # Try the direct format
            elif 'OPENAI_API_KEY' in st.secrets:
                return st.secrets['OPENAI_API_KEY']
    except:
        pass
    
    # Try environment variable
    return os.environ.get('OPENAI_API_KEY')


def calculate_pattern_confidence(pattern_result, prompt: str) -> float:
    """Calculate confidence score for pattern matching"""
    if not pattern_result:
        return 0.0
    
    constraint_type, match_info = pattern_result
    
    # Base confidence
    confidence = 0.6
    
    # Boost confidence for exact parameter matches
    params = match_info.get('parameters', {})
    
    # Check for numeric values (higher confidence)
    for key, value in params.items():
        if value and str(value).replace('.', '').isdigit():
            confidence += 0.15
    
    # Check for specific keywords that increase confidence
    high_confidence_words = [
        'maximum', 'minimum', 'exceed', 'capacity', 
        'vehicle', 'before', 'after', 'between'
    ]
    
    words_found = sum(1 for word in high_confidence_words if word in prompt.lower())
    confidence += min(0.2, words_found * 0.05)
    
    # Penalty for ambiguous patterns
    if len(prompt.split()) > 15:  # Very long prompts might be ambiguous
        confidence -= 0.1
    
    # Check for typos but still give decent confidence for known patterns
    if 'mimimum' in prompt.lower():  # Known typo we handle
        confidence = max(confidence, 0.8)
    
    return min(1.0, max(0.0, confidence))


def process_constraint_with_confidence(
    manager: ConstraintManager, 
    prompt: str, 
    confidence_threshold: float,
    use_llm_fallback: bool, 
    auto_validate: bool
):
    """Process constraint with confidence-based routing"""

    with st.spinner("🔍 Processing constraint..."):
        
        # Step 1: Try pattern matching first
        pattern_result = manager.matcher.match_constraint(prompt)
        
        if pattern_result:
            # Calculate confidence
            confidence = calculate_pattern_confidence(pattern_result, prompt)
            
            st.info(f"📊 Pattern matching confidence: {confidence:.1%}")
            
            if confidence >= confidence_threshold:
                # High confidence - use pattern matching
                constraint_type, match_info = pattern_result
                st.success(f"✅ High confidence pattern match: {constraint_type}")

                # Convert using pattern-based converter
                converter_func = getattr(manager.converter, match_info['conversion_function'])
                mathematical_constraint = converter_func(
                    match_info['parameters'],
                    st.session_state.problem_context
                )

                parsed_constraint = {
                    'original_prompt': prompt,
                    'constraint_type': constraint_type,
                    'parameters': match_info['parameters'],
                    'mathematical_format': mathematical_constraint,
                    'parsing_method': 'pattern_matching',
                    'confidence': confidence
                }
                
            else:
                # Low confidence - fall back to LLM if enabled
                if use_llm_fallback:
                    st.warning(f"⚠️ Low confidence ({confidence:.1%}) - using AI fallback")
                    parsed_constraint = use_llm_parsing(manager, prompt)
                else:
                    st.error(f"❌ Low confidence ({confidence:.1%}) and AI fallback disabled")
                    return
        
        elif use_llm_fallback:
            # No pattern match - use LLM
            st.info("🤖 No pattern match found - using AI parsing")
            parsed_constraint = use_llm_parsing(manager, prompt)
        
        else:
            st.error("❌ No pattern match found and AI parsing disabled")
            return

        if not parsed_constraint:
            return

        # Step 2: Validate if requested
        if auto_validate:
            validate_constraint(parsed_constraint)

        # Step 3: Display parsed constraint
        display_parsed_constraint(parsed_constraint)

        # Step 4: Add to session state if user confirms
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("✅ Add Constraint"):
                st.session_state.constraints.append(parsed_constraint)
                st.success("Constraint added successfully!")
                st.rerun()

        with col2:
            if st.button("❌ Discard"):
                st.info("Constraint discarded")

        with col3:
            if st.button("✏️ Edit Manually"):
                edit_constraint_manually(parsed_constraint)


def use_llm_parsing(manager: ConstraintManager, prompt: str) -> Optional[Dict]:
    """Use LLM for constraint parsing"""
    
    api_key = get_openai_api_key()
    if not api_key:
        st.error("❌ OpenAI API key not configured. Please set up API key in the configuration section above.")
        return None
    
    try:
        llm_result = manager.llm_parser.parse_constraint(
            prompt,
            st.session_state.problem_context
        )

        if llm_result:
            llm_result['original_prompt'] = prompt
            st.success(f"✅ AI parsed: {llm_result.get('constraint_type', 'unknown')}")
            return llm_result
        else:
            st.error("❌ AI could not parse constraint")
            return None
            
    except Exception as e:
        st.error(f"❌ AI parsing failed: {str(e)}")
        return None


def validate_constraint(parsed_constraint: Dict):
    """Validate the parsed constraint"""
    try:
        validator = ConstraintValidator(st.session_state.problem_context)
        validation_result = validator.validate_constraint(parsed_constraint)
        parsed_constraint['validation'] = validation_result

        if not validation_result['is_valid']:
            st.error("❌ Constraint validation failed:")
            for error in validation_result['errors']:
                st.error(f"• {error}")
        elif validation_result['warnings']:
            st.warning("⚠️ Validation warnings:")
            for warning in validation_result['warnings']:
                st.warning(f"• {warning}")
        else:
            st.success("✅ Constraint validated successfully")
    except Exception as e:
        st.warning(f"⚠️ Validation error: {e}")


def display_parsed_constraint(constraint: Dict):
    """Display the parsed constraint in a nice format"""

    st.subheader("📋 Parsed Constraint")

    # Basic info
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Type", constraint.get('constraint_type', 'Unknown'))

    with col2:
        confidence = constraint.get('confidence', 0)
        confidence_color = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.5 else "🔴"
        st.metric("Confidence", f"{confidence:.0%} {confidence_color}")

    with col3:
        method = constraint.get('parsing_method', 'Unknown')
        method_icon = "🎯" if method == 'pattern_matching' else "🤖"
        st.metric("Method", f"{method_icon} {method.replace('_', ' ').title()}")

    # Mathematical representation
    if 'mathematical_format' in constraint:
        math_format = constraint['mathematical_format']
        if isinstance(math_format, dict):
            st.write("**Mathematical Form:**")
            st.code(math_format.get('mathematical_form', 'Not available'))

            st.write("**Description:**")
            st.info(math_format.get('description', 'No description available'))

    # Parameters
    if 'parameters' in constraint:
        st.write("**Parameters:**")
        st.json(constraint['parameters'])

    # Validation results
    if 'validation' in constraint:
        validation = constraint['validation']
        if validation.get('errors'):
            st.error("**Validation Errors:**")
            for error in validation['errors']:
                st.write(f"• {error}")

        if validation.get('warnings'):
            st.warning("**Validation Warnings:**")
            for warning in validation['warnings']:
                st.write(f"• {warning}")


def edit_constraint_manually(constraint: Dict):
    """Allow manual editing of constraint parameters"""

    st.subheader("✏️ Edit Constraint Manually")

    # Edit constraint type
    constraint_types = [
        'capacity', 'time_window', 'distance', 'working_hours', 
        'vehicle_restriction', 'priority', 'vehicle_count', 'custom'
    ]

    edited_type = st.selectbox(
        "Constraint Type:",
        constraint_types,
        index=constraint_types.index(constraint.get('constraint_type', 'custom'))
    )

    # Edit parameters as JSON
    current_params = json.dumps(constraint.get('parameters', {}), indent=2)
    edited_params = st.text_area(
        "Parameters (JSON format):",
        value=current_params,
        height=150
    )

    try:
        parsed_params = json.loads(edited_params)

        if st.button("💾 Save Edited Constraint"):
            constraint['constraint_type'] = edited_type
            constraint['parameters'] = parsed_params
            constraint['manually_edited'] = True

            st.session_state.constraints.append(constraint)
            st.success("Edited constraint saved!")
            st.rerun()

    except json.JSONDecodeError:
        st.error("Invalid JSON format in parameters")


def review_constraints_interface():
    """Interface for reviewing added constraints"""

    st.subheader("📝 Current Constraints")

    if not st.session_state.constraints:
        st.info("No constraints added yet. Go to the 'Add Constraints' tab to add some.")
        return

    # Display constraints in a table
    constraint_data = []
    for i, constraint in enumerate(st.session_state.constraints):
        confidence = constraint.get('confidence', 0)
        confidence_icon = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.5 else "🔴"
        
        constraint_data.append({
            'ID': i,
            'Type': constraint.get('constraint_type', 'Unknown'),
            'Original Prompt': constraint.get('original_prompt', '')[:50] + '...',
            'Method': constraint.get('parsing_method', 'Unknown'),
            'Confidence': f"{confidence:.0%} {confidence_icon}",
            'Valid': '✅' if constraint.get('validation', {}).get('is_valid', True) else '❌'
        })

    df = pd.DataFrame(constraint_data)

    # Display table with selection
    selected_rows = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row"
    )

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🗑️ Delete Selected"):
            if hasattr(selected_rows, 'selection') and selected_rows.selection.rows:
                indices_to_remove = sorted(selected_rows.selection.rows, reverse=True)
                for idx in indices_to_remove:
                    del st.session_state.constraints[idx]
                st.success(f"Deleted {len(indices_to_remove)} constraint(s)")
                st.rerun()

    with col2:
        if st.button("🔄 Revalidate All"):
            revalidate_all_constraints()

    with col3:
        if st.button("🧹 Clear All"):
            st.session_state.constraints = []
            st.success("All constraints cleared")
            st.rerun()

    # Detailed view of selected constraint
    if hasattr(selected_rows, 'selection') and selected_rows.selection.rows:
        if len(selected_rows.selection.rows) == 1:
            selected_idx = selected_rows.selection.rows[0]
            st.subheader(f"📋 Constraint Details (ID: {selected_idx})")

            constraint = st.session_state.constraints[selected_idx]
            display_parsed_constraint(constraint)


def revalidate_all_constraints():
    """Revalidate all constraints with current problem context"""

    validator = ConstraintValidator(st.session_state.problem_context)

    with st.spinner("Revalidating constraints..."):
        for constraint in st.session_state.constraints:
            validation_result = validator.validate_constraint(constraint)
            constraint['validation'] = validation_result

    st.success("All constraints revalidated")
    st.rerun()


def export_constraints_interface():
    """Interface for exporting constraints"""

    st.subheader("📤 Export Constraints")

    if not st.session_state.constraints:
        st.info("No constraints to export")
        return

    # Export format selection
    export_format = st.selectbox(
        "Export Format:",
        ["JSON", "Python Code", "Mathematical Model", "CSV"]
    )

    if export_format == "JSON":
        export_json()
    elif export_format == "Python Code":
        export_python_code()
    elif export_format == "Mathematical Model":
        export_mathematical_model()
    elif export_format == "CSV":
        export_csv()


def export_json():
    """Export constraints as JSON"""
    constraints_json = json.dumps(st.session_state.constraints, indent=2)

    st.code(constraints_json, language="json")

    st.download_button(
        label="📥 Download JSON",
        data=constraints_json,
        file_name="vrp_constraints.json",
        mime="application/json"
    )


def export_python_code():
    """Export constraints as Python code"""
    st.info("Python code export coming soon!")


def export_mathematical_model():
    """Export constraints as mathematical model"""
    st.info("Mathematical model export coming soon!")


def export_csv():
    """Export constraints as CSV"""
    constraint_data = []

    for i, constraint in enumerate(st.session_state.constraints):
        constraint_data.append({
            'ID': i,
            'Original_Prompt': constraint.get('original_prompt', ''),
            'Constraint_Type': constraint.get('constraint_type', ''),
            'Parsing_Method': constraint.get('parsing_method', ''),
            'Confidence': constraint.get('confidence', 0),
            'Is_Valid': constraint.get('validation', {}).get('is_valid', True),
            'Parameters': json.dumps(constraint.get('parameters', {}))
        })

    df = pd.DataFrame(constraint_data)
    csv = df.to_csv(index=False)

    st.dataframe(df)

    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="vrp_constraints.csv",
        mime="text/csv"
    )


if __name__ == "__main__":
    main()