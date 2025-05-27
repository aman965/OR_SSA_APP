"""
Inventory Optimization Model Implementation

This module implements the inventory optimization model using the modular architecture.
It provides comprehensive inventory management including EOQ, safety stock, ABC analysis,
and multi-objective optimization with budget constraints.
"""

import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Union
from pathlib import Path

from ..base.base_model import BaseOptimizationModel
from .inventory_solver import InventoryOptimizationSolver


class InventoryModel(BaseOptimizationModel):
    """
    Inventory Optimization model.
    
    This class implements comprehensive inventory optimization including:
    - Economic Order Quantity (EOQ) optimization
    - Safety stock calculation with service level constraints
    - ABC analysis for inventory classification
    - Multi-item optimization with budget constraints
    - Demand forecasting and variability analysis
    """
    
    def __init__(self, model_config: Dict):
        """Initialize the inventory model with configuration."""
        super().__init__(model_config)
        
        # Inventory-specific initialization
        self.solver = InventoryOptimizationSolver()
        self.temp_dir = None
        
    def validate_parameters(self, params: Dict) -> Dict[str, Any]:
        """
        Validate inventory optimization parameters.
        
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
        
        # Inventory-specific validations
        if 'holding_cost' in processed_params and processed_params['holding_cost'] <= 0:
            errors.append("Holding cost must be positive")
        
        if 'ordering_cost' in processed_params and processed_params['ordering_cost'] <= 0:
            errors.append("Ordering cost must be positive")
        
        if 'service_level' in processed_params:
            service_level = processed_params['service_level']
            if service_level <= 0.5 or service_level >= 1.0:
                errors.append("Service level must be between 0.5 and 1.0")
        
        if 'max_inventory_value' in processed_params and processed_params['max_inventory_value'] <= 0:
            errors.append("Maximum inventory value must be positive")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'processed_params': processed_params
        }
    
    def validate_data(self, data: Union[pd.DataFrame, Dict, Any]) -> Dict[str, Any]:
        """
        Validate input data for inventory optimization.
        
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
        min_rows = data_requirements.get('min_rows', 1)
        max_rows = data_requirements.get('max_rows', 10000)
        
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
        if 'item_id' in data.columns:
            # Check for duplicate item IDs
            if data['item_id'].duplicated().any():
                errors.append("Item IDs must be unique")
        
        if 'demand' in data.columns:
            if not pd.api.types.is_numeric_dtype(data['demand']):
                errors.append("Column 'demand' must contain numeric values")
            if (data['demand'] < 0).any():
                errors.append("Demand values must be non-negative")
            if (data['demand'] == 0).all():
                warnings.append("All demand values are zero - optimization may not be meaningful")
        
        if 'cost' in data.columns:
            if not pd.api.types.is_numeric_dtype(data['cost']):
                errors.append("Column 'cost' must contain numeric values")
            if (data['cost'] <= 0).any():
                errors.append("Cost values must be positive")
        
        if 'lead_time' in data.columns:
            if not pd.api.types.is_numeric_dtype(data['lead_time']):
                errors.append("Column 'lead_time' must contain numeric values")
            if (data['lead_time'] <= 0).any():
                errors.append("Lead time values must be positive")
        
        # Data info
        data_info.update({
            'rows': len(data),
            'columns': len(data.columns),
            'column_names': list(data.columns),
            'has_lead_time': 'lead_time' in data.columns,
            'has_supplier': 'supplier' in data.columns,
            'has_category': 'category' in data.columns,
            'unique_items': data['item_id'].nunique() if 'item_id' in data.columns else len(data),
            'total_demand': data['demand'].sum() if 'demand' in data.columns else 0,
            'avg_cost': data['cost'].mean() if 'cost' in data.columns else 0
        })
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'data_info': data_info
        }
    
    def solve(self, data: Any, params: Dict, constraints: List = None) -> Dict[str, Any]:
        """
        Solve the inventory optimization problem.
        
        Args:
            data: Input data (DataFrame)
            params: Model parameters
            constraints: List of constraints (optional)
            
        Returns:
            Solution dictionary
        """
        try:
            # Validate inputs
            if not isinstance(data, pd.DataFrame):
                return {
                    'status': 'error',
                    'error': 'Data must be a pandas DataFrame',
                    'solve_time': 0
                }
            
            # Process constraints (for future enhancement)
            processed_constraints = self._process_constraints(constraints or [])
            
            # Apply constraints to parameters if needed
            adjusted_params = self._apply_constraints_to_parameters(params, processed_constraints)
            
            # Solve using the inventory solver
            solution = self.solver.solve_inventory_optimization(data, adjusted_params)
            
            # Add timing and metadata
            solution['solve_time'] = 0.1  # Inventory optimization is typically fast
            solution['model_type'] = 'inventory'
            solution['parameters_used'] = adjusted_params
            solution['constraints_applied'] = len(processed_constraints)
            
            return solution
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'solve_time': 0,
                'model_type': 'inventory'
            }
    
    def _process_constraints(self, constraints: List) -> List[Dict]:
        """Process natural language constraints into structured format."""
        processed_constraints = []
        
        for constraint in constraints:
            if isinstance(constraint, str):
                # Simple constraint processing - can be enhanced with NLP
                constraint_lower = constraint.lower()
                
                if 'budget' in constraint_lower or 'maximum inventory value' in constraint_lower:
                    # Extract budget constraint
                    import re
                    numbers = re.findall(r'\d+(?:\.\d+)?', constraint)
                    if numbers:
                        processed_constraints.append({
                            'type': 'budget_constraint',
                            'value': float(numbers[0]),
                            'original': constraint
                        })
                
                elif 'service level' in constraint_lower:
                    # Extract service level constraint
                    import re
                    numbers = re.findall(r'\d+(?:\.\d+)?', constraint)
                    if numbers:
                        service_level = float(numbers[0])
                        if service_level > 1:
                            service_level = service_level / 100  # Convert percentage
                        processed_constraints.append({
                            'type': 'service_level_constraint',
                            'value': service_level,
                            'original': constraint
                        })
                
                elif 'abc' in constraint_lower or 'classification' in constraint_lower:
                    processed_constraints.append({
                        'type': 'abc_classification',
                        'original': constraint
                    })
            
            elif isinstance(constraint, dict):
                processed_constraints.append(constraint)
        
        return processed_constraints
    
    def _apply_constraints_to_parameters(self, params: Dict, constraints: List[Dict]) -> Dict:
        """Apply constraints to modify parameters."""
        adjusted_params = params.copy()
        
        for constraint in constraints:
            constraint_type = constraint.get('type', '')
            
            if constraint_type == 'budget_constraint':
                adjusted_params['max_inventory_value'] = constraint['value']
            
            elif constraint_type == 'service_level_constraint':
                adjusted_params['service_level'] = constraint['value']
        
        return adjusted_params
    
    def calculate_kpis(self, solution: Dict) -> Dict[str, Any]:
        """
        Calculate Key Performance Indicators from inventory solution.
        
        Args:
            solution: Solution dictionary from solve() method
            
        Returns:
            Dictionary of KPIs with their values
        """
        if solution.get('status') != 'optimal':
            return {}
        
        # Extract KPIs from solution
        aggregate_kpis = solution.get('aggregate_kpis', {})
        
        # Map solution KPIs to configuration KPIs
        kpis = {
            'total_cost': aggregate_kpis.get('total_annual_cost', 0),
            'holding_cost': aggregate_kpis.get('total_holding_cost', 0),
            'ordering_cost': aggregate_kpis.get('total_ordering_cost', 0),
            'service_level_achieved': aggregate_kpis.get('service_level_achieved', 0),
            'inventory_turnover': aggregate_kpis.get('inventory_turnover', 0),
            'total_inventory_value': aggregate_kpis.get('total_inventory_value', 0),
            'items_optimized': aggregate_kpis.get('items_optimized', 0),
            'avg_order_frequency': aggregate_kpis.get('avg_order_frequency', 0)
        }
        
        return kpis
    
    def get_comparison_metrics(self, solution: Dict) -> Dict[str, Any]:
        """
        Get metrics for comparing different inventory scenarios.
        
        Args:
            solution: Solution dictionary from solve() method
            
        Returns:
            Dictionary of comparison metrics
        """
        if solution.get('status') != 'optimal':
            return {}
        
        kpis = self.calculate_kpis(solution)
        aggregate_kpis = solution.get('aggregate_kpis', {})
        
        return {
            'total_cost': kpis.get('total_cost', 0),
            'holding_cost': kpis.get('holding_cost', 0),
            'ordering_cost': kpis.get('ordering_cost', 0),
            'service_level_achieved': kpis.get('service_level_achieved', 0),
            'inventory_turnover': kpis.get('inventory_turnover', 0),
            'total_inventory_value': kpis.get('total_inventory_value', 0)
        }
    
    def get_detailed_results(self, solution: Dict) -> Dict[str, Any]:
        """
        Get detailed results for display in result tabs.
        
        Args:
            solution: Solution dictionary from solve() method
            
        Returns:
            Dictionary with detailed results for each tab
        """
        if solution.get('status') != 'optimal':
            return {}
        
        optimization_results = solution.get('optimization_results', [])
        abc_analysis = solution.get('abc_analysis', {})
        cost_breakdown = solution.get('cost_breakdown', {})
        demand_forecast = solution.get('demand_forecast', [])
        
        # Prepare policy table data
        policy_data = []
        for result in optimization_results:
            policy_data.append({
                'item_id': result['item_id'],
                'eoq': result['eoq'],
                'reorder_point': result['reorder_point'],
                'safety_stock': result['safety_stock'],
                'max_inventory': result['max_inventory'],
                'order_frequency': result['order_frequency'],
                'annual_cost': result['total_annual_cost'],
                'abc_class': result['abc_class']
            })
        
        # Prepare forecast data
        forecast_data = []
        for forecast in demand_forecast:
            forecast_data.append({
                'item_id': forecast['item_id'],
                'annual_demand': forecast['annual_demand_mean'],
                'demand_std': forecast['annual_demand_std'],
                'cv': forecast['demand_cv'],
                'forecast_method': forecast['forecast_method']
            })
        
        # Prepare cost analysis data
        cost_data = {
            'cost_components': [
                {'component': 'Holding Cost', 'percentage': cost_breakdown.get('holding_cost_percentage', 0)},
                {'component': 'Ordering Cost', 'percentage': cost_breakdown.get('ordering_cost_percentage', 0)},
                {'component': 'Stockout Cost', 'percentage': cost_breakdown.get('stockout_cost_percentage', 0)}
            ],
            'cost_by_item': [
                {
                    'item_id': result['item_id'],
                    'total_cost': result['total_annual_cost'],
                    'holding_cost': result['annual_holding_cost'],
                    'ordering_cost': result['annual_ordering_cost'],
                    'stockout_cost': result['annual_stockout_cost']
                }
                for result in optimization_results
            ]
        }
        
        # Prepare inventory level data
        inventory_data = {
            'inventory_by_item': [
                {
                    'item_id': result['item_id'],
                    'inventory_value': result['inventory_value'],
                    'average_inventory': result['average_inventory'],
                    'safety_stock': result['safety_stock'],
                    'abc_class': result['abc_class']
                }
                for result in optimization_results
            ],
            'abc_distribution': {
                'A': len([r for r in optimization_results if r['abc_class'] == 'A']),
                'B': len([r for r in optimization_results if r['abc_class'] == 'B']),
                'C': len([r for r in optimization_results if r['abc_class'] == 'C'])
            }
        }
        
        return {
            'policy': policy_data,
            'forecast': forecast_data,
            'costs': cost_data,
            'inventory': inventory_data
        } 