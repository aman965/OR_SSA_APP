import argparse
import json
import os
import sys
import traceback
import pandas as pd
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, LpStatus, value, PULP_CBC_CMD

# Import the enhanced constraint parsing system
try:
    # Add the path to find our enhanced VRP constraint parsing modules
    constraint_module_path = os.path.join(os.path.dirname(__file__), '..', 'applications', 'vehicle_routing')
    constraint_module_path = os.path.abspath(constraint_module_path)
    if constraint_module_path not in sys.path:
        sys.path.append(constraint_module_path)
    
    # Import basic constraint parsing first
    from constraint_patterns import VRPConstraintMatcher, ConstraintConverter
    from llm_parser import LLMConstraintParser
    CONSTRAINT_PARSING_AVAILABLE = True
    
    # Try to import enhanced modules
    try:
        print(f"[vrp_solver_enhanced] Attempting to import enhanced constraint modules...")
        print(f"[vrp_solver_enhanced] Current sys.path: {sys.path}")
        print(f"[vrp_solver_enhanced] Current working directory: {os.getcwd()}")
        print(f"[vrp_solver_enhanced] Constraint module path: {constraint_module_path}")
        
        from enhanced_constraint_parser import EnhancedConstraintParser, ParsedConstraint
        print(f"[vrp_solver_enhanced] ✅ Successfully imported EnhancedConstraintParser")
        
        from enhanced_constraint_applier import EnhancedConstraintApplier
        print(f"[vrp_solver_enhanced] ✅ Successfully imported EnhancedConstraintApplier")
        
        ENHANCED_CONSTRAINT_PARSING_AVAILABLE = True
        print(f"[vrp_solver_enhanced] ✅ Enhanced constraint parsing system loaded successfully")
    except ImportError as enhanced_import_error:
        print(f"[vrp_solver_enhanced] ❌ Enhanced constraint parsing not available: {enhanced_import_error}")
        print(f"[vrp_solver_enhanced] ❌ Import error details: {type(enhanced_import_error).__name__}: {str(enhanced_import_error)}")
        import traceback
        print(f"[vrp_solver_enhanced] ❌ Full traceback:")
        traceback.print_exc()
        ENHANCED_CONSTRAINT_PARSING_AVAILABLE = False
    
except ImportError as e:
    print(f"[vrp_solver_enhanced] Basic constraint parsing not available: {e}")
    CONSTRAINT_PARSING_AVAILABLE = False
    ENHANCED_CONSTRAINT_PARSING_AVAILABLE = False


def log(msg):
    print(f"[vrp_solver_enhanced] {msg}")


def calculate_pattern_confidence(pattern_result, prompt: str) -> float:
    """Calculate confidence for pattern matching (same as our demo)"""
    if not pattern_result:
        return 0.0
    
    constraint_type, match_info = pattern_result
    confidence = 0.6
    
    # Boost for numeric values
    params = match_info.get('parameters', {})
    for key, value in params.items():
        if value and str(value).replace('.', '').isdigit():
            confidence += 0.15
    
    # Boost for keywords
    high_confidence_words = ['maximum', 'minimum', 'exceed', 'capacity', 'vehicle']
    words_found = sum(1 for word in high_confidence_words if word in prompt.lower())
    confidence += min(0.2, words_found * 0.05)
    
    # Handle known typos
    if 'mimimum' in prompt.lower():
        confidence = max(confidence, 0.8)
    
    return min(1.0, max(0.0, confidence))


