"""
Inventory Optimization Solver

This module implements various inventory optimization algorithms including:
- Economic Order Quantity (EOQ)
- Safety Stock Optimization
- Reorder Point Calculation
- ABC Analysis
- Inventory Turnover Optimization
- Multi-item Inventory Optimization with Budget Constraints
"""

import numpy as np
import pandas as pd
from scipy import stats, optimize
from typing import Dict, List, Any, Tuple
import warnings
warnings.filterwarnings('ignore')


class InventoryOptimizationSolver:
    """
    Advanced inventory optimization solver implementing multiple algorithms.
    """
    
    def __init__(self, solver_config: Dict = None):
        """Initialize the inventory solver."""
        self.solver_config = solver_config or {}
        self.solver_name = "Advanced Inventory Optimizer"
        
    def solve_inventory_optimization(self, data: pd.DataFrame, parameters: Dict) -> Dict[str, Any]:
        """
        Main solver method for inventory optimization.
        
        Args:
            data: DataFrame with inventory data
            parameters: Optimization parameters
            
        Returns:
            Complete solution dictionary
        """
        try:
            # Extract parameters
            holding_cost_rate = parameters.get('holding_cost', 0.2)  # 20% annual holding cost
            ordering_cost = parameters.get('ordering_cost', 50.0)
            service_level = parameters.get('service_level', 0.95)
            lead_time_default = parameters.get('lead_time', 7)
            review_period = parameters.get('review_period', 30)
            stockout_cost = parameters.get('stockout_cost', 10.0)
            max_inventory_value = parameters.get('max_inventory_value', float('inf'))
            demand_forecast_method = parameters.get('demand_forecast', 'constant')
            
            # Prepare data
            processed_data = self._prepare_data(data, lead_time_default)
            
            # Perform ABC Analysis
            abc_analysis = self._perform_abc_analysis(processed_data)
            
            # Calculate demand statistics
            demand_stats = self._calculate_demand_statistics(processed_data, demand_forecast_method)
            
            # Optimize inventory policies for each item
            optimization_results = []
            total_inventory_value = 0
            
            for idx, item in processed_data.iterrows():
                item_id = item['item_id']
                
                # Get demand statistics for this item
                item_stats = demand_stats[demand_stats['item_id'] == item_id].iloc[0]
                
                # Calculate optimal policy
                policy = self._optimize_item_policy(
                    item, item_stats, holding_cost_rate, ordering_cost, 
                    service_level, stockout_cost, abc_analysis.get(item_id, 'C')
                )
                
                optimization_results.append(policy)
                total_inventory_value += policy['average_inventory'] * item['cost']
            
            # Apply budget constraint if specified
            if total_inventory_value > max_inventory_value:
                optimization_results = self._apply_budget_constraint(
                    optimization_results, max_inventory_value, processed_data
                )
                total_inventory_value = sum(
                    result['average_inventory'] * processed_data[processed_data['item_id'] == result['item_id']]['cost'].iloc[0]
                    for result in optimization_results
                )
            
            # Calculate aggregate KPIs
            total_annual_cost = sum(result['total_annual_cost'] for result in optimization_results)
            total_holding_cost = sum(result['annual_holding_cost'] for result in optimization_results)
            total_ordering_cost = sum(result['annual_ordering_cost'] for result in optimization_results)
            total_stockout_cost = sum(result['annual_stockout_cost'] for result in optimization_results)
            
            # Calculate inventory turnover
            total_annual_demand = sum(result['annual_demand'] for result in optimization_results)
            average_inventory = sum(result['average_inventory'] for result in optimization_results)
            inventory_turnover = total_annual_demand / average_inventory if average_inventory > 0 else 0
            
            # Calculate service level achieved
            weighted_service_level = sum(
                result['service_level_achieved'] * result['annual_demand'] 
                for result in optimization_results
            ) / total_annual_demand if total_annual_demand > 0 else service_level
            
            # Prepare solution
            solution = {
                'status': 'optimal',
                'solver_info': {
                    'solver_name': self.solver_name,
                    'algorithm': 'Multi-objective Inventory Optimization',
                    'items_optimized': len(optimization_results)
                },
                'optimization_results': optimization_results,
                'aggregate_kpis': {
                    'total_annual_cost': round(total_annual_cost, 2),
                    'total_holding_cost': round(total_holding_cost, 2),
                    'total_ordering_cost': round(total_ordering_cost, 2),
                    'total_stockout_cost': round(total_stockout_cost, 2),
                    'total_inventory_value': round(total_inventory_value, 2),
                    'inventory_turnover': round(inventory_turnover, 2),
                    'service_level_achieved': round(weighted_service_level * 100, 1),
                    'items_optimized': len(optimization_results),
                    'avg_order_frequency': round(
                        sum(result['order_frequency'] for result in optimization_results) / len(optimization_results), 1
                    )
                },
                'abc_analysis': abc_analysis,
                'demand_forecast': demand_stats.to_dict('records'),
                'cost_breakdown': {
                    'holding_cost_percentage': round((total_holding_cost / total_annual_cost) * 100, 1) if total_annual_cost > 0 else 0,
                    'ordering_cost_percentage': round((total_ordering_cost / total_annual_cost) * 100, 1) if total_annual_cost > 0 else 0,
                    'stockout_cost_percentage': round((total_stockout_cost / total_annual_cost) * 100, 1) if total_annual_cost > 0 else 0
                }
            }
            
            return solution
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'solver_info': {
                    'solver_name': self.solver_name,
                    'error_details': str(e)
                }
            }
    
    def _prepare_data(self, data: pd.DataFrame, lead_time_default: int) -> pd.DataFrame:
        """Prepare and validate inventory data."""
        processed_data = data.copy()
        
        # Ensure required columns exist
        if 'lead_time' not in processed_data.columns:
            processed_data['lead_time'] = lead_time_default
        
        if 'category' not in processed_data.columns:
            processed_data['category'] = 'General'
        
        if 'supplier' not in processed_data.columns:
            processed_data['supplier'] = 'Default'
        
        # Convert demand to annual if it's not already
        if 'demand_period' in processed_data.columns:
            period_multiplier = {
                'daily': 365,
                'weekly': 52,
                'monthly': 12,
                'quarterly': 4,
                'annual': 1
            }
            multiplier = period_multiplier.get(processed_data['demand_period'].iloc[0], 12)  # Default to monthly
            processed_data['annual_demand'] = processed_data['demand'] * multiplier
        else:
            processed_data['annual_demand'] = processed_data['demand'] * 12  # Assume monthly demand
        
        return processed_data
    
    def _perform_abc_analysis(self, data: pd.DataFrame) -> Dict[str, str]:
        """Perform ABC analysis based on annual demand value."""
        data_with_value = data.copy()
        data_with_value['annual_value'] = data_with_value['annual_demand'] * data_with_value['cost']
        data_with_value = data_with_value.sort_values('annual_value', ascending=False)
        
        total_value = data_with_value['annual_value'].sum()
        cumulative_percentage = (data_with_value['annual_value'].cumsum() / total_value) * 100
        
        abc_classification = {}
        for idx, item_id in enumerate(data_with_value['item_id']):
            cum_pct = cumulative_percentage.iloc[idx]
            if cum_pct <= 80:
                abc_classification[item_id] = 'A'
            elif cum_pct <= 95:
                abc_classification[item_id] = 'B'
            else:
                abc_classification[item_id] = 'C'
        
        return abc_classification
    
    def _calculate_demand_statistics(self, data: pd.DataFrame, forecast_method: str) -> pd.DataFrame:
        """Calculate demand statistics and forecasts."""
        demand_stats = []
        
        for _, item in data.iterrows():
            # For simplicity, we'll use the provided demand as mean and estimate variance
            annual_demand = item['annual_demand']
            
            # Estimate demand variability based on forecast method
            if forecast_method == 'constant':
                demand_std = annual_demand * 0.1  # 10% CV
            elif forecast_method == 'linear_trend':
                demand_std = annual_demand * 0.15  # 15% CV
            elif forecast_method == 'seasonal':
                demand_std = annual_demand * 0.25  # 25% CV
            else:  # moving_average
                demand_std = annual_demand * 0.2   # 20% CV
            
            demand_stats.append({
                'item_id': item['item_id'],
                'annual_demand_mean': annual_demand,
                'annual_demand_std': demand_std,
                'demand_cv': demand_std / annual_demand if annual_demand > 0 else 0,
                'forecast_method': forecast_method
            })
        
        return pd.DataFrame(demand_stats)
    
    def _optimize_item_policy(self, item: pd.Series, demand_stats: pd.Series, 
                            holding_cost_rate: float, ordering_cost: float,
                            service_level: float, stockout_cost: float, 
                            abc_class: str) -> Dict[str, Any]:
        """Optimize inventory policy for a single item."""
        
        # Extract item data
        item_id = item['item_id']
        unit_cost = item['cost']
        lead_time = item['lead_time']
        annual_demand = demand_stats['annual_demand_mean']
        demand_std = demand_stats['annual_demand_std']
        
        # Calculate holding cost per unit per year
        holding_cost_per_unit = unit_cost * holding_cost_rate
        
        # Calculate EOQ (Economic Order Quantity)
        if annual_demand > 0 and holding_cost_per_unit > 0:
            eoq = np.sqrt(2 * annual_demand * ordering_cost / holding_cost_per_unit)
        else:
            eoq = 1
        
        # Adjust service level based on ABC classification
        adjusted_service_level = service_level
        if abc_class == 'A':
            adjusted_service_level = min(0.99, service_level + 0.02)  # Higher service for A items
        elif abc_class == 'C':
            adjusted_service_level = max(0.85, service_level - 0.05)  # Lower service for C items
        
        # Calculate safety stock
        z_score = stats.norm.ppf(adjusted_service_level)
        lead_time_demand_std = demand_std * np.sqrt(lead_time / 365)  # Convert to lead time period
        safety_stock = z_score * lead_time_demand_std
        
        # Calculate reorder point
        average_lead_time_demand = annual_demand * (lead_time / 365)
        reorder_point = average_lead_time_demand + safety_stock
        
        # Calculate maximum inventory level (for periodic review)
        max_inventory = reorder_point + eoq
        
        # Calculate costs
        order_frequency = annual_demand / eoq if eoq > 0 else 0
        annual_ordering_cost = order_frequency * ordering_cost
        average_inventory = (eoq / 2) + safety_stock
        annual_holding_cost = average_inventory * holding_cost_per_unit
        
        # Calculate stockout cost (simplified)
        stockout_probability = 1 - adjusted_service_level
        expected_stockout_quantity = stockout_probability * demand_std * np.sqrt(lead_time / 365)
        annual_stockout_cost = expected_stockout_quantity * stockout_cost * order_frequency
        
        total_annual_cost = annual_ordering_cost + annual_holding_cost + annual_stockout_cost
        
        return {
            'item_id': item_id,
            'eoq': round(eoq, 0),
            'safety_stock': round(safety_stock, 0),
            'reorder_point': round(reorder_point, 0),
            'max_inventory': round(max_inventory, 0),
            'average_inventory': round(average_inventory, 1),
            'order_frequency': round(order_frequency, 1),
            'annual_demand': round(annual_demand, 0),
            'annual_ordering_cost': round(annual_ordering_cost, 2),
            'annual_holding_cost': round(annual_holding_cost, 2),
            'annual_stockout_cost': round(annual_stockout_cost, 2),
            'total_annual_cost': round(total_annual_cost, 2),
            'service_level_achieved': adjusted_service_level,
            'abc_class': abc_class,
            'unit_cost': unit_cost,
            'inventory_value': round(average_inventory * unit_cost, 2)
        }
    
    def _apply_budget_constraint(self, optimization_results: List[Dict], 
                               max_inventory_value: float, 
                               data: pd.DataFrame) -> List[Dict]:
        """Apply budget constraint by adjusting inventory levels."""
        
        # Sort items by ABC class and cost efficiency
        results_df = pd.DataFrame(optimization_results)
        results_df['cost_efficiency'] = results_df['total_annual_cost'] / results_df['inventory_value']
        results_df = results_df.sort_values(['abc_class', 'cost_efficiency'])
        
        # Reduce inventory levels starting with least efficient C items
        current_value = results_df['inventory_value'].sum()
        reduction_factor = max_inventory_value / current_value if current_value > 0 else 1
        
        if reduction_factor < 1:
            # Apply proportional reduction, but protect A items more
            for idx, result in results_df.iterrows():
                if result['abc_class'] == 'A':
                    factor = max(0.9, reduction_factor)  # Reduce A items by max 10%
                elif result['abc_class'] == 'B':
                    factor = max(0.8, reduction_factor)  # Reduce B items by max 20%
                else:  # C items
                    factor = reduction_factor  # C items bear most of the reduction
                
                # Adjust EOQ and recalculate costs
                new_eoq = result['eoq'] * factor
                new_average_inventory = (new_eoq / 2) + result['safety_stock']
                
                # Recalculate costs with new EOQ
                item_data = data[data['item_id'] == result['item_id']].iloc[0]
                holding_cost_per_unit = item_data['cost'] * 0.2  # Assuming 20% holding cost
                
                new_order_frequency = result['annual_demand'] / new_eoq if new_eoq > 0 else 0
                new_annual_ordering_cost = new_order_frequency * 50  # Assuming $50 ordering cost
                new_annual_holding_cost = new_average_inventory * holding_cost_per_unit
                
                # Update the result
                results_df.loc[idx, 'eoq'] = round(new_eoq, 0)
                results_df.loc[idx, 'average_inventory'] = round(new_average_inventory, 1)
                results_df.loc[idx, 'order_frequency'] = round(new_order_frequency, 1)
                results_df.loc[idx, 'annual_ordering_cost'] = round(new_annual_ordering_cost, 2)
                results_df.loc[idx, 'annual_holding_cost'] = round(new_annual_holding_cost, 2)
                results_df.loc[idx, 'total_annual_cost'] = round(
                    new_annual_ordering_cost + new_annual_holding_cost + result['annual_stockout_cost'], 2
                )
                results_df.loc[idx, 'inventory_value'] = round(new_average_inventory * item_data['cost'], 2)
        
        return results_df.to_dict('records') 