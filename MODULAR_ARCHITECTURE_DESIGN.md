# Modular Architecture Design for Multi-Model OR SaaS

## 🎯 **Objective**
Design a clean, modular architecture that allows easy integration of new optimization models (Inventory, Scheduling, Network Flow) with minimal code changes and maximum reusability.

## 🏗️ **Core Architecture Principles**

### 1. **Model-Agnostic Framework**
- Abstract base classes for all optimization models
- Standardized interfaces for parameters, constraints, and results
- Pluggable solver architecture
- Unified UI components with model-specific configurations

### 2. **Configuration-Driven Development**
- Model definitions in JSON/YAML configuration files
- Parameter schemas for automatic UI generation
- KPI definitions for results display
- Comparison metrics configuration

### 3. **Separation of Concerns**
- **Frontend**: Model-agnostic UI components
- **Backend**: Model-specific solvers and logic
- **Configuration**: Model definitions and schemas
- **Data**: Unified data management layer

## 📁 **Proposed Directory Structure**

```
or_saas_app/
├── backend/
│   ├── core/                          # Django core (unchanged)
│   ├── orsaas_backend/               # Django settings (unchanged)
│   ├── models/                       # Model-specific implementations
│   │   ├── __init__.py
│   │   ├── base/                     # Abstract base classes
│   │   │   ├── __init__.py
│   │   │   ├── base_model.py         # Abstract optimization model
│   │   │   ├── base_solver.py        # Abstract solver interface
│   │   │   ├── base_parameters.py    # Parameter validation
│   │   │   └── base_results.py       # Results processing
│   │   ├── vrp/                      # Vehicle Routing Problem
│   │   │   ├── __init__.py
│   │   │   ├── vrp_model.py          # VRP-specific implementation
│   │   │   ├── vrp_solver.py         # VRP solver (existing, refactored)
│   │   │   ├── vrp_parameters.py     # VRP parameter definitions
│   │   │   ├── vrp_constraints.py    # VRP constraint handling
│   │   │   └── vrp_kpis.py           # VRP KPI calculations
│   │   ├── inventory/                # Inventory Optimization (NEW)
│   │   │   ├── __init__.py
│   │   │   ├── inventory_model.py
│   │   │   ├── inventory_solver.py
│   │   │   ├── inventory_parameters.py
│   │   │   ├── inventory_constraints.py
│   │   │   └── inventory_kpis.py
│   │   ├── scheduling/               # Scheduling (FUTURE)
│   │   └── network_flow/             # Network Flow (FUTURE)
│   ├── config/                       # Model configurations
│   │   ├── models/
│   │   │   ├── vrp_config.json       # VRP model definition
│   │   │   ├── inventory_config.json # Inventory model definition
│   │   │   └── scheduling_config.json
│   │   └── schemas/
│   │       ├── parameter_schema.json # Parameter validation schemas
│   │       └── result_schema.json    # Result format schemas
│   ├── services/                     # Business logic services
│   │   ├── model_factory.py          # Factory for creating model instances
│   │   ├── solver_registry.py        # Registry of available solvers
│   │   ├── parameter_validator.py    # Parameter validation service
│   │   └── result_processor.py       # Result processing service
│   └── utils/                        # Utility functions
├── frontend/
│   ├── main.py                       # Main app (refactored)
│   ├── pages/                        # Model-agnostic pages
│   │   ├── __init__.py
│   │   ├── home.py
│   │   ├── data_manager.py           # Universal data manager
│   │   ├── snapshots.py              # Universal snapshots
│   │   ├── scenario_builder.py       # Dynamic scenario builder
│   │   ├── view_results.py           # Dynamic results viewer
│   │   └── compare_outputs.py        # Universal comparison
│   ├── components/                   # Reusable UI components
│   │   ├── parameter_widgets.py      # Dynamic parameter inputs
│   │   ├── results_display.py        # Dynamic results display
│   │   ├── kpi_dashboard.py          # KPI visualization
│   │   └── comparison_charts.py      # Comparison visualizations
│   ├── config/                       # Frontend configurations
│   │   └── ui_config.json            # UI layout configurations
│   └── utils/
│       ├── model_loader.py           # Load model configurations
│       └── dynamic_ui.py             # Dynamic UI generation
└── config/                           # Global configurations
    ├── models.yaml                   # Available models registry
    └── app_config.yaml               # Application settings
```

