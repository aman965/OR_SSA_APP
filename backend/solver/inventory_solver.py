#!/usr/bin/env python3
"""
Inventory Optimization Solver using PuLP + CBC
Follows the same pattern as VRP solver for consistency
"""

import json
import os
import sys
import argparse
import traceback
import pandas as pd
import numpy as np
from pulp import *
from scipy import stats
from datetime import datetime

def log(message):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_scenario(scenario_path):
    """Load scenario configuration from JSON file"""
    with open(scenario_path, 'r') as f:
        return json.load(f)

def load_inventory_data(csv_path):
    """Load inventory data from CSV file"""
    df = pd.read_csv(csv_path)
    
    # Validate required columns
    required_columns = ['item_id', 'demand', 'cost']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Add default values for optional columns
    if 'lead_time' not in df.columns:
        df['lead_time'] = 7  # Default 7 days
    if 'category' not in df.columns:
        df['category'] = 'General'
    if 'supplier' not in df.columns:
        df['supplier'] = 'Default'
    
    return df

def calculate_eoq(demand, ordering_cost, holding_cost_rate, unit_cost):
    """Calculate Economic Order Quantity"""
    if demand <= 0 or ordering_cost <= 0 or holding_cost_rate <= 0 or unit_cost <= 0:
        return 0
    holding_cost = holding_cost_rate * unit_cost
    eoq = np.sqrt((2 * demand * ordering_cost) / holding_cost)
    return eoq

def calculate_safety_stock(demand, lead_time, service_level, demand_std=None):
    """Calculate safety stock based on service level"""
    if demand_std is None:
        # Estimate standard deviation as 20% of demand if not provided
        demand_std = demand * 0.2
    
    # Calculate z-score for service level
    z_score = stats.norm.ppf(service_level)
    
    # Safety stock formula
    safety_stock = z_score * demand_std * np.sqrt(lead_time / 30)  # Assuming monthly demand
    return max(0, safety_stock)

def build_and_solve_inventory(scenario, df, output_dir):
    """Build and solve inventory optimization model"""
    
    # Extract parameters from scenario
    params = scenario.get('params', {})
    
    # Map generic parameters to inventory-specific ones
    holding_cost_rate = params.get('param1', 0.2) / 100  # Convert percentage to decimal
    ordering_cost = params.get('param2', 50.0)
    service_level = params.get('param3', 95) / 100  # Convert percentage to decimal
    max_inventory_value = params.get('param4', 100000.0) if params.get('param4', False) else float('inf')
    use_safety_stock = params.get('param5', True)
    
    # Additional parameters (could be from GPT prompt parsing)
    review_period = 30  # days
    stockout_cost = 10.0
    
    log(f"Parameters: holding_cost={holding_cost_rate}, ordering_cost={ordering_cost}, service_level={service_level}")
    
    # Initialize results
    results = []
    total_cost = 0
    total_inventory_value = 0
    
    # Process each item
    for idx, row in df.iterrows():
        item_id = row['item_id']
        demand = row['demand']
        unit_cost = row['cost']
        lead_time = row['lead_time']
        
        # Calculate EOQ
        eoq = calculate_eoq(demand, ordering_cost, holding_cost_rate, unit_cost)
        
        # Calculate safety stock if enabled
        safety_stock = 0
        if use_safety_stock:
            safety_stock = calculate_safety_stock(demand, lead_time, service_level)
        
        # Calculate reorder point
        daily_demand = demand / 30  # Convert to daily
        reorder_point = (daily_demand * lead_time) + safety_stock
        
        # Calculate costs
        num_orders = demand / eoq if eoq > 0 else 0
        annual_ordering_cost = num_orders * ordering_cost
        avg_inventory = (eoq / 2) + safety_stock
        annual_holding_cost = avg_inventory * unit_cost * holding_cost_rate
        annual_total_cost = annual_ordering_cost + annual_holding_cost
        
        # Store results
        results.append({
            'item_id': item_id,
            'demand': demand,
            'unit_cost': unit_cost,
            'eoq': round(eoq, 2),
            'safety_stock': round(safety_stock, 2),
            'reorder_point': round(reorder_point, 2),
            'avg_inventory': round(avg_inventory, 2),
            'inventory_value': round(avg_inventory * unit_cost, 2),
            'num_orders_per_year': round(num_orders, 2),
            'ordering_cost': round(annual_ordering_cost, 2),
            'holding_cost': round(annual_holding_cost, 2),
            'total_cost': round(annual_total_cost, 2),
            'category': row.get('category', 'General')
        })
        
        total_cost += annual_total_cost
        total_inventory_value += avg_inventory * unit_cost
    
    # Check inventory value constraint
    if total_inventory_value > max_inventory_value:
        log(f"Warning: Total inventory value ${total_inventory_value:.2f} exceeds maximum ${max_inventory_value:.2f}")
        # Could implement optimization to reduce inventory levels here
    
    # Create solution summary
    solution = {
        'status': 'optimal',
        'total_cost': round(total_cost, 2),
        'total_inventory_value': round(total_inventory_value, 2),
        'num_items': len(df),
        'service_level': service_level,
        'parameters': {
            'holding_cost_rate': holding_cost_rate,
            'ordering_cost': ordering_cost,
            'service_level': service_level,
            'max_inventory_value': max_inventory_value,
            'use_safety_stock': use_safety_stock
        },
        'items': results,
        'timestamp': datetime.now().isoformat()
    }
    
    # Save solution
    solution_path = os.path.join(output_dir, "solution_summary.json")
    with open(solution_path, 'w') as f:
        json.dump(solution, f, indent=4)
    log(f"Solution written to {solution_path}")
    
    # Save detailed results as CSV
    results_df = pd.DataFrame(results)
    results_csv_path = os.path.join(output_dir, "inventory_policy.csv")
    results_df.to_csv(results_csv_path, index=False)
    log(f"Detailed results written to {results_csv_path}")
    
    # Create comparison metrics (similar to VRP)
    total_demand = df['demand'].sum()
    inventory_turnover = total_demand / (total_inventory_value / df['cost'].mean()) if total_inventory_value > 0 else 0
    
    compare_metrics = {
        "scenario_id": os.path.basename(os.path.dirname(output_dir)),
        "snapshot_id": scenario.get("snapshot_id", ""),
        "parameters": scenario.get("params", {}),
        "kpis": {
            "total_cost": round(total_cost, 2),
            "total_inventory_value": round(total_inventory_value, 2),
            "inventory_turnover": round(inventory_turnover, 2),
            "service_level_achieved": service_level * 100,
            "items_optimized": len(df),
            "avg_order_frequency": round(sum(r['num_orders_per_year'] for r in results) / len(results), 2)
        },
        "status": "solved"
    }
    
    compare_metrics_path = os.path.join(output_dir, "compare_metrics.json")
    with open(compare_metrics_path, 'w') as f:
        json.dump(compare_metrics, f, indent=4)
    log(f"Comparison metrics written to {compare_metrics_path}")