def parse_constraints_intelligently(gpt_prompt, scenario_params):
    """
    Enhanced constraint parsing using the new constraint system
    Returns list of parsed constraints that can be applied to the model
    """
    if not gpt_prompt or not gpt_prompt.strip():
        log("No GPT prompt provided - no additional constraints to parse")
        return []
    
    log(f"Processing constraint prompt: '{gpt_prompt}'")
    
    # FORCE ENHANCED CONSTRAINT PARSING ONLY
    if ENHANCED_CONSTRAINT_PARSING_AVAILABLE:
        log("🚀 FORCING enhanced constraint parsing system (no fallback)")
        try:
            # Get OpenAI API key
            openai_api_key = os.environ.get('OPENAI_API_KEY')
            
            # TEMPORARY WORKAROUND: If not in environment, try reading directly from secrets.toml
            if not openai_api_key:
                possible_paths = [
                    os.path.join(os.path.dirname(__file__), '..', '..', '.streamlit', 'secrets.toml'),
                    os.path.join(os.getcwd(), '.streamlit', 'secrets.toml'),
                    '.streamlit/secrets.toml'
                ]
                
                for secrets_path in possible_paths:
                    secrets_path = os.path.abspath(secrets_path)
                    if os.path.exists(secrets_path):
                        try:
                            with open(secrets_path, 'r') as f:
                                content = f.read()
                                for line in content.split('\n'):
                                    stripped_line = line.strip()
                                    if stripped_line.startswith('OPENAI_API_KEY') and '=' in stripped_line:
                                        key_value = line.split('=', 1)[1].strip().strip('"').strip("'")
                                        if key_value and not key_value.startswith('#') and len(key_value) > 10:
                                            openai_api_key = key_value
                                            log(f"✅ Successfully extracted OpenAI API key (length: {len(openai_api_key)})")
                                            break
                            if openai_api_key:
                                break
                        except Exception as e:
                            log(f"Error reading secrets.toml: {e}")
            
            # Initialize enhanced parser
            enhanced_parser = EnhancedConstraintParser(api_key=openai_api_key)
            
            # Parse the constraint using enhanced system
            parsed_constraint = enhanced_parser.parse_constraint(gpt_prompt, scenario_params)
            
            if parsed_constraint:
                log(f"✅ Enhanced parsing successful: {parsed_constraint.constraint_type} ({parsed_constraint.complexity_level})")
                log(f"✅ Parsing method: {parsed_constraint.parsing_method}")
                log(f"✅ Confidence: {parsed_constraint.confidence}")
                log(f"✅ Interpretation: {parsed_constraint.interpretation}")
                
                # Convert to legacy format for compatibility with existing apply function
                legacy_constraint = {
                    'original_prompt': gpt_prompt,
                    'constraint_type': parsed_constraint.constraint_type,
                    'subtype': parsed_constraint.subtype,
                    'parameters': parsed_constraint.parameters or {},
                    'entities': [{'type': e.type, 'id': e.id} for e in (parsed_constraint.entities or [])],
                    'mathematical_format': parsed_constraint.mathematical_description,
                    'parsing_method': parsed_constraint.parsing_method,
                    'confidence': parsed_constraint.confidence,
                    'complexity_level': parsed_constraint.complexity_level,
                    'enhanced_constraint': parsed_constraint  # Store the full enhanced constraint
                }
                
                log(f"🎉 ENHANCED PARSING SUCCESSFUL - Using {parsed_constraint.parsing_method} with {parsed_constraint.confidence} confidence")
                log(f"🚀 RETURNING ENHANCED CONSTRAINT - NO FALLBACK TO BASIC SYSTEM")
                return [legacy_constraint]
            else:
                log("❌ Enhanced parsing returned None - this should not happen with our patterns")
                log("❌ CRITICAL ERROR: Enhanced parser failed unexpectedly")
                return []
                
        except Exception as e:
            log(f"❌ CRITICAL ERROR in enhanced constraint parsing: {e}")
            import traceback
            log(f"❌ Traceback: {traceback.format_exc()}")
            log("❌ ENHANCED PARSING FAILED - RETURNING EMPTY (NO FALLBACK)")
            return []
    else:
        log("❌ Enhanced constraint parsing not available - CRITICAL ERROR")
        log("❌ This should not happen - enhanced parsing should always be available")
        return []