## 🔧 **Implementation Strategy**

### **Phase 1: Refactor VRP to Modular Architecture**

#### 1.1 Create Base Classes
```python
# backend/models/base/base_model.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class BaseOptimizationModel(ABC):
    def __init__(self, model_config: Dict):
        self.model_config = model_config
        self.model_type = model_config['type']
        self.parameters = {}
        self.constraints = []
        self.results = {}
    
    @abstractmethod
    def validate_parameters(self, params: Dict) -> bool:
        pass
    
    @abstractmethod
    def validate_data(self, data: Any) -> bool:
        pass
    
    @abstractmethod
    def solve(self, data: Any, params: Dict, constraints: List) -> Dict:
        pass
    
    @abstractmethod
    def calculate_kpis(self, solution: Dict) -> Dict:
        pass
    
    @abstractmethod
    def get_comparison_metrics(self, solution: Dict) -> Dict:
        pass
```

#### 1.2 Create Model Configuration Files
```json
// backend/config/models/vrp_config.json
{
  "type": "vrp",
  "name": "Vehicle Routing Problem",
  "description": "Optimize vehicle routes for delivery/pickup operations",
  "icon": "🚛",
  "parameters": {
    "capacity": {
      "type": "float",
      "label": "Vehicle Capacity",
      "min": 0.01,
      "default": 100.0,
      "help": "Maximum capacity per vehicle"
    },
    "vehicle_count": {
      "type": "integer",
      "label": "Available Vehicles",
      "min": 1,
      "default": 3,
      "help": "Number of available vehicles"
    },
    "max_distance": {
      "type": "float",
      "label": "Max Route Distance",
      "min": 0,
      "default": 1000,
      "help": "Maximum distance per route"
    }
  },
  "data_requirements": {
    "required_columns": ["x", "y"],
    "optional_columns": ["demand", "time_window_start", "time_window_end"],
    "data_format": "coordinates_or_distance_matrix"
  },
  "kpis": [
    {
      "name": "total_distance",
      "label": "Total Distance",
      "type": "numeric",
      "format": "%.2f",
      "unit": "units"
    },
    {
      "name": "vehicle_utilization",
      "label": "Vehicle Utilization",
      "type": "percentage",
      "format": "%.1f%%"
    }
  ],
  "comparison_metrics": [
    "total_distance",
    "vehicles_used",
    "avg_route_distance",
    "customer_coverage"
  ],
  "result_tabs": [
    {
      "name": "routes",
      "label": "Route Details",
      "type": "table",
      "columns": ["vehicle", "route", "distance", "customers"]
    },
    {
      "name": "map",
      "label": "Route Map",
      "type": "map",
      "visualization": "route_overlay"
    }
  ]
}
```

#### 1.3 Create Dynamic UI Components
```python
# frontend/components/parameter_widgets.py
import streamlit as st
from typing import Dict, Any

def render_parameter_widget(param_name: str, param_config: Dict) -> Any:
    """Dynamically render parameter input widget based on configuration"""
    param_type = param_config['type']
    label = param_config['label']
    help_text = param_config.get('help', '')
    default = param_config.get('default')
    
    if param_type == 'float':
        return st.number_input(
            label,
            min_value=param_config.get('min', 0.0),
            max_value=param_config.get('max', float('inf')),
            value=default,
            step=param_config.get('step', 0.1),
            help=help_text,
            key=f"param_{param_name}"
        )
    elif param_type == 'integer':
        return st.number_input(
            label,
            min_value=param_config.get('min', 0),
            max_value=param_config.get('max', 1000),
            value=default,
            step=1,
            help=help_text,
            key=f"param_{param_name}"
        )
    elif param_type == 'boolean':
        return st.checkbox(
            label,
            value=default,
            help=help_text,
            key=f"param_{param_name}"
        )
    elif param_type == 'select':
        return st.selectbox(
            label,
            options=param_config['options'],
            index=param_config.get('default_index', 0),
            help=help_text,
            key=f"param_{param_name}"
        )
```

