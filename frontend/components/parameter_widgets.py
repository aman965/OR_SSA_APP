"""
Dynamic Parameter Widgets

This module provides functions to dynamically render parameter input widgets
based on model configuration. It supports various parameter types and layouts.
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Union
import json


class ParameterWidgetGenerator:
    """
    Class for generating parameter widgets dynamically based on configuration.
    """
    
    def __init__(self):
        """Initialize the parameter widget generator."""
        self.widget_cache = {}
    
    def create_parameter_widget(self, param_name: str, param_config: Dict) -> Dict[str, Any]:
        """
        Create a parameter widget configuration.
        
        Args:
            param_name: Name of the parameter
            param_config: Parameter configuration dictionary
            
        Returns:
            Widget configuration dictionary
        """
        param_type = param_config.get('type', 'string')
        label = param_config.get('label', param_name.title())
        help_text = param_config.get('help', '')
        default = param_config.get('default')
        required = param_config.get('required', False)
        
        widget_config = {
            'name': param_name,
            'type': param_type,
            'label': label,
            'help': help_text,
            'default': default,
            'required': required,
            'config': param_config
        }
        
        return widget_config
    
    def get_default_values(self, parameters_config: Dict) -> Dict[str, Any]:
        """
        Get default values for all parameters.
        
        Args:
            parameters_config: Dictionary of parameter configurations
            
        Returns:
            Dictionary of default parameter values
        """
        default_values = {}
        
        for param_name, param_config in parameters_config.items():
            default = param_config.get('default')
            if default is not None:
                default_values[param_name] = default
            else:
                param_type = param_config.get('type', 'string')
                if param_type == 'float':
                    default_values[param_name] = 0.0
                elif param_type == 'integer':
                    default_values[param_name] = 0
                elif param_type == 'boolean':
                    default_values[param_name] = False
                elif param_type == 'select':
                    options = param_config.get('options', [])
                    default_values[param_name] = options[0] if options else ""
                else:
                    default_values[param_name] = ""
        
        return default_values
    
    def validate_parameter_values(self, parameter_values: Dict[str, Any], parameters_config: Dict) -> Dict[str, Any]:
        """
        Validate parameter values against their configuration.
        
        Args:
            parameter_values: Dictionary of parameter values
            parameters_config: Dictionary of parameter configurations
            
        Returns:
            Validation results dictionary
        """
        return validate_parameters(parameter_values, parameters_config)


def render_parameter_widget(param_name: str, param_config: Dict, key_prefix: str = "") -> Any:
    """
    Dynamically render parameter input widget based on configuration.
    
    Args:
        param_name: Name of the parameter
        param_config: Parameter configuration dictionary
        key_prefix: Prefix for widget keys to avoid conflicts
        
    Returns:
        Parameter value from the widget
    """
    param_type = param_config.get('type', 'string')
    label = param_config.get('label', param_name.title())
    help_text = param_config.get('help', '')
    default = param_config.get('default')
    required = param_config.get('required', False)
    
    # Create unique key for the widget
    widget_key = f"{key_prefix}param_{param_name}" if key_prefix else f"param_{param_name}"
    
    # Add required indicator to label
    if required:
        label = f"{label} *"
    
    try:
        if param_type == 'float':
            return st.number_input(
                label,
                min_value=param_config.get('min', 0.0),
                max_value=param_config.get('max', float('inf')),
                value=float(default) if default is not None else 0.0,
                step=param_config.get('step', 0.1),
                help=help_text,
                key=widget_key,
                format=param_config.get('format', '%.2f')
            )
            
        elif param_type == 'integer':
            return st.number_input(
                label,
                min_value=param_config.get('min', 0),
                max_value=param_config.get('max', 1000000),
                value=int(default) if default is not None else 0,
                step=param_config.get('step', 1),
                help=help_text,
                key=widget_key
            )
            
        elif param_type == 'boolean':
            return st.checkbox(
                label,
                value=bool(default) if default is not None else False,
                help=help_text,
                key=widget_key
            )
            
        elif param_type == 'select':
            options = param_config.get('options', [])
            default_index = param_config.get('default_index', 0)
            
            if not options:
                st.error(f"No options provided for select parameter: {param_name}")
                return None
                
            return st.selectbox(
                label,
                options=options,
                index=min(default_index, len(options) - 1),
                help=help_text,
                key=widget_key
            )
            
        elif param_type == 'multiselect':
            options = param_config.get('options', [])
            default_values = param_config.get('default', [])
            
            return st.multiselect(
                label,
                options=options,
                default=default_values,
                help=help_text,
                key=widget_key
            )
            
        elif param_type == 'slider':
            min_val = param_config.get('min', 0)
            max_val = param_config.get('max', 100)
            default_val = default if default is not None else min_val
            step = param_config.get('step', 1)
            
            return st.slider(
                label,
                min_value=min_val,
                max_value=max_val,
                value=default_val,
                step=step,
                help=help_text,
                key=widget_key
            )
            
        elif param_type == 'text':
            max_chars = param_config.get('max_chars', None)
            return st.text_input(
                label,
                value=str(default) if default is not None else "",
                max_chars=max_chars,
                help=help_text,
                key=widget_key
            )
            
        elif param_type == 'textarea':
            height = param_config.get('height', 100)
            max_chars = param_config.get('max_chars', None)
            return st.text_area(
                label,
                value=str(default) if default is not None else "",
                height=height,
                max_chars=max_chars,
                help=help_text,
                key=widget_key
            )
            
        elif param_type == 'date':
            from datetime import date, datetime
            
            if default:
                if isinstance(default, str):
                    default_date = datetime.strptime(default, '%Y-%m-%d').date()
                else:
                    default_date = default
            else:
                default_date = date.today()
                
            return st.date_input(
                label,
                value=default_date,
                help=help_text,
                key=widget_key
            )
            
        elif param_type == 'time':
            from datetime import time, datetime
            
            if default:
                if isinstance(default, str):
                    default_time = datetime.strptime(default, '%H:%M').time()
                else:
                    default_time = default
            else:
                default_time = time(9, 0)  # 9:00 AM
                
            return st.time_input(
                label,
                value=default_time,
                help=help_text,
                key=widget_key
            )
            
        elif param_type == 'color':
            default_color = default if default else "#FF0000"
            return st.color_picker(
                label,
                value=default_color,
                help=help_text,
                key=widget_key
            )
            
        else:
            # Default to text input for unknown types
            st.warning(f"Unknown parameter type '{param_type}' for {param_name}. Using text input.")
            return st.text_input(
                label,
                value=str(default) if default is not None else "",
                help=help_text,
                key=widget_key
            )
            
    except Exception as e:
        st.error(f"Error rendering parameter widget for '{param_name}': {str(e)}")
        return default


def render_parameter_section(parameters_config: Dict, key_prefix: str = "", layout: str = "columns") -> Dict[str, Any]:
    """
    Render a complete parameter section with multiple parameters.
    
    Args:
        parameters_config: Dictionary of parameter configurations
        key_prefix: Prefix for widget keys
        layout: Layout style ('columns', 'rows', 'tabs')
        
    Returns:
        Dictionary of parameter values
    """
    if not parameters_config:
        st.info("No parameters to configure for this model.")
        return {}
    
    parameter_values = {}
    param_items = list(parameters_config.items())
    
    if layout == "columns" and len(param_items) > 1:
        # Organize parameters in columns
        num_columns = min(3, len(param_items))
        cols = st.columns(num_columns)
        
        for i, (param_name, param_config) in enumerate(param_items):
            with cols[i % num_columns]:
                parameter_values[param_name] = render_parameter_widget(
                    param_name, param_config, key_prefix
                )
                
    elif layout == "tabs" and len(param_items) > 6:
        # Use tabs for many parameters
        required_params = {k: v for k, v in param_items if v.get('required', False)}
        optional_params = {k: v for k, v in param_items if not v.get('required', False)}
        
        if required_params and optional_params:
            tab1, tab2 = st.tabs(["Required Parameters", "Optional Parameters"])
            
            with tab1:
                for param_name, param_config in required_params.items():
                    parameter_values[param_name] = render_parameter_widget(
                        param_name, param_config, key_prefix
                    )
            
            with tab2:
                for param_name, param_config in optional_params.items():
                    parameter_values[param_name] = render_parameter_widget(
                        param_name, param_config, key_prefix
                    )
        else:
            # All parameters in one tab
            for param_name, param_config in param_items:
                parameter_values[param_name] = render_parameter_widget(
                    param_name, param_config, key_prefix
                )
    else:
        # Default rows layout
        for param_name, param_config in param_items:
            parameter_values[param_name] = render_parameter_widget(
                param_name, param_config, key_prefix
            )
    
    return parameter_values


def validate_parameters(parameter_values: Dict[str, Any], parameters_config: Dict) -> Dict[str, Any]:
    """
    Validate parameter values against their configuration.
    
    Args:
        parameter_values: Dictionary of parameter values
        parameters_config: Dictionary of parameter configurations
        
    Returns:
        Validation results dictionary
    """
    errors = []
    warnings = []
    
    for param_name, param_config in parameters_config.items():
        value = parameter_values.get(param_name)
        required = param_config.get('required', False)
        param_type = param_config.get('type', 'string')
        
        # Check required parameters
        if required and (value is None or value == ""):
            errors.append(f"Parameter '{param_config.get('label', param_name)}' is required")
            continue
        
        if value is None or value == "":
            continue  # Skip validation for empty optional parameters
        
        # Type-specific validation
        if param_type in ['float', 'integer']:
            min_val = param_config.get('min')
            max_val = param_config.get('max')
            
            if min_val is not None and value < min_val:
                errors.append(f"Parameter '{param_config.get('label', param_name)}' must be >= {min_val}")
            
            if max_val is not None and value > max_val:
                errors.append(f"Parameter '{param_config.get('label', param_name)}' must be <= {max_val}")
        
        elif param_type == 'select':
            options = param_config.get('options', [])
            if value not in options:
                errors.append(f"Parameter '{param_config.get('label', param_name)}' must be one of: {options}")
        
        elif param_type == 'text':
            max_chars = param_config.get('max_chars')
            if max_chars and len(str(value)) > max_chars:
                errors.append(f"Parameter '{param_config.get('label', param_name)}' exceeds maximum length of {max_chars}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def show_parameter_help(parameters_config: Dict):
    """
    Show help information for parameters.
    
    Args:
        parameters_config: Dictionary of parameter configurations
    """
    with st.expander("📖 Parameter Help", expanded=False):
        for param_name, param_config in parameters_config.items():
            label = param_config.get('label', param_name.title())
            help_text = param_config.get('help', 'No description available')
            param_type = param_config.get('type', 'string')
            required = param_config.get('required', False)
            
            st.markdown(f"**{label}** {'*(required)*' if required else '*(optional)*'}")
            st.markdown(f"- Type: `{param_type}`")
            st.markdown(f"- Description: {help_text}")
            
            # Show constraints
            constraints = []
            if param_type in ['float', 'integer']:
                min_val = param_config.get('min')
                max_val = param_config.get('max')
                if min_val is not None:
                    constraints.append(f"min: {min_val}")
                if max_val is not None:
                    constraints.append(f"max: {max_val}")
            elif param_type == 'select':
                options = param_config.get('options', [])
                constraints.append(f"options: {', '.join(map(str, options))}")
            
            if constraints:
                st.markdown(f"- Constraints: {', '.join(constraints)}")
            
            st.markdown("---")


def export_parameters(parameter_values: Dict[str, Any], filename: str = "parameters.json"):
    """
    Export parameter values to a downloadable file.
    
    Args:
        parameter_values: Dictionary of parameter values
        filename: Name of the export file
    """
    if parameter_values:
        json_str = json.dumps(parameter_values, indent=2, default=str)
        st.download_button(
            label="📥 Export Parameters",
            data=json_str,
            file_name=filename,
            mime="application/json",
            help="Download current parameter values as JSON file"
        )


def import_parameters(parameters_config: Dict, key_prefix: str = "") -> Optional[Dict[str, Any]]:
    """
    Import parameter values from an uploaded file.
    
    Args:
        parameters_config: Dictionary of parameter configurations for validation
        key_prefix: Prefix for widget keys
        
    Returns:
        Imported parameter values or None
    """
    uploaded_file = st.file_uploader(
        "📤 Import Parameters",
        type=['json'],
        help="Upload a JSON file with parameter values",
        key=f"{key_prefix}import_params"
    )
    
    if uploaded_file is not None:
        try:
            imported_params = json.load(uploaded_file)
            
            # Validate imported parameters
            validation = validate_parameters(imported_params, parameters_config)
            
            if validation['valid']:
                st.success("✅ Parameters imported successfully!")
                return imported_params
            else:
                st.error("❌ Imported parameters are invalid:")
                for error in validation['errors']:
                    st.error(f"- {error}")
                return None
                
        except json.JSONDecodeError:
            st.error("❌ Invalid JSON file")
            return None
        except Exception as e:
            st.error(f"❌ Error importing parameters: {str(e)}")
            return None
    
    return None 