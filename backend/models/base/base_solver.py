"""
Abstract Base Solver Class

This module defines the interface that all optimization solvers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import pandas as pd


class BaseSolver(ABC):
    """
    Abstract base class for all optimization solvers.
    
    All solvers must inherit from this class and implement the required abstract methods.
    """
    
    def __init__(self, solver_config: Dict = None):
        """
        Initialize the solver.
        
        Args:
            solver_config: Dictionary containing solver configuration
        """
        self.solver_config = solver_config or {}
        self.solver_name = self.solver_config.get('name', 'unknown')
        self.time_limit = self.solver_config.get('time_limit', 300)
        self.gap_tolerance = self.solver_config.get('gap_tolerance', 0.01)
        
    @abstractmethod
    def solve(self, data: Any, parameters: Dict, constraints: List = None) -> Dict[str, Any]:
        """
        Solve the optimization problem.
        
        Args:
            data: Input data
            parameters: Model parameters
            constraints: List of constraints (optional)
            
        Returns:
            Dictionary containing solution results
        """
        pass
    
    @abstractmethod
    def validate_input(self, data: Any, parameters: Dict) -> Dict[str, Any]:
        """
        Validate input data and parameters.
        
        Args:
            data: Input data
            parameters: Model parameters
            
        Returns:
            Validation results dictionary
        """
        pass
    
    def get_solver_info(self) -> Dict[str, Any]:
        """
        Get information about the solver.
        
        Returns:
            Dictionary with solver information
        """
        return {
            'name': self.solver_name,
            'time_limit': self.time_limit,
            'gap_tolerance': self.gap_tolerance,
            'config': self.solver_config
        } 