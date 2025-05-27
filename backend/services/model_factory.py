"""
Model Factory for Dynamic Model Creation

This factory creates optimization model instances based on model type and configuration.
It supports dynamic loading of models and provides a unified interface for model creation.
"""

import json
import os
from typing import Dict, List, Optional, Type, Any
from pathlib import Path

from ..models.base.base_model import BaseOptimizationModel


class ModelFactory:
    """
    Factory class for creating optimization model instances.
    
    This factory dynamically loads model configurations and creates appropriate
    model instances based on the model type.
    """
    
    def __init__(self, config_dir: str = None):
        """
        Initialize the model factory.
        
        Args:
            config_dir: Directory containing model configuration files
        """
        if config_dir is None:
            # Default to backend/config/models/
            current_dir = Path(__file__).parent.parent
            config_dir = current_dir / "config" / "models"
        
        self.config_dir = Path(config_dir)
        self._model_configs = {}
        self._model_classes = {}
        self._load_model_configs()
        self._register_model_classes()
    
    def _load_model_configs(self):
        """Load all model configuration files."""
        if not self.config_dir.exists():
            print(f"Warning: Model config directory {self.config_dir} does not exist")
            return
        
        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                model_type = config.get('type')
                if model_type:
                    self._model_configs[model_type] = config
                    print(f"Loaded config for model type: {model_type}")
                else:
                    print(f"Warning: No 'type' field in config file {config_file}")
                    
            except Exception as e:
                print(f"Error loading config file {config_file}: {e}")
    
    def _register_model_classes(self):
        """Register available model classes."""
        # Import and register VRP model
        try:
            from ..models.vrp.vrp_model import VRPModel
            self._model_classes['vrp'] = VRPModel
            print("Registered VRP model class")
        except ImportError as e:
            print(f"VRP model not available: {e}")
        
        # Import and register Inventory model
        try:
            from ..models.inventory.inventory_model import InventoryModel
            self._model_classes['inventory'] = InventoryModel
            print("Registered Inventory model class")
        except ImportError as e:
            print(f"Inventory model not available: {e}")
        
        # Import and register Scheduling model
        try:
            from ..models.scheduling.scheduling_model import SchedulingModel
            self._model_classes['scheduling'] = SchedulingModel
            print("Registered Scheduling model class")
        except ImportError as e:
            print(f"Scheduling model not available: {e}")
        
        # Import and register Network Flow model
        try:
            from ..models.network_flow.network_flow_model import NetworkFlowModel
            self._model_classes['network_flow'] = NetworkFlowModel
            print("Registered Network Flow model class")
        except ImportError as e:
            print(f"Network Flow model not available: {e}")
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """
        Get list of available optimization models.
        
        Returns:
            List of dictionaries with model information
        """
        available_models = []
        
        for model_type, config in self._model_configs.items():
            if model_type in self._model_classes:
                available_models.append({
                    'type': model_type,
                    'name': config.get('name', model_type.title()),
                    'description': config.get('description', ''),
                    'icon': config.get('icon', '🔧'),
                    'available': True
                })
            else:
                available_models.append({
                    'type': model_type,
                    'name': config.get('name', model_type.title()),
                    'description': config.get('description', ''),
                    'icon': config.get('icon', '🔧'),
                    'available': False,
                    'reason': 'Model class not implemented'
                })
        
        return available_models
    
    def get_model_config(self, model_type: str) -> Optional[Dict]:
        """
        Get configuration for a specific model type.
        
        Args:
            model_type: Type of model (e.g., 'vrp', 'inventory')
            
        Returns:
            Model configuration dictionary or None if not found
        """
        return self._model_configs.get(model_type)
    
    def create_model(self, model_type: str) -> Optional[BaseOptimizationModel]:
        """
        Create an instance of the specified model type.
        
        Args:
            model_type: Type of model to create (e.g., 'vrp', 'inventory')
            
        Returns:
            Model instance or None if model type not available
        """
        # Check if model type is available
        if model_type not in self._model_configs:
            raise ValueError(f"Model type '{model_type}' not found in configurations")
        
        if model_type not in self._model_classes:
            raise ValueError(f"Model class for '{model_type}' not registered")
        
        # Get configuration and model class
        config = self._model_configs[model_type]
        model_class = self._model_classes[model_type]
        
        # Create and return model instance
        try:
            model_instance = model_class(config)
            print(f"Created {model_type} model instance")
            return model_instance
        except Exception as e:
            raise RuntimeError(f"Failed to create {model_type} model: {e}")
    
    def is_model_available(self, model_type: str) -> bool:
        """
        Check if a model type is available.
        
        Args:
            model_type: Type of model to check
            
        Returns:
            True if model is available, False otherwise
        """
        return (model_type in self._model_configs and 
                model_type in self._model_classes)
    
    def get_model_info(self, model_type: str) -> Optional[Dict]:
        """
        Get comprehensive information about a model type.
        
        Args:
            model_type: Type of model
            
        Returns:
            Dictionary with model information
        """
        if model_type not in self._model_configs:
            return None
        
        config = self._model_configs[model_type]
        available = model_type in self._model_classes
        
        return {
            'type': model_type,
            'name': config.get('name', ''),
            'description': config.get('description', ''),
            'icon': config.get('icon', '🔧'),
            'available': available,
            'parameter_count': len(config.get('parameters', {})),
            'kpi_count': len(config.get('kpis', [])),
            'result_tabs': len(config.get('result_tabs', [])),
            'data_requirements': config.get('data_requirements', {}),
            'comparison_metrics': config.get('comparison_metrics', [])
        }
    
    def validate_model_config(self, model_type: str) -> Dict[str, Any]:
        """
        Validate a model configuration.
        
        Args:
            model_type: Type of model to validate
            
        Returns:
            Validation results
        """
        if model_type not in self._model_configs:
            return {
                'valid': False,
                'errors': [f"Model type '{model_type}' not found"]
            }
        
        config = self._model_configs[model_type]
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ['type', 'name', 'description', 'parameters']
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Check parameters structure
        if 'parameters' in config:
            for param_name, param_config in config['parameters'].items():
                if 'type' not in param_config:
                    errors.append(f"Parameter '{param_name}' missing type")
                if 'label' not in param_config:
                    warnings.append(f"Parameter '{param_name}' missing label")
        
        # Check KPIs structure
        if 'kpis' in config:
            for i, kpi in enumerate(config['kpis']):
                if 'name' not in kpi:
                    errors.append(f"KPI {i} missing name")
                if 'label' not in kpi:
                    errors.append(f"KPI {i} missing label")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def reload_configs(self):
        """Reload all model configurations."""
        self._model_configs.clear()
        self._load_model_configs()
        print("Model configurations reloaded")


# Global factory instance
_factory_instance = None

def get_model_factory() -> ModelFactory:
    """
    Get the global model factory instance.
    
    Returns:
        ModelFactory instance
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = ModelFactory()
    return _factory_instance

def create_model(model_type: str) -> Optional[BaseOptimizationModel]:
    """
    Convenience function to create a model instance.
    
    Args:
        model_type: Type of model to create
        
    Returns:
        Model instance
    """
    factory = get_model_factory()
    return factory.create_model(model_type)

def get_available_models() -> List[Dict[str, str]]:
    """
    Convenience function to get available models.
    
    Returns:
        List of available models
    """
    factory = get_model_factory()
    return factory.get_available_models() 