"""
Base Results Class

This module provides base functionality for handling optimization results.
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime


class BaseResults:
    """
    Base class for handling optimization results.
    
    Provides common functionality for result processing, validation, and serialization.
    """
    
    def __init__(self, result_schema: Dict = None):
        """
        Initialize the results handler.
        
        Args:
            result_schema: Dictionary defining result schema
        """
        self.result_schema = result_schema or {}
        self.raw_results = {}
        self.processed_results = {}
        self.kpis = {}
        self.comparison_metrics = {}
        self.metadata = {
            'created_at': datetime.now().isoformat(),
            'status': 'unknown'
        }
        
    def set_raw_results(self, results: Dict[str, Any]) -> None:
        """
        Set the raw results from the solver.
        
        Args:
            results: Raw results dictionary from solver
        """
        self.raw_results = results
        self.metadata['status'] = results.get('status', 'unknown')
        self.metadata['updated_at'] = datetime.now().isoformat()
        
    def process_results(self) -> Dict[str, Any]:
        """
        Process raw results into standardized format.
        
        Returns:
            Processing results dictionary
        """
        if not self.raw_results:
            return {
                'success': False,
                'error': 'No raw results to process'
            }
        
        try:
            # Basic processing - copy raw results
            self.processed_results = self.raw_results.copy()
            
            # Extract standard fields
            self.processed_results['objective_value'] = self.raw_results.get('total_distance', 0)
            self.processed_results['solve_time'] = self.raw_results.get('solve_time', 0)
            self.processed_results['solver_status'] = self.raw_results.get('status', 'unknown')
            
            return {
                'success': True,
                'processed_fields': len(self.processed_results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_kpis(self, kpi_definitions: List[Dict] = None) -> Dict[str, Any]:
        """
        Calculate KPIs from processed results.
        
        Args:
            kpi_definitions: List of KPI definitions
            
        Returns:
            Dictionary of calculated KPIs
        """
        if not self.processed_results:
            return {}
        
        kpi_definitions = kpi_definitions or self.result_schema.get('kpis', [])
        calculated_kpis = {}
        
        for kpi_def in kpi_definitions:
            kpi_name = kpi_def.get('name')
            if not kpi_name:
                continue
                
            # Try to extract KPI value from results
            kpi_value = self._extract_kpi_value(kpi_name, kpi_def)
            if kpi_value is not None:
                calculated_kpis[kpi_name] = self._format_kpi_value(kpi_value, kpi_def)
        
        self.kpis = calculated_kpis
        return calculated_kpis
    
    def _extract_kpi_value(self, kpi_name: str, kpi_def: Dict) -> Any:
        """
        Extract KPI value from results.
        
        Args:
            kpi_name: Name of the KPI
            kpi_def: KPI definition
            
        Returns:
            KPI value or None if not found
        """
        # Try direct lookup first
        if kpi_name in self.processed_results:
            return self.processed_results[kpi_name]
        
        # Try alternative names
        alt_names = kpi_def.get('alternative_names', [])
        for alt_name in alt_names:
            if alt_name in self.processed_results:
                return self.processed_results[alt_name]
        
        # Try calculation if formula is provided
        formula = kpi_def.get('formula')
        if formula:
            try:
                return self._calculate_kpi_from_formula(formula)
            except:
                pass
        
        return None
    
    def _calculate_kpi_from_formula(self, formula: str) -> Any:
        """
        Calculate KPI value from formula.
        
        Args:
            formula: Formula string
            
        Returns:
            Calculated value
        """
        # Simple formula evaluation (can be extended)
        # For now, just support basic arithmetic with result fields
        
        # Replace field names with values
        eval_formula = formula
        for key, value in self.processed_results.items():
            if isinstance(value, (int, float)):
                eval_formula = eval_formula.replace(f"{{{key}}}", str(value))
        
        # Evaluate safely (limited to basic math)
        try:
            return eval(eval_formula, {"__builtins__": {}}, {})
        except:
            return None
    
    def _format_kpi_value(self, value: Any, kpi_def: Dict) -> Any:
        """
        Format KPI value according to definition.
        
        Args:
            value: Raw KPI value
            kpi_def: KPI definition
            
        Returns:
            Formatted KPI value
        """
        kpi_type = kpi_def.get('type', 'numeric')
        format_str = kpi_def.get('format', None)
        
        if kpi_type == 'percentage':
            if isinstance(value, (int, float)):
                if format_str:
                    return format_str % value
                return f"{value:.1f}%"
        elif kpi_type == 'currency':
            if isinstance(value, (int, float)):
                if format_str:
                    return format_str % value
                return f"${value:.2f}"
        elif kpi_type == 'numeric':
            if isinstance(value, (int, float)):
                if format_str:
                    return format_str % value
                return round(value, 2)
        elif kpi_type == 'integer':
            if isinstance(value, (int, float)):
                return int(value)
        
        return value
    
    def get_comparison_metrics(self, metric_names: List[str] = None) -> Dict[str, Any]:
        """
        Get metrics for comparison purposes.
        
        Args:
            metric_names: List of metric names to extract
            
        Returns:
            Dictionary of comparison metrics
        """
        if not metric_names:
            metric_names = self.result_schema.get('comparison_metrics', [])
        
        comparison_metrics = {}
        
        # Extract from KPIs first
        for metric_name in metric_names:
            if metric_name in self.kpis:
                comparison_metrics[metric_name] = self.kpis[metric_name]
            elif metric_name in self.processed_results:
                comparison_metrics[metric_name] = self.processed_results[metric_name]
        
        self.comparison_metrics = comparison_metrics
        return comparison_metrics
    
    def validate_results(self) -> Dict[str, Any]:
        """
        Validate results against schema.
        
        Returns:
            Validation results dictionary
        """
        errors = []
        warnings = []
        
        # Check if results exist
        if not self.raw_results:
            errors.append("No raw results available")
        
        if not self.processed_results:
            warnings.append("Results not processed yet")
        
        # Check required fields
        required_fields = self.result_schema.get('required_fields', [])
        for field in required_fields:
            if field not in self.processed_results:
                errors.append(f"Required field '{field}' missing from results")
        
        # Check status
        status = self.metadata.get('status', 'unknown')
        if status not in ['optimal', 'feasible', 'infeasible', 'error', 'timeout']:
            warnings.append(f"Unknown status: {status}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert results to dictionary.
        
        Returns:
            Dictionary representation of results
        """
        return {
            'raw_results': self.raw_results,
            'processed_results': self.processed_results,
            'kpis': self.kpis,
            'comparison_metrics': self.comparison_metrics,
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        """
        Convert results to JSON string.
        
        Returns:
            JSON string representation of results
        """
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        Load results from dictionary.
        
        Args:
            data: Dictionary containing results data
        """
        self.raw_results = data.get('raw_results', {})
        self.processed_results = data.get('processed_results', {})
        self.kpis = data.get('kpis', {})
        self.comparison_metrics = data.get('comparison_metrics', {})
        self.metadata = data.get('metadata', {})
    
    def from_json(self, json_str: str) -> None:
        """
        Load results from JSON string.
        
        Args:
            json_str: JSON string containing results data
        """
        data = json.loads(json_str)
        self.from_dict(data) 