### **Phase 2: Add Inventory Optimization Model**

#### 2.1 Create Inventory Model Configuration
```json
// backend/config/models/inventory_config.json
{
  "type": "inventory",
  "name": "Inventory Optimization",
  "description": "Optimize inventory levels and ordering policies",
  "icon": "📦",
  "parameters": {
    "holding_cost": {
      "type": "float",
      "label": "Holding Cost per Unit",
      "min": 0.01,
      "default": 1.0,
      "help": "Cost to hold one unit in inventory per period"
    },
    "ordering_cost": {
      "type": "float",
      "label": "Ordering Cost",
      "min": 0.01,
      "default": 50.0,
      "help": "Fixed cost per order"
    },
    "demand_forecast": {
      "type": "select",
      "label": "Demand Forecast Method",
      "options": ["constant", "linear_trend", "seasonal"],
      "default_index": 0,
      "help": "Method for forecasting demand"
    },
    "service_level": {
      "type": "float",
      "label": "Service Level",
      "min": 0.5,
      "max": 0.99,
      "default": 0.95,
      "help": "Target service level (probability of not stocking out)"
    }
  },
  "data_requirements": {
    "required_columns": ["item_id", "demand", "cost"],
    "optional_columns": ["lead_time", "supplier", "category"],
    "data_format": "item_demand_history"
  },
  "kpis": [
    {
      "name": "total_cost",
      "label": "Total Cost",
      "type": "currency",
      "format": "$%.2f"
    },
    {
      "name": "service_level_achieved",
      "label": "Service Level Achieved",
      "type": "percentage",
      "format": "%.1f%%"
    },
    {
      "name": "inventory_turnover",
      "label": "Inventory Turnover",
      "type": "numeric",
      "format": "%.2f"
    }
  ],
  "comparison_metrics": [
    "total_cost",
    "holding_cost",
    "ordering_cost",
    "stockout_probability"
  ],
  "result_tabs": [
    {
      "name": "policy",
      "label": "Ordering Policy",
      "type": "table",
      "columns": ["item", "reorder_point", "order_quantity", "safety_stock"]
    },
    {
      "name": "forecast",
      "label": "Demand Forecast",
      "type": "chart",
      "visualization": "time_series"
    },
    {
      "name": "costs",
      "label": "Cost Breakdown",
      "type": "chart",
      "visualization": "pie_chart"
    }
  ]
}
```

