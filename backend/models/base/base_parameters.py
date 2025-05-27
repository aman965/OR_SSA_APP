"""
Base Parameters Class

This module provides base functionality for parameter handling and validation.
"""

from typing import Dict, List, Any, Optional
import json


class BaseParameters:
    """
    Base class for handling optimization model parameters.
    
    Provides common functionality for parameter validation, serialization, and management.
    """
    
    def __init__(self, parameter_schema: Dict = None):
        """
        Initialize the parameters handler.
        
        Args:
            parameter_schema: Dictionary defining parameter schema
        """
        self.parameter_schema = parameter_schema or {}
        self.parameters = {}
        self.validation_errors = []
        self.validation_warnings = []
        
    def set_parameter(self, name: str, value: Any) -> bool:
        """
        Set a single parameter value.
        
        Args:
            name: Parameter name
            value: Parameter value
            
        Returns:
            True if parameter was set successfully, False otherwise
        """
        if name not in self.parameter_schema:
            self.validation_warnings.append(f"Unknown parameter: {name}")
            
        self.parameters[name] = value
        return True
    
    def set_parameters(self, params: Dict[str, Any]) -> bool:
        """
        Set multiple parameter values.
        
        Args:
            params: Dictionary of parameter values
            
        Returns:
            True if all parameters were set successfully, False otherwise
        """
        success = True
        for name, value in params.items():
            if not self.set_parameter(name, value):
                success = False
        return success
    
    def get_parameter(self, name: str, default: Any = None) -> Any:
        """
        Get a parameter value.
        
        Args:
            name: Parameter name
            default: Default value if parameter not found
            
        Returns:
            Parameter value or default
        """
        return self.parameters.get(name, default)
    
    def get_all_parameters(self) -> Dict[str, Any]:
        """
        Get all parameter values.
        
        Returns:
            Dictionary of all parameters
        """
        return self.parameters.copy()
    
    def validate_parameters(self) -> Dict[str, Any]:
        """
        Validate all parameters against the schema.
        
        Returns:
            Validation results dictionary
        """
        errors = []
        warnings = []
        
        # Check required parameters
        for param_name, param_config in self.parameter_schema.items():
            if param_config.get('required', False):
                if param_name not in self.parameters:
                    errors.append(f"Required parameter '{param_name}' is missing")
                elif self.parameters[param_name] is None:
                    errors.append(f"Required parameter '{param_name}' cannot be None")
        
        # Validate parameter types and constraints
        for param_name, value in self.parameters.items():
            if param_name in self.parameter_schema:
                param_config = self.parameter_schema[param_name]
                validation_result = self._validate_single_parameter(param_name, value, param_config)
                errors.extend(validation_result.get('errors', []))
                warnings.extend(validation_result.get('warnings', []))
        
        self.validation_errors = errors
        self.validation_warnings = warnings
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_single_parameter(self, name: str, value: Any, config: Dict) -> Dict[str, List[str]]:
        """
        Validate a single parameter.
        
        Args:
            name: Parameter name
            value: Parameter value
            config: Parameter configuration
            
        Returns:
            Dictionary with validation errors and warnings
        """
        errors = []
        warnings = []
        
        param_type = config.get('type', 'string')
        
        # Type validation
        if param_type == 'float':
            try:
                float_value = float(value)
                min_val = config.get('min')
                max_val = config.get('max')
                
                if min_val is not None and float_value < min_val:
                    errors.append(f"Parameter '{name}' must be >= {min_val}")
                if max_val is not None and float_value > max_val:
                    errors.append(f"Parameter '{name}' must be <= {max_val}")
                    
            except (ValueError, TypeError):
                errors.append(f"Parameter '{name}' must be a number")
                
        elif param_type == 'integer':
            try:
                int_value = int(value)
                min_val = config.get('min')
                max_val = config.get('max')
                
                if min_val is not None and int_value < min_val:
                    errors.append(f"Parameter '{name}' must be >= {min_val}")
                if max_val is not None and int_value > max_val:
                    errors.append(f"Parameter '{name}' must be <= {max_val}")
                    
            except (ValueError, TypeError):
                errors.append(f"Parameter '{name}' must be an integer")
                
        elif param_type == 'boolean':
            if not isinstance(value, bool):
                try:
                    bool(value)
                except:
                    errors.append(f"Parameter '{name}' must be a boolean")
                    
        elif param_type == 'select':
            options = config.get('options', [])
            if value not in options:
                errors.append(f"Parameter '{name}' must be one of: {options}")
        
        return {'errors': errors, 'warnings': warnings}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert parameters to dictionary.
        
        Returns:
            Dictionary representation of parameters
        """
        return {
            'parameters': self.parameters,
            'schema': self.parameter_schema,
            'validation_errors': self.validation_errors,
            'validation_warnings': self.validation_warnings
        }
    
    def to_json(self) -> str:
        """
        Convert parameters to JSON string.
        
        Returns:
            JSON string representation of parameters
        """
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        Load parameters from dictionary.
        
        Args:
            data: Dictionary containing parameters data
        """
        self.parameters = data.get('parameters', {})
        self.parameter_schema = data.get('schema', {})
        self.validation_errors = data.get('validation_errors', [])
        self.validation_warnings = data.get('validation_warnings', [])
    
    def from_json(self, json_str: str) -> None:
        """
        Load parameters from JSON string.
        
        Args:
            json_str: JSON string containing parameters data
        """
        data = json.loads(json_str)
        self.from_dict(data) 