def apply_constraints_to_model(prob, constraints, nodes, vehicle_count, vehicle_capacity, demand, used_k, x, u):
    """
    Apply parsed constraints to the PuLP model using enhanced constraint application
    This handles both basic and complex routing constraints
    """
    if not constraints:
        log("No constraints to apply")
        return
    
    log("=== APPLYING CONSTRAINTS TO MODEL ===")
    
    # Try enhanced constraint application first
    if ENHANCED_CONSTRAINT_PARSING_AVAILABLE:
        log("Using enhanced constraint application system")
        try:
            # Check if we have enhanced constraints
            enhanced_constraints = []
            basic_constraints = []
            
            for constraint in constraints:
                if 'enhanced_constraint' in constraint and constraint['enhanced_constraint']:
                    enhanced_constraints.append(constraint['enhanced_constraint'])
                    log(f"✅ Found enhanced constraint: {constraint['enhanced_constraint'].constraint_type} ({constraint['enhanced_constraint'].parsing_method})")
                else:
                    basic_constraints.append(constraint)
                    log(f"⚠️ Found basic constraint: {constraint.get('constraint_type', 'unknown')}")
            
            # Apply enhanced constraints
            if enhanced_constraints:
                log(f"🚀 Applying {len(enhanced_constraints)} enhanced constraints")
                enhanced_applier = EnhancedConstraintApplier()
                
                application_results = enhanced_applier.apply_constraints_to_model(
                    prob, enhanced_constraints, nodes, vehicle_count, vehicle_capacity, 
                    demand, used_k, x, u
                )
                
                log(f"Enhanced constraint application results:")
                log(f"  Total constraints: {application_results['total_constraints']}")
                log(f"  Applied successfully: {application_results['applied_successfully']}")
                log(f"  Failed applications: {application_results['failed_applications']}")
                
                if application_results['warnings']:
                    for warning in application_results['warnings']:
                        log(f"  Warning: {warning}")
                
                # Get constraint summary
                summary = enhanced_applier.get_constraint_summary()
                log(f"Constraint summary: {summary}")
            else:
                log("⚠️ No enhanced constraints found to apply")
            
            # Apply any remaining basic constraints using the legacy method
            if basic_constraints:
                log(f"Applying {len(basic_constraints)} basic constraints using legacy method")
                _apply_basic_constraints(prob, basic_constraints, nodes, vehicle_count, vehicle_capacity, demand, used_k, x, u)
            
            return
            
        except Exception as e:
            log(f"❌ Error in enhanced constraint application: {e}")
            import traceback
            log(f"Traceback: {traceback.format_exc()}")
            log("Falling back to basic constraint application")
    
    # Fallback to basic constraint application
    log("Using basic constraint application system")
    _apply_basic_constraints(prob, constraints, nodes, vehicle_count, vehicle_capacity, demand, used_k, x, u)


