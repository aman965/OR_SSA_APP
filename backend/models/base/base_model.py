"""
Abstract Base Class for Optimization Models

This module defines the interface that all optimization models must implement.
It ensures consistency across different model types (VRP, Inventory, Scheduling, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
import pandas as pd
import json
import os
from datetime import datetime


class BaseOptimizationModel(ABC):
    """
    Abstract base class for all optimization models.
    
    All optimization models (VRP, Inventory, Scheduling, etc.) must inherit from this class
    and implement the required abstract methods.
    """
    
    def __init__(self, model_config: Dict):
        """
        Initialize the optimization model.
        
        Args:
            model_config: Dictionary containing model configuration from JSON file
        """
        self.model_config = model_config
        self.model_type = model_config['type']
        self.model_name = model_config['name']
        self.model_description = model_config['description']
        self.model_icon = model_config.get('icon', '🔧')
        
        # Model state
        self.parameters = {}
        self.constraints = []
        self.data = None
        self.solution = None
        self.kpis = {}
        self.comparison_metrics = {}
        
        # Validation flags
        self._parameters_validated = False
        self._data_validated = False
        
    @abstractmethod
    def validate_parameters(self, params: Dict) -> Dict[str, Any]:
        """
        Validate model parameters.
        
        Args:
            params: Dictionary of parameter values
            
        Returns:
            Dictionary with validation results:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str],
                'processed_params': Dict
            }
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: Union[pd.DataFrame, Dict, Any]) -> Dict[str, Any]:
        """
        Validate input data for the model.
        
        Args:
            data: Input data (usually DataFrame)
            
        Returns:
            Dictionary with validation results:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str],
                'data_info': Dict
            }
        """
        pass
    
    @abstractmethod
    def solve(self, data: Any, params: Dict, constraints: List = None) -> Dict[str, Any]:
        """
        Solve the optimization problem.
        
        Args:
            data: Input data
            params: Model parameters
            constraints: List of constraints (optional)
            
        Returns:
            Dictionary containing solution:
            {
                'status': str,  # 'optimal', 'feasible', 'infeasible', 'error'
                'objective_value': float,
                'solution_data': Dict,
                'solve_time': float,
                'solver_info': Dict
            }
        """
        pass
    
    @abstractmethod
    def calculate_kpis(self, solution: Dict) -> Dict[str, Any]:
        """
        Calculate Key Performance Indicators from solution.
        
        Args:
            solution: Solution dictionary from solve() method
            
        Returns:
            Dictionary of KPIs with their values
        """
        pass
    
    @abstractmethod
    def get_comparison_metrics(self, solution: Dict) -> Dict[str, Any]:
        """
        Get metrics for comparing different scenarios.
        
        Args:
            solution: Solution dictionary from solve() method
            
        Returns:
            Dictionary of comparison metrics
        """
        pass
    
    def get_parameter_schema(self) -> Dict:
        """
        Get parameter schema for UI generation.
        
        Returns:
            Parameter schema from model configuration
        """
        return self.model_config.get('parameters', {})
    
    def get_data_requirements(self) -> Dict:
        """
        Get data requirements for this model.
        
        Returns:
            Data requirements from model configuration
        """
        return self.model_config.get('data_requirements', {})
    
    def get_kpi_definitions(self) -> List[Dict]:
        """
        Get KPI definitions for results display.
        
        Returns:
            List of KPI definitions from model configuration
        """
        return self.model_config.get('kpis', [])
    
    def get_result_tabs(self) -> List[Dict]:
        """
        Get result tab configurations for UI.
        
        Returns:
            List of result tab configurations
        """
        return self.model_config.get('result_tabs', [])
    
    def set_parameters(self, params: Dict) -> bool:
        """
        Set and validate model parameters.
        
        Args:
            params: Dictionary of parameter values
            
        Returns:
            True if parameters are valid, False otherwise
        """
        validation_result = self.validate_parameters(params)
        
        if validation_result['valid']:
            self.parameters = validation_result['processed_params']
            self._parameters_validated = True
            return True
        else:
            self._parameters_validated = False
            return False
    
    def set_data(self, data: Any) -> bool:
        """
        Set and validate input data.
        
        Args:
            data: Input data
            
        Returns:
            True if data is valid, False otherwise
        """
        validation_result = self.validate_data(data)
        
        if validation_result['valid']:
            self.data = data
            self._data_validated = True
            return True
        else:
            self._data_validated = False
            return False
    
    def is_ready_to_solve(self) -> Dict[str, Any]:
        """
        Check if model is ready to solve.
        
        Returns:
            Dictionary with readiness status and any issues
        """
        issues = []
        
        if not self._parameters_validated:
            issues.append("Parameters not validated")
        
        if not self._data_validated:
            issues.append("Data not validated")
        
        if not self.parameters:
            issues.append("No parameters set")
        
        if self.data is None:
            issues.append("No data set")
        
        return {
            'ready': len(issues) == 0,
            'issues': issues
        }
    
    def solve_complete(self, data: Any = None, params: Dict = None, constraints: List = None) -> Dict[str, Any]:
        """
        Complete solve workflow with validation and KPI calculation.
        
        Args:
            data: Input data (optional if already set)
            params: Parameters (optional if already set)
            constraints: Constraints (optional)
            
        Returns:
            Complete solution with KPIs and metrics
        """
        start_time = datetime.now()
        
        try:
            # Set data and parameters if provided
            if data is not None:
                if not self.set_data(data):
                    return {
                        'status': 'error',
                        'error': 'Data validation failed',
                        'solve_time': 0
                    }
            
            if params is not None:
                if not self.set_parameters(params):
                    return {
                        'status': 'error', 
                        'error': 'Parameter validation failed',
                        'solve_time': 0
                    }
            
            # Check readiness
            readiness = self.is_ready_to_solve()
            if not readiness['ready']:
                return {
                    'status': 'error',
                    'error': f"Model not ready: {', '.join(readiness['issues'])}",
                    'solve_time': 0
                }
            
            # Solve the problem
            solution = self.solve(self.data, self.parameters, constraints or [])
            
            # Calculate KPIs if solution is successful
            if solution.get('status') in ['optimal', 'feasible']:
                solution['kpis'] = self.calculate_kpis(solution)
                solution['comparison_metrics'] = self.get_comparison_metrics(solution)
            
            # Add timing information
            end_time = datetime.now()
            solution['total_time'] = (end_time - start_time).total_seconds()
            
            # Store solution
            self.solution = solution
            self.kpis = solution.get('kpis', {})
            self.comparison_metrics = solution.get('comparison_metrics', {})
            
            return solution
            
        except Exception as e:
            end_time = datetime.now()
            return {
                'status': 'error',
                'error': str(e),
                'solve_time': (end_time - start_time).total_seconds()
            }
    
    def export_solution(self, output_dir: str, scenario_id: str = None) -> Dict[str, str]:
        """
        Export solution to files.
        
        Args:
            output_dir: Directory to save files
            scenario_id: Optional scenario ID for file naming
            
        Returns:
            Dictionary of exported file paths
        """
        if not self.solution:
            raise ValueError("No solution to export")
        
        os.makedirs(output_dir, exist_ok=True)
        
        exported_files = {}
        
        # Export main solution
        solution_file = os.path.join(output_dir, "solution_summary.json")
        with open(solution_file, 'w') as f:
            json.dump(self.solution, f, indent=4, default=str)
        exported_files['solution'] = solution_file
        
        # Export KPIs
        if self.kpis:
            kpi_file = os.path.join(output_dir, "kpis.json")
            with open(kpi_file, 'w') as f:
                json.dump(self.kpis, f, indent=4, default=str)
            exported_files['kpis'] = kpi_file
        
        # Export comparison metrics
        if self.comparison_metrics:
            metrics_file = os.path.join(output_dir, "compare_metrics.json")
            with open(metrics_file, 'w') as f:
                json.dump({
                    'scenario_id': scenario_id,
                    'model_type': self.model_type,
                    'kpis': self.comparison_metrics,
                    'status': self.solution.get('status', 'unknown')
                }, f, indent=4, default=str)
            exported_files['comparison'] = metrics_file
        
        return exported_files
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get comprehensive model information.
        
        Returns:
            Dictionary with model information
        """
        return {
            'type': self.model_type,
            'name': self.model_name,
            'description': self.model_description,
            'icon': self.model_icon,
            'parameter_count': len(self.get_parameter_schema()),
            'kpi_count': len(self.get_kpi_definitions()),
            'result_tabs': len(self.get_result_tabs()),
            'data_requirements': self.get_data_requirements(),
            'has_solution': self.solution is not None,
            'parameters_set': self._parameters_validated,
            'data_set': self._data_validated
        } 