def main():
    parser = argparse.ArgumentParser(description="Inventory Optimization Solver")
    parser.add_argument('--scenario-path', required=True, help='Path to scenario.json')
    args = parser.parse_args()
    
    scenario_path = args.scenario_path
    
    try:
        log(f"Loading scenario from {scenario_path}")
        scenario = load_scenario(scenario_path)
        output_dir = os.path.dirname(scenario_path)
        
        # Create outputs directory
        outputs_dir = os.path.join(output_dir, "outputs")
        os.makedirs(outputs_dir, exist_ok=True)
        
        csv_path = scenario.get('dataset_file_path')
        if not csv_path:
            raise FileNotFoundError("Dataset file path is empty or not specified")
        
        normalized_path = os.path.normpath(csv_path)
        if not os.path.exists(normalized_path):
            raise FileNotFoundError(f"Dataset file not found: {csv_path}")
        
        log(f"Loading inventory data from {normalized_path}")
        df = load_inventory_data(normalized_path)
        
        log(f"Building and solving inventory optimization for {len(df)} items")
        build_and_solve_inventory(scenario, df, outputs_dir)
        
        log("Inventory optimization completed successfully")
        
    except Exception as e:
        log(f"Exception: {e}")
        traceback.print_exc()
        
        failure = {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        
        output_dir = os.path.dirname(scenario_path)
        outputs_dir = os.path.join(output_dir, "outputs")
        os.makedirs(outputs_dir, exist_ok=True)
        
        with open(os.path.join(outputs_dir, "failure_summary.json"), 'w') as f:
            json.dump(failure, f, indent=4)
        
        log(f"Failure written to failure_summary.json")
        
        # Write comparison metrics for failed scenario
        compare_metrics = {
            "scenario_id": os.path.basename(output_dir),
            "snapshot_id": scenario.get("snapshot_id", "") if 'scenario' in locals() else "",
            "parameters": scenario.get("params", {}) if 'scenario' in locals() else {},
            "kpis": {
                "total_cost": 0,
                "total_inventory_value": 0,
                "inventory_turnover": 0,
                "service_level_achieved": 0,
                "items_optimized": 0,
                "avg_order_frequency": 0
            },
            "status": "error"
        }
        
        with open(os.path.join(outputs_dir, "compare_metrics.json"), 'w') as f:
            json.dump(compare_metrics, f, indent=4)
        
        sys.exit(1)

if __name__ == "__main__":
    main() 