#### 2.2 Implement Inventory Solver
```python
# backend/models/inventory/inventory_solver.py
from ..base.base_model import BaseOptimizationModel
import numpy as np
from scipy import stats
import pandas as pd

class InventoryOptimizationModel(BaseOptimizationModel):
    def __init__(self, model_config):
        super().__init__(model_config)
    
    def validate_parameters(self, params: Dict) -> bool:
        required = ['holding_cost', 'ordering_cost', 'service_level']
        return all(param in params for param in required)
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        required_cols = ['item_id', 'demand', 'cost']
        return all(col in data.columns for col in required_cols)
    
    def solve(self, data: pd.DataFrame, params: Dict, constraints: List) -> Dict:
        """Solve inventory optimization using EOQ and safety stock models"""
        results = []
        
        for _, item in data.iterrows():
            # Calculate EOQ (Economic Order Quantity)
            annual_demand = item['demand'] * 12  # Assuming monthly data
            holding_cost = params['holding_cost']
            ordering_cost = params['ordering_cost']
            
            eoq = np.sqrt(2 * annual_demand * ordering_cost / holding_cost)
            
            # Calculate safety stock
            service_level = params['service_level']
            lead_time = item.get('lead_time', 1)  # Default 1 period
            demand_std = data[data['item_id'] == item['item_id']]['demand'].std()
            
            z_score = stats.norm.ppf(service_level)
            safety_stock = z_score * demand_std * np.sqrt(lead_time)
            
            # Calculate reorder point
            avg_demand = item['demand']
            reorder_point = avg_demand * lead_time + safety_stock
            
            results.append({
                'item_id': item['item_id'],
                'eoq': eoq,
                'safety_stock': safety_stock,
                'reorder_point': reorder_point,
                'annual_demand': annual_demand,
                'total_cost': self._calculate_total_cost(eoq, annual_demand, holding_cost, ordering_cost, safety_stock)
            })
        
        return {
            'status': 'optimal',
            'items': results,
            'summary': self._calculate_summary(results)
        }
    
    def calculate_kpis(self, solution: Dict) -> Dict:
        items = solution['items']
        total_cost = sum(item['total_cost'] for item in items)
        avg_service_level = self.parameters.get('service_level', 0.95)
        
        return {
            'total_cost': total_cost,
            'service_level_achieved': avg_service_level * 100,
            'inventory_turnover': sum(item['annual_demand'] for item in items) / sum(item['eoq'] for item in items),
            'items_optimized': len(items)
        }
    
    def get_comparison_metrics(self, solution: Dict) -> Dict:
        kpis = self.calculate_kpis(solution)
        return {
            'total_cost': kpis['total_cost'],
            'holding_cost': sum(item['eoq'] * self.parameters['holding_cost'] / 2 for item in solution['items']),
            'ordering_cost': sum(item['annual_demand'] / item['eoq'] * self.parameters['ordering_cost'] for item in solution['items']),
            'stockout_probability': (1 - self.parameters['service_level']) * 100
        }
```

### **Phase 3: Create Universal Frontend Components**

#### 3.1 Dynamic Scenario Builder
```python
# frontend/pages/scenario_builder.py
import streamlit as st
from utils.model_loader import load_model_config
from components.parameter_widgets import render_parameter_widget

def show_scenario_builder(model_type: str):
    """Universal scenario builder that adapts to any model type"""
    
    # Load model configuration
    model_config = load_model_config(model_type)
    
    st.title(f"{model_config['icon']} {model_config['name']} - Scenario Builder")
    st.write(model_config['description'])
    
    # Snapshot selection (universal)
    snapshots = get_snapshots()  # Universal function
    selected_snapshot = st.selectbox("Select Snapshot", snapshots)
    
    # Scenario name
    scenario_name = st.text_input("Scenario Name")
    
    # Dynamic parameter inputs
    st.subheader("Parameters")
    parameters = {}
    
    # Organize parameters in columns
    param_items = list(model_config['parameters'].items())
    cols = st.columns(min(3, len(param_items)))
    
    for i, (param_name, param_config) in enumerate(param_items):
        with cols[i % len(cols)]:
            parameters[param_name] = render_parameter_widget(param_name, param_config)
    
    # Constraints (universal)
    st.subheader("Constraints")
    constraints_text = st.text_area(
        "Describe any custom constraints (optional)",
        help="Enter constraints in natural language"
    )
    
    # Create scenario button
    if st.button("Create Scenario", type="primary"):
        create_scenario(model_type, scenario_name, selected_snapshot, parameters, constraints_text)
```

