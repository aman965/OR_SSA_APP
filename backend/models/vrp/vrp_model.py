"""
VRP (Vehicle Routing Problem) Model Implementation

This module implements the VRP optimization model using the modular architecture.
It integrates with the existing VRP solver while providing a standardized interface.
"""

import os
import sys
import json
import tempfile
import subprocess
import pandas as pd
from typing import Dict, List, Any, Union
from pathlib import Path

from ..base.base_model import BaseOptimizationModel


class VRPModel(BaseOptimizationModel):
    """
    Vehicle Routing Problem optimization model.
    
    This class implements the VRP model using the existing enhanced VRP solver
    while providing a standardized interface through the base class.
    """
    
    def __init__(self, model_config: Dict):
        """Initialize the VRP model with configuration."""
        super().__init__(model_config)
        
        # VRP-specific initialization
        self.solver_path = self._get_solver_path()
        self.temp_dir = None
        
    def _get_solver_path(self) -> str:
        """Get the path to the VRP solver."""
        # Get the path to the enhanced VRP solver
        current_dir = Path(__file__).parent.parent.parent
        solver_path = current_dir / "solver" / "vrp_solver_enhanced.py"
        
        if not solver_path.exists():
            # Fallback to basic solver
            solver_path = current_dir / "solver" / "vrp_solver.py"
            
        if not solver_path.exists():
            raise FileNotFoundError("VRP solver not found")
            
        return str(solver_path)
    
    def validate_parameters(self, params: Dict) -> Dict[str, Any]:
        """
        Validate VRP parameters.
        
        Args:
            params: Dictionary of parameter values
            
        Returns:
            Validation results dictionary
        """
        errors = []
        warnings = []
        processed_params = {}
        
        # Get parameter schema from config
        param_schema = self.get_parameter_schema()
        
        # Validate each parameter
        for param_name, param_config in param_schema.items():
            value = params.get(param_name)
            required = param_config.get('required', False)
            param_type = param_config.get('type', 'string')
            
            # Check required parameters
            if required and (value is None or value == ""):
                errors.append(f"Parameter '{param_config.get('label', param_name)}' is required")
                continue
            
            # Skip validation for empty optional parameters
            if value is None or value == "":
                if param_config.get('default') is not None:
                    processed_params[param_name] = param_config['default']
                continue
            
            # Type-specific validation
            try:
                if param_type == 'float':
                    processed_value = float(value)
                    min_val = param_config.get('min')
                    max_val = param_config.get('max')
                    
                    if min_val is not None and processed_value < min_val:
                        errors.append(f"Parameter '{param_config.get('label', param_name)}' must be >= {min_val}")
                        continue
                    
                    if max_val is not None and processed_value > max_val:
                        errors.append(f"Parameter '{param_config.get('label', param_name)}' must be <= {max_val}")
                        continue
                    
                    processed_params[param_name] = processed_value
                    
                elif param_type == 'integer':
                    processed_value = int(value)
                    min_val = param_config.get('min')
                    max_val = param_config.get('max')
                    
                    if min_val is not None and processed_value < min_val:
                        errors.append(f"Parameter '{param_config.get('label', param_name)}' must be >= {min_val}")
                        continue
                    
                    if max_val is not None and processed_value > max_val:
                        errors.append(f"Parameter '{param_config.get('label', param_name)}' must be <= {max_val}")
                        continue
                    
                    processed_params[param_name] = processed_value
                    
                elif param_type == 'boolean':
                    processed_params[param_name] = bool(value)
                    
                elif param_type == 'select':
                    options = param_config.get('options', [])
                    if value not in options:
                        errors.append(f"Parameter '{param_config.get('label', param_name)}' must be one of: {options}")
                        continue
                    processed_params[param_name] = value
                    
                else:
                    processed_params[param_name] = str(value)
                    
            except (ValueError, TypeError) as e:
                errors.append(f"Parameter '{param_config.get('label', param_name)}' has invalid value: {value}")
        
        # VRP-specific validations
        if 'capacity' in processed_params and 'vehicle_count' in processed_params:
            if processed_params['capacity'] <= 0:
                errors.append("Vehicle capacity must be positive")
            if processed_params['vehicle_count'] <= 0:
                errors.append("Vehicle count must be positive")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'processed_params': processed_params
        }
    
    def validate_data(self, data: Union[pd.DataFrame, Dict, Any]) -> Dict[str, Any]:
        """
        Validate input data for VRP.
        
        Args:
            data: Input data (usually DataFrame)
            
        Returns:
            Validation results dictionary
        """
        errors = []
        warnings = []
        data_info = {}
        
        if not isinstance(data, pd.DataFrame):
            errors.append("Data must be a pandas DataFrame")
            return {
                'valid': False,
                'errors': errors,
                'warnings': warnings,
                'data_info': data_info
            }
        
        # Get data requirements from config
        data_requirements = self.get_data_requirements()
        required_columns = data_requirements.get('required_columns', [])
        optional_columns = data_requirements.get('optional_columns', [])
        min_rows = data_requirements.get('min_rows', 3)
        max_rows = data_requirements.get('max_rows', 1000)
        
        # Check minimum rows
        if len(data) < min_rows:
            errors.append(f"Data must have at least {min_rows} rows")
        
        # Check maximum rows
        if len(data) > max_rows:
            warnings.append(f"Data has {len(data)} rows, which exceeds recommended maximum of {max_rows}")
        
        # Check for required columns
        missing_required = []
        for col in required_columns:
            if col not in data.columns:
                missing_required.append(col)
        
        # Check for alternative formats
        if missing_required:
            alternative_formats = data_requirements.get('alternative_formats', [])
            format_found = False
            
            for alt_format in alternative_formats:
                alt_required = alt_format.get('required_columns', [])
                if all(col in data.columns for col in alt_required):
                    format_found = True
                    data_info['format'] = alt_format['name']
                    break
            
            if not format_found:
                errors.append(f"Missing required columns: {missing_required}")
                errors.append(f"Available columns: {list(data.columns)}")
        else:
            data_info['format'] = 'standard'
        
        # Validate data types and values
        if 'x' in data.columns and 'y' in data.columns:
            # Coordinate-based data
            if not pd.api.types.is_numeric_dtype(data['x']):
                errors.append("Column 'x' must contain numeric values")
            if not pd.api.types.is_numeric_dtype(data['y']):
                errors.append("Column 'y' must contain numeric values")
            
            # Check for missing coordinates
            if data[['x', 'y']].isnull().any().any():
                errors.append("Coordinates (x, y) cannot contain missing values")
        
        if 'demand' in data.columns:
            if not pd.api.types.is_numeric_dtype(data['demand']):
                errors.append("Column 'demand' must contain numeric values")
            if (data['demand'] < 0).any():
                errors.append("Demand values must be non-negative")
        
        # Data info
        data_info.update({
            'rows': len(data),
            'columns': len(data.columns),
            'column_names': list(data.columns),
            'has_coordinates': 'x' in data.columns and 'y' in data.columns,
            'has_demand': 'demand' in data.columns,
            'has_time_windows': 'time_window_start' in data.columns and 'time_window_end' in data.columns
        })
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'data_info': data_info
        }
    
    def solve(self, data: Any, params: Dict, constraints: List = None) -> Dict[str, Any]:
        """
        Solve the VRP problem using the existing enhanced solver.
        
        Args:
            data: Input data (DataFrame)
            params: Model parameters
            constraints: List of constraints (optional)
            
        Returns:
            Solution dictionary
        """
        try:
            # Create temporary directory for solver files
            self.temp_dir = tempfile.mkdtemp(prefix="vrp_solve_")
            
            # Prepare data file
            data_file = os.path.join(self.temp_dir, "data.csv")
            data.to_csv(data_file, index=False)
            
            # Prepare scenario file for the solver
            scenario_data = {
                'dataset_file_path': data_file,
                'params': self._convert_params_to_solver_format(params),
                'gpt_prompt': self._convert_constraints_to_prompt(constraints or [])
            }
            
            scenario_file = os.path.join(self.temp_dir, "scenario.json")
            with open(scenario_file, 'w') as f:
                json.dump(scenario_data, f, indent=2)
            
            # Run the VRP solver
            cmd = [sys.executable, self.solver_path, '--scenario-path', scenario_file]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                return {
                    'status': 'error',
                    'error': f"Solver failed: {result.stderr}",
                    'solver_output': result.stdout,
                    'solve_time': 0
                }
            
            # Read solution from outputs directory
            outputs_dir = os.path.join(self.temp_dir, "outputs")
            solution_file = os.path.join(outputs_dir, "solution_summary.json")
            
            if os.path.exists(solution_file):
                with open(solution_file, 'r') as f:
                    solution = json.load(f)
                
                # Add solver output for debugging
                solution['solver_output'] = result.stdout
                solution['solver_stderr'] = result.stderr
                
                return solution
            else:
                # Check for failure file
                failure_file = os.path.join(outputs_dir, "failure_summary.json")
                if os.path.exists(failure_file):
                    with open(failure_file, 'r') as f:
                        failure = json.load(f)
                    return failure
                else:
                    return {
                        'status': 'error',
                        'error': 'No solution or failure file found',
                        'solver_output': result.stdout,
                        'solve_time': 0
                    }
                    
        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'error': 'Solver timeout (5 minutes)',
                'solve_time': 300
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'solve_time': 0
            }
        finally:
            # Cleanup temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                try:
                    shutil.rmtree(self.temp_dir)
                except:
                    pass  # Ignore cleanup errors
    
    def _convert_params_to_solver_format(self, params: Dict) -> Dict:
        """Convert parameters to the format expected by the existing solver."""
        solver_params = {}
        
        # Map new parameter names to old solver parameter names
        param_mapping = {
            'capacity': 'param1',
            'vehicle_count': 'param2',
            'max_distance': 'vehicle_limit'
        }
        
        for new_name, old_name in param_mapping.items():
            if new_name in params:
                solver_params[old_name] = params[new_name]
        
        # Add any additional parameters
        for key, value in params.items():
            if key not in param_mapping:
                solver_params[key] = value
        
        return solver_params
    
    def _convert_constraints_to_prompt(self, constraints: List) -> str:
        """Convert constraint objects to natural language prompt for the solver."""
        if not constraints:
            return ""
        
        # For now, just concatenate constraint descriptions
        # In the future, this could be more sophisticated
        constraint_texts = []
        for constraint in constraints:
            if isinstance(constraint, dict):
                text = constraint.get('text', constraint.get('description', str(constraint)))
            else:
                text = str(constraint)
            constraint_texts.append(text)
        
        return " ".join(constraint_texts)
    
    def calculate_kpis(self, solution: Dict) -> Dict[str, Any]:
        """
        Calculate Key Performance Indicators from VRP solution.
        
        Args:
            solution: Solution dictionary from solve() method
            
        Returns:
            Dictionary of KPIs with their values
        """
        if solution.get('status') != 'optimal':
            return {}
        
        routes = solution.get('routes', [])
        total_distance = solution.get('total_distance', 0)
        vehicle_count_used = solution.get('vehicle_count', 0)
        
        # Calculate KPIs based on the configuration
        kpis = {}
        
        # Total distance
        kpis['total_distance'] = round(float(total_distance), 2)
        
        # Vehicle utilization
        max_vehicles = self.parameters.get('vehicle_count', 3)
        kpis['vehicle_utilization'] = round((vehicle_count_used / max_vehicles) * 100, 1) if max_vehicles > 0 else 0
        
        # Average route distance
        kpis['avg_route_distance'] = round(total_distance / len(routes), 2) if routes else 0
        
        # Capacity utilization (approximate)
        total_capacity = max_vehicles * self.parameters.get('capacity', 100)
        total_demand = sum(len(route.get('stops', [])) - 2 for route in routes)  # Exclude depot
        kpis['capacity_utilization'] = round((total_demand / total_capacity) * 100, 1) if total_capacity > 0 else 0
        
        # Customers served
        kpis['customers_served'] = sum(len(route.get('stops', [])) - 2 for route in routes)  # Exclude depot
        
        # Routes count
        kpis['routes_count'] = len(routes)
        
        return kpis
    
    def get_comparison_metrics(self, solution: Dict) -> Dict[str, Any]:
        """
        Get metrics for comparing different VRP scenarios.
        
        Args:
            solution: Solution dictionary from solve() method
            
        Returns:
            Dictionary of comparison metrics
        """
        if solution.get('status') != 'optimal':
            return {}
        
        kpis = self.calculate_kpis(solution)
        routes = solution.get('routes', [])
        
        return {
            'total_distance': kpis.get('total_distance', 0),
            'vehicles_used': solution.get('vehicle_count', 0),
            'avg_route_distance': kpis.get('avg_route_distance', 0),
            'customer_coverage': kpis.get('customers_served', 0),
            'capacity_utilization': kpis.get('capacity_utilization', 0),
            'total_cost': kpis.get('total_distance', 0)  # Assuming cost = distance for now
        } 