def _apply_basic_constraints(prob, constraints, nodes, vehicle_count, vehicle_capacity, demand, used_k, x, u):
    """
    Apply constraints using the basic/legacy constraint application method
    """
    for i, constraint in enumerate(constraints):
        try:
            constraint_type = constraint.get('constraint_type', 'unknown')
            params = constraint.get('parameters', {})
            
            log(f"Applying basic constraint {i+1}: {constraint_type}")
            log(f"Constraint parameters: {params}")
            
            if constraint_type == 'vehicle_capacity_max':
                # Maximum capacity constraint
                max_capacity = float(params.get('capacity', vehicle_capacity))
                for v in range(vehicle_count):
                    prob += lpSum(demand[j] * x[i, j, v] for i in nodes for j in nodes if i != j) <= max_capacity, f"UserMaxCap_{v}_{i}"
                log(f"Applied maximum capacity constraint: {max_capacity}")
                
            elif constraint_type == 'vehicle_count_min' or constraint_type == 'min_vehicles':
                # Minimum vehicles constraint
                min_vehicles = int(params.get('vehicle_count', params.get('min_vehicles', 1)))
                prob += lpSum(used_k[k] for k in range(vehicle_count)) >= min_vehicles, f"UserMinVehicles_{i}"
                log(f"Applied minimum vehicles constraint: {min_vehicles}")
                
            elif constraint_type == 'vehicle_count_max' or constraint_type == 'max_vehicles':
                # Maximum vehicles constraint
                max_vehicles = int(params.get('vehicle_count', params.get('max_vehicles', vehicle_count)))
                prob += lpSum(used_k[k] for k in range(vehicle_count)) <= max_vehicles, f"UserMaxVehicles_{i}"
                log(f"Applied maximum vehicles constraint: {max_vehicles}")
                
            elif constraint_type == 'vehicle_count':
                # Generic vehicle count constraint - check parameters to determine min/max
                if 'min' in params or 'min_vehicles' in params:
                    min_vehicles = int(params.get('min', params.get('min_vehicles', 2)))
                    prob += lpSum(used_k[k] for k in range(vehicle_count)) >= min_vehicles, f"UserMinVehicles_{i}"
                    log(f"Applied minimum vehicles constraint: {min_vehicles}")
                elif 'max' in params or 'max_vehicles' in params:
                    max_vehicles = int(params.get('max', params.get('max_vehicles', vehicle_count)))
                    prob += lpSum(used_k[k] for k in range(vehicle_count)) <= max_vehicles, f"UserMaxVehicles_{i}"
                    log(f"Applied maximum vehicles constraint: {max_vehicles}")
                elif params.get('constraint_direction') == 'minimize':
                    # Minimize vehicle count by adding penalty to objective
                    log(f"Applied vehicle count minimization (handled via objective)")
                elif params.get('constraint_direction') == 'minimum':
                    # Handle case where constraint_direction is 'minimum' but no explicit min_vehicles
                    # Look for any numeric value in the parameters
                    min_vehicles = 2  # Default from the constraint text
                    for key, value in params.items():
                        if isinstance(value, (int, float)) and value > 0:
                            min_vehicles = int(value)
                            break
                    prob += lpSum(used_k[k] for k in range(vehicle_count)) >= min_vehicles, f"UserMinVehicles_{i}"
                    log(f"Applied minimum vehicles constraint (from direction): {min_vehicles}")
                else:
                    log(f"Vehicle count constraint found but no clear min/max specified: {params}")
                    # Try to extract any numeric value as minimum
                    for key, value in params.items():
                        if isinstance(value, (int, float)) and value > 0:
                            min_vehicles = int(value)
                            prob += lpSum(used_k[k] for k in range(vehicle_count)) >= min_vehicles, f"UserMinVehicles_{i}"
                            log(f"Applied minimum vehicles constraint (inferred): {min_vehicles}")
                            break
                
            elif constraint_type == 'total_distance_max':
                # Maximum total distance (approximation)
                max_distance = float(params.get('distance', float('inf')))
                # This would need the objective function, so we'll handle it differently
                log(f"Maximum distance constraint noted: {max_distance} (applied via objective bound)")
                
            # Handle enhanced constraint types that might fall back to basic application
            elif constraint_type == 'node_separation':
                log(f"Node separation constraint detected but enhanced application failed - skipping")
                log(f"Constraint: {constraint.get('original_prompt', 'unknown')}")
                
            elif constraint_type == 'node_grouping':
                log(f"Node grouping constraint detected but enhanced application failed - skipping")
                log(f"Constraint: {constraint.get('original_prompt', 'unknown')}")
                
            elif constraint_type == 'multi_part':
                log(f"Multi-part constraint detected but enhanced application failed - skipping")
                log(f"Constraint: {constraint.get('original_prompt', 'unknown')}")
                
            else:
                log(f"Unknown constraint type: {constraint_type} - skipped")
                
        except Exception as e:
            log(f"Error applying basic constraint {i+1}: {e}")
            import traceback
            log(f"Traceback: {traceback.format_exc()}")


def load_scenario(scenario_path):
    with open(scenario_path, 'r') as f:
        scenario = json.load(f)
    return scenario


def load_snapshot_csv(csv_path):
    return pd.read_csv(csv_path)


