"""
Base Classes for Optimization Models

This module provides abstract base classes that all optimization models must inherit from.
This ensures consistent interfaces and behavior across all model types.
"""

from .base_model import BaseOptimizationModel
from .base_solver import BaseSolver
from .base_parameters import BaseParameters
from .base_results import BaseResults

__all__ = [
    'BaseOptimizationModel',
    'BaseSolver',
    'BaseParameters', 
    'BaseResults'
] 