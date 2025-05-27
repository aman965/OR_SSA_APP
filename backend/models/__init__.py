"""
Optimization Models Package

This package contains all optimization model implementations following a modular architecture.
Each model type (VRP, Inventory, Scheduling, etc.) has its own subdirectory with:
- Model implementation (inherits from BaseOptimizationModel)
- Solver implementation
- Parameter definitions
- KPI calculations
- Constraint handling (if needed)

Usage:
    from backend.models.vrp import VRPModel
    from backend.models.inventory import InventoryModel
"""

from .base.base_model import BaseOptimizationModel
from .base.base_solver import BaseSolver
from .base.base_parameters import BaseParameters
from .base.base_results import BaseResults

__all__ = [
    'BaseOptimizationModel',
    'BaseSolver', 
    'BaseParameters',
    'BaseResults'
] 