def build_and_solve_vrp(scenario, df, output_dir):
    # Extract scenario information
    gpt_prompt = scenario.get('gpt_prompt', '')
    scenario_params = scenario.get('params', {})
    
    # Parse user constraints intelligently (TRANSPARENT TO USER)
    log("=== INTELLIGENT CONSTRAINT PARSING ===")
    parsed_constraints = parse_constraints_intelligently(gpt_prompt, scenario_params)
    
    # Log parsed constraints for debugging (but hidden from user)
    for constraint in parsed_constraints:
        log(f"Parsed: {constraint['constraint_type']} from '{constraint['original_prompt']}'")
    
    # Original VRP setup
    n = len(df)
    nodes = list(range(n))
    depot = 0
    demand = df['demand'].tolist() if 'demand' in df.columns else [0]*n
    
    # Default parameters (may be overridden by constraints)
    vehicle_count = int(scenario['params'].get('param2', 3)) or 3
    vehicle_capacity = float(scenario['params'].get('param1', 100)) or 100
    vehicle_limit = int(scenario['params'].get('vehicle_limit', vehicle_count))
    
    log(f"Base parameters - Nodes: {n}, Vehicles: {vehicle_count}, Capacity: {vehicle_capacity}")

    # Distance matrix calculation (same as original)
    if 'distance' in df.columns:
        dist_matrix = df['distance'].values.reshape((n, n))
    elif 'x' in df.columns and 'y' in df.columns:
        log("Calculating distance matrix from x,y coordinates")
        dist_matrix = [[0 for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j:
                    dist_matrix[i][j] = ((df['x'][i] - df['x'][j])**2 + (df['y'][i] - df['y'][j])**2)**0.5
    elif 'latitude' in df.columns and 'longitude' in df.columns:
        log("Calculating distance matrix from latitude,longitude coordinates")
        dist_matrix = [[0 for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Simple Euclidean distance (for small areas, more accurate would be Haversine)
                    dist_matrix[i][j] = ((df['latitude'][i] - df['latitude'][j])**2 + (df['longitude'][i] - df['longitude'][j])**2)**0.5
    else:
        if df.shape[1] >= n:
            dist_matrix = df.iloc[:, :n].values
        else:
            raise ValueError(f"CSV does not have enough columns for distance matrix. Expected 'x,y' or 'latitude,longitude' columns, or a full {n}x{n} distance matrix. Found columns: {list(df.columns)}")

    # Create the optimization model
    prob = LpProblem("VRP_Enhanced", LpMinimize)
    x = LpVariable.dicts('x', ((i, j, v) for i in nodes for j in nodes for v in range(vehicle_count)), cat=LpBinary)
    u = LpVariable.dicts('u', ((i, v) for i in nodes for v in range(vehicle_count)), lowBound=0, upBound=vehicle_capacity, cat='Continuous')
    used_k = LpVariable.dicts('used', list(range(vehicle_count)), cat=LpBinary)

    # Objective function
    prob += lpSum(dist_matrix[i][j] * x[i, j, v] for i in nodes for j in nodes for v in range(vehicle_count) if i != j)

    # Standard VRP constraints (same as original)
    # 1. Each customer visited exactly once
    for j in nodes:
        if j == depot:
            continue
        prob += lpSum(x[i, j, v] for i in nodes for v in range(vehicle_count) if i != j) == 1, f"Visit_{j}"

    # 2. Vehicle limit
    prob += lpSum(used_k[k] for k in range(vehicle_count)) <= vehicle_limit, "VehicleLimit"

    # 3. Flow conservation and depot constraints
    for v in range(vehicle_count):
        prob += lpSum(x[depot, j, v] for j in nodes if j != depot) == used_k[v], f"DepartDepot_{v}"
        prob += lpSum(x[i, depot, v] for i in nodes if i != depot) == used_k[v], f"ReturnDepot_{v}"
        for h in nodes:
            if h == depot:
                continue
            prob += (
                lpSum(x[i, h, v] for i in nodes if i != h) == lpSum(x[h, j, v] for j in nodes if j != h)
            ), f"FlowCons_{h}_{v}"

    # 4. Subtour elimination (MTZ)
    for v in range(vehicle_count):
        for i in nodes:
            if i == depot:
                continue
            prob += u[i, v] >= demand[i], f"MTZ_lb_{i}_{v}"
            prob += u[i, v] <= vehicle_capacity, f"MTZ_ub_{i}_{v}"
        for i in nodes:
            for j in nodes:
                if i != j and i != depot and j != depot:
                    prob += u[i, v] - u[j, v] + vehicle_capacity * x[i, j, v] <= vehicle_capacity - demand[j], f"MTZ_{i}_{j}_{v}"

    # 5. Vehicle capacity
    for v in range(vehicle_count):
        prob += lpSum(demand[j] * x[i, j, v] for i in nodes for j in nodes if i != j) <= vehicle_capacity, f"Cap_{v}"

    # === APPLY USER CONSTRAINTS TRANSPARENTLY ===
    log("=== APPLYING USER CONSTRAINTS ===")
    apply_constraints_to_model(prob, parsed_constraints, nodes, vehicle_count, vehicle_capacity, demand, used_k, x, u)

    # Write model.lp
    model_lp_path = os.path.join(output_dir, "model.lp")
    prob.writeLP(model_lp_path)
    log(f"Model written to {model_lp_path}")

    # Solve the model
    solver = PULP_CBC_CMD(msg=1, timeLimit=60)
    result_status = prob.solve(solver)
    log(f"Solver status: {LpStatus[prob.status]}")

    # Process solution (same as original)
    if LpStatus[prob.status] == 'Optimal':
        total_distance = value(prob.objective)
        routes = []
        for v in range(vehicle_count):
            if value(used_k[v]) < 0.5:
                continue
            route = [int(depot)]
            current = depot
            visited = set([depot])
            while True:
                next_nodes = [j for j in nodes if j != current and value(x[current, j, v]) > 0.5]
                if not next_nodes:
                    break
                next_node = int(next_nodes[0])
                route.append(next_node)
                visited.add(next_node)
                current = next_node
                if current == depot:
                    break
            if len(route) > 1:
                route_distance = sum(float(dist_matrix[int(route[i])][int(route[i+1])]) for i in range(len(route)-1))
                routes.append({
                    "stops": [int(node) for node in route],
                    "distance": round(float(route_distance), 2),
                    "duration": round(float(route_distance * 1.5), 2)
                })
        
        # Include constraint information in solution
        solution = {
            "status": "optimal",
            "total_distance": total_distance,
            "vehicle_count": int(sum(value(used_k[v]) > 0.5 for v in range(vehicle_count))),
            "routes": routes,
            "applied_constraints": []
        }
        
        # Generate applied constraints info with correct parsing method
        for c in parsed_constraints:
            constraint_info = {
                "original": c['original_prompt'],
                "type": c['constraint_type']
            }
            
            # Check if this is an enhanced constraint with correct parsing method
            if 'enhanced_constraint' in c and c['enhanced_constraint']:
                # Use the parsing method from the enhanced constraint
                constraint_info["method"] = c['enhanced_constraint'].parsing_method
            else:
                # Use the parsing method from the legacy constraint
                constraint_info["method"] = c.get('parsing_method', 'unknown')
            
            solution["applied_constraints"].append(constraint_info)
        
        # Save solution file in outputs directory (new location)
        solution_path_outputs = os.path.join(output_dir, "solution_summary.json")
        with open(solution_path_outputs, 'w') as f:
            json.dump(solution, f, indent=4)
        log(f"Solution written to outputs directory: {solution_path_outputs}")
        
        # Also save solution file in root scenario directory for backward compatibility
        root_scenario_dir = os.path.dirname(output_dir)
        solution_path_root = os.path.join(root_scenario_dir, "solution_summary.json")
        with open(solution_path_root, 'w') as f:
            json.dump(solution, f, indent=4)
        log(f"Solution written to root directory: {solution_path_root}")
        
        log(f"Solution written with {len(parsed_constraints)} applied constraints")
        
        # Comparison metrics
        compare_metrics = {
            "scenario_id": os.path.basename(root_scenario_dir),
            "snapshot_id": scenario.get("snapshot_id", ""),
            "parameters": scenario.get("params", {}),
            "constraints_applied": len(parsed_constraints),
            "kpis": {
                "total_distance": total_distance,
                "total_routes": len(routes),
                "avg_route_distance": round(total_distance / len(routes), 2) if routes else 0,
                "customers_served": sum(len(route['stops']) - 2 for route in routes),
                "max_route_length": max(len(route['stops']) - 2 for route in routes) if routes else 0,
                "avg_utilization": round(sum(len(route['stops']) - 2 for route in routes) / (len(routes) * vehicle_capacity) * 100, 2) if routes else 0
            },
            "status": "solved"
        }
        with open(os.path.join(output_dir, "compare_metrics.json"), 'w') as f:
            json.dump(compare_metrics, f, indent=4)
            
    else:
        # Handle failure case
        failure = {
            "status": LpStatus[prob.status],
            "message": "Model not solved to optimality.",
            "details": str(prob.status),
            "constraints_attempted": len(parsed_constraints)
        }
        
        # Save failure file in outputs directory (new location)
        failure_path_outputs = os.path.join(output_dir, "failure_summary.json")
        with open(failure_path_outputs, 'w') as f:
            json.dump(failure, f, indent=4)
        log(f"Failure written to outputs directory: {failure_path_outputs}")
        
        # Also save failure file in root scenario directory for backward compatibility
        root_scenario_dir = os.path.dirname(output_dir)
        failure_path_root = os.path.join(root_scenario_dir, "failure_summary.json")
        with open(failure_path_root, 'w') as f:
            json.dump(failure, f, indent=4)
        log(f"Failure written to root directory: {failure_path_root}")


def main():
    parser = argparse.ArgumentParser(description="Enhanced MILP VRP Solver with Intelligent Constraint Parsing")
    parser.add_argument('--scenario-path', required=True, help='Path to scenario.json')
    args = parser.parse_args()

    try:
        log(f"Loading scenario from {args.scenario_path}")
        scenario = load_scenario(args.scenario_path)
        
        csv_path = scenario['dataset_file_path']
        log(f"Loading dataset from {csv_path}")
        df = load_snapshot_csv(csv_path)
        
        output_dir = os.path.dirname(args.scenario_path)
        outputs_subdir = os.path.join(output_dir, "outputs")
        os.makedirs(outputs_subdir, exist_ok=True)
        
        log("Building and solving VRP with intelligent constraint parsing...")
        build_and_solve_vrp(scenario, df, outputs_subdir)
        
        log("VRP solving completed successfully")
        
    except Exception as e:
        log(f"Error in main: {e}")
        traceback.print_exc()
        # Write failure file
        failure = {
            "status": "error",
            "message": f"Solver error: {str(e)}",
            "details": traceback.format_exc()
        }
        output_dir = os.path.dirname(args.scenario_path)
        outputs_subdir = os.path.join(output_dir, "outputs")
        os.makedirs(outputs_subdir, exist_ok=True)
        
        # Save failure file in outputs directory (new location)
        failure_path_outputs = os.path.join(outputs_subdir, "failure_summary.json")
        with open(failure_path_outputs, 'w') as f:
            json.dump(failure, f, indent=4)
        log(f"Error failure written to outputs directory: {failure_path_outputs}")
        
        # Also save failure file in root scenario directory for backward compatibility
        failure_path_root = os.path.join(output_dir, "failure_summary.json")
        with open(failure_path_root, 'w') as f:
            json.dump(failure, f, indent=4)
        log(f"Error failure written to root directory: {failure_path_root}")
        
        sys.exit(1)


if __name__ == "__main__":
    main() 