#### 3.2 Dynamic Results Viewer
```python
# frontend/pages/view_results.py
import streamlit as st
from utils.model_loader import load_model_config
from components.results_display import render_results_tab

def show_results(model_type: str, scenario_id: str):
    """Universal results viewer that adapts to any model type"""
    
    model_config = load_model_config(model_type)
    solution = load_solution(scenario_id)
    
    st.title(f"📊 {model_config['name']} Results")
    
    # KPI Dashboard (universal)
    render_kpi_dashboard(model_config['kpis'], solution)
    
    # Dynamic result tabs
    tab_configs = model_config['result_tabs']
    tab_names = [tab['label'] for tab in tab_configs]
    tabs = st.tabs(tab_names)
    
    for i, (tab, tab_config) in enumerate(zip(tabs, tab_configs)):
        with tab:
            render_results_tab(tab_config, solution)
```

## 📋 **Files to Modify for New Model Integration**

### **Required Files (Must Create/Modify)**

1. **Model Configuration**
   - `backend/config/models/{model_name}_config.json` ✨ **NEW**
   - `config/models.yaml` (add model to registry) ✨ **NEW**

2. **Model Implementation**
   - `backend/models/{model_name}/` (entire directory) ✨ **NEW**
   - `backend/models/{model_name}/{model_name}_model.py` ✨ **NEW**
   - `backend/models/{model_name}/{model_name}_solver.py` ✨ **NEW**
   - `backend/models/{model_name}/{model_name}_parameters.py` ✨ **NEW**
   - `backend/models/{model_name}/{model_name}_kpis.py` ✨ **NEW**

3. **Service Registration**
   - `backend/services/model_factory.py` (add model to factory) 📝 **MODIFY**
   - `backend/services/solver_registry.py` (register solver) 📝 **MODIFY**

### **Optional Files (For Advanced Features)**

4. **Custom UI Components** (if needed)
   - `frontend/components/{model_name}_widgets.py` ✨ **NEW**
   - `frontend/components/{model_name}_charts.py` ✨ **NEW**

5. **Custom Constraint Handling** (if needed)
   - `backend/models/{model_name}/{model_name}_constraints.py` ✨ **NEW**

### **No Changes Required**
- ✅ `frontend/main.py` (uses dynamic model loading)
- ✅ `frontend/pages/data_manager.py` (universal)
- ✅ `frontend/pages/snapshots.py` (universal)
- ✅ `frontend/pages/scenario_builder.py` (dynamic)
- ✅ `frontend/pages/view_results.py` (dynamic)
- ✅ `frontend/pages/compare_outputs.py` (universal)
- ✅ Database models (universal)
- ✅ Core Django functionality

## 🎯 **Benefits of This Architecture**

### **For Developers**
- **Minimal Code Changes**: Only 2-3 files need modification for new models
- **Consistent Interface**: All models follow the same patterns
- **Reusable Components**: UI components work across all models
- **Easy Testing**: Each model is independently testable

### **For Users**
- **Consistent Experience**: Same workflow across all optimization models
- **Familiar Interface**: Once you learn one model, you know them all
- **Easy Comparison**: Standardized metrics across models

### **For Maintenance**
- **Separation of Concerns**: Model logic separate from UI logic
- **Configuration-Driven**: Changes via config files, not code
- **Extensible**: Easy to add new parameter types, KPIs, visualizations

## 🚀 **Implementation Timeline**

### **Week 1-2: Foundation**
- Create base classes and interfaces
- Refactor VRP to use new architecture
- Create model configuration system

### **Week 3: Inventory Model**
- Implement inventory optimization model
- Create inventory-specific solver
- Test with sample data

### **Week 4: Integration & Testing**
- Integrate inventory model into UI
- Test end-to-end workflow
- Performance optimization

### **Future: Additional Models**
- Scheduling optimization (Week 5-6)
- Network flow optimization (Week 7-8)
- Advanced features and optimizations

This architecture ensures that adding new models like inventory optimization becomes a **configuration and implementation task** rather than a **refactoring task**, making the process stable, predictable, and bug-free. 