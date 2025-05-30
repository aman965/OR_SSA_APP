#!/usr/bin/env python3
"""
Enhanced Inventory Optimization Solver with Natural Language Constraint Parsing
Based on the standard inventory solver but with constraint parsing capabilities
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
import re

# Add current directory and parent to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

# Try to import the enhanced constraint parser
ENHANCED_PARSER_AVAILABLE = False
try:
    from inventory_constraint_parser import EnhancedInventoryConstraintParser, ParsedConstraint
    ENHANCED_PARSER_AVAILABLE = True
    print(f"[inventory_solver_enhanced] ✅ Successfully imported EnhancedInventoryConstraintParser")
except ImportError as e:
    print(f"[inventory_solver_enhanced] ❌ Could not import enhanced parser: {e}")

def log(message):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def parse_inventory_constraints(gpt_prompt, enhanced_parser=None):
    """Parse natural language constraints for inventory optimization"""
    constraints = []
    if not gpt_prompt or not gpt_prompt.strip():
        return constraints
    
    log(f"Parsing constraint prompt: {gpt_prompt}")
    
    # If enhanced parser is available, use it
    if enhanced_parser:
        log("Using enhanced constraint parser with LLM support")
        # Split prompt by common delimiters
        constraint_parts = re.split(r'[.;,]\s*(?=\w)', gpt_prompt)
        
        for part in constraint_parts:
            part = part.strip()
            if not part:
                continue
                
            try:
                parsed = enhanced_parser.parse_constraint(part)
                
                # Convert ParsedConstraint to our format
                constraint = {
                    'type': parsed.constraint_type,
                    'subtype': parsed.subtype,
                    'parameters': parsed.parameters,
                    'confidence': parsed.confidence,
                    'interpretation': parsed.interpretation,
                    'original': part,
                    'method': parsed.parsing_method
                }
                
                # Map constraint types to our format
                if parsed.constraint_type == 'safety_stock' and 'item_id' in parsed.parameters:
                    constraint['type'] = 'safety_stock_limit'
                    constraint['item_id'] = parsed.parameters.get('item_id')
                    constraint['operator'] = parsed.parameters.get('operator', '<=')
                    constraint['value'] = parsed.parameters.get('value', 0)
                elif parsed.constraint_type == 'eoq' and 'item_id' in parsed.parameters:
                    constraint['type'] = 'eoq_limit'
                    constraint['item_id'] = parsed.parameters.get('item_id')
                    constraint['operator'] = parsed.parameters.get('operator', '>=')
                    constraint['value'] = parsed.parameters.get('value', 0)
                elif parsed.constraint_type == 'inventory_value' and 'item_id' in parsed.parameters:
                    constraint['type'] = 'inventory_value_limit'
                    constraint['item_id'] = parsed.parameters.get('item_id')
                    constraint['operator'] = parsed.parameters.get('operator', '<=')
                    constraint['value'] = parsed.parameters.get('value', 0)
                elif parsed.constraint_type == 'category_constraint':
                    constraint['type'] = 'category_constraint'
                    constraint['category'] = parsed.parameters.get('category')
                    constraint['metric'] = parsed.parameters.get('metric')
                    constraint['operator'] = parsed.parameters.get('operator', '>=')
                    constraint['value'] = parsed.parameters.get('value', 0)
                elif parsed.constraint_type == 'supplier_constraint':
                    constraint['type'] = 'supplier_constraint'
                    constraint['supplier'] = parsed.parameters.get('supplier')
                    constraint['metric'] = parsed.parameters.get('metric')
                    constraint['operator'] = parsed.parameters.get('operator', '>=')
                    constraint['value'] = parsed.parameters.get('value', 0)
                elif parsed.constraint_type == 'service_level' and 'item_id' in parsed.parameters:
                    constraint['type'] = 'service_level_constraint'
                    constraint['item_id'] = parsed.parameters.get('item_id')
                    constraint['operator'] = parsed.parameters.get('operator', '>=')
                    constraint['value'] = parsed.parameters.get('value', 0.95)
                elif parsed.constraint_type == 'reorder_point' and 'item_id' in parsed.parameters:
                    constraint['type'] = 'reorder_point_constraint'
                    constraint['item_id'] = parsed.parameters.get('item_id')
                    constraint['operator'] = parsed.parameters.get('operator', '=')
                    constraint['value'] = parsed.parameters.get('value', 0)
                
                constraints.append(constraint)
                log(f"Parsed constraint ({parsed.parsing_method}): {constraint['type']} with confidence {parsed.confidence}")
                
            except Exception as e:
                log(f"Error parsing constraint part '{part}': {e}")
                # Fallback to pattern matching
                constraints.extend(parse_inventory_constraints_fallback(part))
    else:
        # Use fallback pattern matching
        log("Using fallback pattern matching (enhanced parser not available)")
        constraints = parse_inventory_constraints_fallback(gpt_prompt)
    
    return constraints

def parse_inventory_constraints_fallback(gpt_prompt):
    """Fallback pattern matching for inventory constraints"""
    constraints = []
    
    # Pattern for safety stock constraints: "ITEM001 safety stock should be <= 10"
    safety_stock_pattern = r'(\w+)\s+safety\s*stock\s+(?:should\s+be\s+)?([<>=]+)\s*(\d+(?:\.\d+)?)'
    matches = re.finditer(safety_stock_pattern, gpt_prompt, re.IGNORECASE)
    for match in matches:
        item_id = match.group(1)
        operator = match.group(2)
        value = float(match.group(3))
        constraints.append({
            'type': 'safety_stock_limit',
            'item_id': item_id,
            'operator': operator,
            'value': value,
            'original': match.group(0),
            'method': 'fallback_pattern_matching',
            'confidence': 0.85
        })
        log(f"Parsed safety stock constraint: {item_id} {operator} {value}")
    
    # Pattern for EOQ constraints: "ITEM002 EOQ must be >= 50"
    eoq_pattern = r'(\w+)\s+(?:EOQ|order\s*quantity)\s+(?:must\s+be\s+|should\s+be\s+)?([<>=]+)\s*(\d+(?:\.\d+)?)'
    matches = re.finditer(eoq_pattern, gpt_prompt, re.IGNORECASE)
    for match in matches:
        item_id = match.group(1)
        operator = match.group(2)
        value = float(match.group(3))
        constraints.append({
            'type': 'eoq_limit',
            'item_id': item_id,
            'operator': operator,  
            'value': value,
            'original': match.group(0),
            'method': 'fallback_pattern_matching',
            'confidence': 0.85
        })
        log(f"Parsed EOQ constraint: {item_id} {operator} {value}")
    
    # Pattern for inventory value constraints: "ITEM003 inventory value <= 5000"
    inv_value_pattern = r'(\w+)\s+inventory\s*value\s+(?:should\s+be\s+|must\s+be\s+)?([<>=]+)\s*(\d+(?:\.\d+)?)'
    matches = re.finditer(inv_value_pattern, gpt_prompt, re.IGNORECASE)
    for match in matches:
        item_id = match.group(1)
        operator = match.group(2)
        value = float(match.group(3))
        constraints.append({
            'type': 'inventory_value_limit',
            'item_id': item_id,
            'operator': operator,
            'value': value,
            'original': match.group(0),
            'method': 'fallback_pattern_matching',
            'confidence': 0.85
        })
        log(f"Parsed inventory value constraint: {item_id} {operator} {value}")
    
    return constraints

def apply_constraint(item_result, constraint):
    """Apply a constraint to an item's optimization result"""
    item_id = item_result['item_id']
    
    if constraint.get('type') == 'category_constraint':
        # Check if item is in the specified category
        if item_result.get('category', '').upper() != constraint.get('category', '').upper():
            return item_result
    elif constraint.get('type') == 'supplier_constraint':
        # Check if item is from the specified supplier
        if item_result.get('supplier', '').upper() != constraint.get('supplier', '').upper():
            return item_result
    elif constraint.get('item_id', '').upper() != item_id.upper():
        return item_result
    
    log(f"Applying constraint to {item_id}: {constraint.get('type', 'unknown')} {constraint.get('operator', '')} {constraint.get('value', '')}")
    
    if constraint['type'] == 'safety_stock_limit':
        current_ss = item_result['safety_stock']
        target_value = constraint['value']
        
        # Apply the constraint based on operator
        if constraint['operator'] == '<=' and current_ss > target_value:
            item_result['safety_stock'] = target_value
            item_result['constraint_applied'] = f"Safety stock reduced from {current_ss:.2f} to {target_value:.2f}"
        elif constraint['operator'] == '>=' and current_ss < target_value:
            item_result['safety_stock'] = target_value
            item_result['constraint_applied'] = f"Safety stock increased from {current_ss:.2f} to {target_value:.2f}"
        elif constraint['operator'] == '=' and abs(current_ss - target_value) > 0.01:
            item_result['safety_stock'] = target_value
            item_result['constraint_applied'] = f"Safety stock set to {target_value:.2f}"
        
        # Recalculate dependent values
        item_result['reorder_point'] = item_result['reorder_point'] - current_ss + item_result['safety_stock']
        item_result['avg_inventory'] = (item_result['eoq'] / 2) + item_result['safety_stock']
        item_result['inventory_value'] = item_result['avg_inventory'] * item_result['unit_cost']
        item_result['holding_cost'] = item_result['avg_inventory'] * item_result['unit_cost'] * item_result['holding_rate']
        item_result['total_cost'] = item_result['ordering_cost'] + item_result['holding_cost']
        
    elif constraint['type'] == 'eoq_limit':
        current_eoq = item_result['eoq']
        target_value = constraint['value']
        
        # Apply the constraint based on operator  
        if constraint['operator'] == '<=' and current_eoq > target_value:
            item_result['eoq'] = target_value
            item_result['constraint_applied'] = f"EOQ reduced from {current_eoq:.2f} to {target_value:.2f}"
        elif constraint['operator'] == '>=' and current_eoq < target_value:
            item_result['eoq'] = target_value
            item_result['constraint_applied'] = f"EOQ increased from {current_eoq:.2f} to {target_value:.2f}"
        elif constraint['operator'] == '=' and abs(current_eoq - target_value) > 0.01:
            item_result['eoq'] = target_value
            item_result['constraint_applied'] = f"EOQ set to {target_value:.2f}"
        
        # Recalculate dependent values
        item_result['num_orders_per_year'] = item_result['demand'] / item_result['eoq'] if item_result['eoq'] > 0 else 0
        item_result['ordering_cost'] = item_result['num_orders_per_year'] * item_result['ordering_cost_per_order']
        item_result['avg_inventory'] = (item_result['eoq'] / 2) + item_result['safety_stock']
        item_result['inventory_value'] = item_result['avg_inventory'] * item_result['unit_cost']
        item_result['holding_cost'] = item_result['avg_inventory'] * item_result['unit_cost'] * item_result['holding_rate']
        item_result['total_cost'] = item_result['ordering_cost'] + item_result['holding_cost']
    
    elif constraint['type'] == 'category_constraint':
        metric = constraint.get('metric', '').replace('_', ' ')
        if metric == 'safety stock':
            apply_constraint(item_result, {
                'type': 'safety_stock_limit',
                'item_id': item_id,
                'operator': constraint['operator'],
                'value': constraint['value']
            })
        elif metric == 'eoq':
            apply_constraint(item_result, {
                'type': 'eoq_limit',
                'item_id': item_id,
                'operator': constraint['operator'],
                'value': constraint['value']
            })
    
    elif constraint['type'] == 'service_level_constraint':
        # Service level affects safety stock calculation
        target_service_level = constraint['value']
        if target_service_level > 1:
            target_service_level = target_service_level / 100
        
        # Recalculate safety stock based on new service level
        demand_std = item_result['demand'] * 0.2  # Assume 20% variability
        z_score = stats.norm.ppf(target_service_level)
        new_safety_stock = z_score * demand_std * np.sqrt(item_result.get('lead_time', 7) / 30)
        
        if new_safety_stock != item_result['safety_stock']:
            old_ss = item_result['safety_stock']
            item_result['safety_stock'] = round(new_safety_stock, 2)
            item_result['constraint_applied'] = f"Safety stock adjusted from {old_ss:.2f} to {new_safety_stock:.2f} for {target_service_level*100:.1f}% service level"
            
            # Recalculate dependent values
            item_result['reorder_point'] = item_result['reorder_point'] - old_ss + item_result['safety_stock']
            item_result['avg_inventory'] = (item_result['eoq'] / 2) + item_result['safety_stock']
            item_result['inventory_value'] = item_result['avg_inventory'] * item_result['unit_cost']
            item_result['holding_cost'] = item_result['avg_inventory'] * item_result['unit_cost'] * item_result['holding_rate']
            item_result['total_cost'] = item_result['ordering_cost'] + item_result['holding_cost']
    
    return item_result

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
    """Build and solve inventory optimization model with constraint support"""
    
    # Extract parameters from scenario
    params = scenario.get('params', {})
    
    # Map generic parameters to inventory-specific ones
    holding_cost_rate = params.get('param1', 0.2) / 100  # Convert percentage to decimal
    ordering_cost = params.get('param2', 50.0)
    service_level = params.get('param3', 95) / 100  # Convert percentage to decimal
    max_inventory_value = params.get('param4', 100000.0) if params.get('param4', False) else float('inf')
    use_safety_stock = params.get('param5', True)
    
    # Initialize enhanced parser if available
    enhanced_parser = None
    if ENHANCED_PARSER_AVAILABLE:
        # Get OpenAI API key
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            log("⚠️ No OpenAI API key found in environment. Enhanced parser will use pattern matching only.")
        else:
            log(f"✅ OpenAI API key found (length: {len(openai_api_key)})")
        
        try:
            enhanced_parser = EnhancedInventoryConstraintParser(api_key=openai_api_key)
            if enhanced_parser.is_available():
                log("✅ Enhanced parser initialized with LLM support")
            else:
                log("⚠️ Enhanced parser initialized with pattern matching only (no LLM)")
        except Exception as e:
            log(f"❌ Failed to initialize enhanced parser: {e}")
    
    # Parse custom constraints from GPT prompt
    gpt_prompt = scenario.get('gpt_prompt', '')
    constraints = parse_inventory_constraints(gpt_prompt, enhanced_parser)
    
    log(f"Parameters: holding_cost={holding_cost_rate}, ordering_cost={ordering_cost}, service_level={service_level}")
    log(f"Found {len(constraints)} custom constraints")
    
    # Initialize results
    results = []
    total_cost = 0
    total_inventory_value = 0
    applied_constraints = []
    
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
        
        # Store initial results
        item_result = {
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
            'category': row.get('category', 'General'),
            'supplier': row.get('supplier', 'Default'),
            'lead_time': lead_time,
            'holding_rate': holding_cost_rate,
            'ordering_cost_per_order': ordering_cost
        }
        
        # Apply any relevant constraints
        for constraint in constraints:
            original_result = item_result.copy()
            item_result = apply_constraint(item_result, constraint)
            if 'constraint_applied' in item_result:
                applied_constraints.append({
                    **constraint,
                    'item_id': item_id,
                    'application_detail': item_result['constraint_applied']
                })
        
        results.append(item_result)
        total_cost += item_result['total_cost']
        total_inventory_value += item_result['inventory_value']
    
    # Check inventory value constraint
    if total_inventory_value > max_inventory_value:
        log(f"Warning: Total inventory value ${total_inventory_value:.2f} exceeds maximum ${max_inventory_value:.2f}")
    
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
        'applied_constraints': applied_constraints,
        'timestamp': datetime.now().isoformat()
    }
    
    # Save solution
    solution_path = os.path.join(output_dir, "solution_summary.json")
    with open(solution_path, 'w') as f:
        json.dump(solution, f, indent=4)
    log(f"Solution written to {solution_path}")
    log(f"Applied {len(applied_constraints)} constraints")
    
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
            "avg_order_frequency": round(sum(r['num_orders_per_year'] for r in results) / len(results), 2),
            "constraints_applied": len(applied_constraints)
        },
        "status": "solved"
    }
    
    compare_metrics_path = os.path.join(output_dir, "compare_metrics.json")
    with open(compare_metrics_path, 'w') as f:
        json.dump(compare_metrics, f, indent=4)
    log(f"Comparison metrics written to {compare_metrics_path}")

def main():
    parser = argparse.ArgumentParser(description="Enhanced Inventory Optimization Solver")
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
                "avg_order_frequency": 0,
                "constraints_applied": 0
            },
            "status": "error"
        }
        
        with open(os.path.join(outputs_dir, "compare_metrics.json"), 'w') as f:
            json.dump(compare_metrics, f, indent=4)
        
        sys.exit(1)

if __name__ == "__main__":
    main() 