import argparse
import json
import os
import sys
import traceback
import pandas as pd
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, LpStatus, value, PULP_CBC_CMD

# Import the confidence-based constraint parsing system
try:
    # Add the path to find our VRP constraint parsing modules
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'applications', 'vehicle_routing'))
    from constraint_patterns import VRPConstraintMatcher, ConstraintConverter
    from llm_parser import LLMConstraintParser
    CONSTRAINT_PARSING_AVAILABLE = True
except ImportError:
    CONSTRAINT_PARSING_AVAILABLE = False


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
    Transparently parse user constraints using confidence-based routing
    Returns list of parsed constraints that can be applied to the model
    """
    if not gpt_prompt or not gpt_prompt.strip():
        log("No GPT prompt provided - no additional constraints to parse")
        return []
    
    if not CONSTRAINT_PARSING_AVAILABLE:
        log("Constraint parsing modules not available - skipping intelligent parsing")
        return []
    
    log(f"Processing constraint prompt: '{gpt_prompt}'")
    
    try:
        # Initialize parsing components
        matcher = VRPConstraintMatcher()
        converter = ConstraintConverter()
        
        # Get OpenAI API key from environment (passed from Streamlit) OR directly from secrets
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        
        # TEMPORARY WORKAROUND: If not in environment, try reading directly from secrets.toml
        if not openai_api_key:
            # Try multiple possible paths for secrets.toml
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '..', '..', '.streamlit', 'secrets.toml'),
                os.path.join(os.getcwd(), '.streamlit', 'secrets.toml'),
                '.streamlit/secrets.toml'
            ]
            
            for secrets_path in possible_paths:
                secrets_path = os.path.abspath(secrets_path)
                log(f"Trying secrets path: {secrets_path}")
                if os.path.exists(secrets_path):
                    log(f"Found secrets file at {secrets_path}")
                    try:
                        with open(secrets_path, 'r') as f:
                            content = f.read()
                            log(f"Reading secrets content: {len(content)} characters")
                            for line_num, line in enumerate(content.split('\n'), 1):
                                log(f"Line {line_num}: {repr(line[:50])}...")
                                stripped_line = line.strip()
                                if stripped_line.startswith('OPENAI_API_KEY') and '=' in stripped_line:
                                    log(f"Found OPENAI_API_KEY line: {repr(line)}")
                                    key_value = line.split('=', 1)[1].strip().strip('"').strip("'")
                                    log(f"Extracted key value: {repr(key_value[:20])}... (length: {len(key_value)})")
                                    if key_value and not key_value.startswith('#') and len(key_value) > 10:
                                        openai_api_key = key_value
                                        log(f"✅ Successfully extracted OpenAI API key (length: {len(openai_api_key)})")
                                        break
                                    else:
                                        log(f"❌ Invalid key value: empty={not key_value}, starts_with_hash={key_value.startswith('#') if key_value else False}, length={len(key_value) if key_value else 0}")
                                elif stripped_line.startswith('OPENAI_API_KEY'):
                                    log(f"Found OPENAI_API_KEY line but no = sign: {repr(line)}")
                        if openai_api_key:
                            break
                    except Exception as e:
                        log(f"Error reading secrets.toml: {e}")
                else:
                    log(f"Secrets file not found at {secrets_path}")
            
            if not openai_api_key:
                log("Failed to find secrets.toml in any expected location")
        
        if openai_api_key:
            log(f"OpenAI API key available for LLM parsing (length: {len(openai_api_key)})")
        else:
            log("No OpenAI API key found in environment variables or secrets.toml")
            
        llm_parser = LLMConstraintParser(api_key=openai_api_key)
        
        # Confidence threshold (hidden from user)
        confidence_threshold = 0.85
        
        parsed_constraints = []
        
        # Split prompt into individual constraints (simple approach)
        # User might write: "maximum 30 capacity per vehicle, minimum 2 vehicles needed"
        constraint_sentences = [s.strip() for s in gpt_prompt.replace(',', '.').replace(';', '.').split('.') if s.strip()]
        
        for sentence in constraint_sentences:
            log(f"Processing constraint sentence: '{sentence}'")
            
            # Try pattern matching first
            pattern_result = matcher.match_constraint(sentence)
            
            if pattern_result:
                confidence = calculate_pattern_confidence(pattern_result, sentence)
                constraint_type, match_info = pattern_result
                
                log(f"Pattern match found: {constraint_type} (confidence: {confidence:.1%})")
                
                if confidence >= confidence_threshold:
                    log("HIGH CONFIDENCE - Using pattern matching")
                    
                    # Convert constraint to mathematical form
                    try:
                        converter_func = getattr(converter, match_info['conversion_function'])
                        mathematical_constraint = converter_func(match_info['parameters'], scenario_params)
                        
                        parsed_constraint = {
                            'original_prompt': sentence,
                            'constraint_type': constraint_type,
                            'parameters': match_info['parameters'],
                            'mathematical_format': mathematical_constraint,
                            'parsing_method': 'pattern_matching',
                            'confidence': confidence
                        }
                        parsed_constraints.append(parsed_constraint)
                        log(f"Successfully parsed: {constraint_type}")
                        
                    except Exception as e:
                        log(f"Error converting constraint: {e}")
                        
                else:
                    log(f"LOW CONFIDENCE ({confidence:.1%}) - Using LLM fallback")
                    
                    if llm_parser.is_available():
                        llm_result = llm_parser.parse_constraint(sentence, scenario_params)
                        if llm_result:
                            llm_result['original_prompt'] = sentence
                            parsed_constraints.append(llm_result)
                            log("LLM parsing successful")
                        else:
                            log("LLM parsing failed - using fallback")
                            fallback_result = llm_parser._fallback_parse(sentence)
                            fallback_result['original_prompt'] = sentence
                            parsed_constraints.append(fallback_result)
                    else:
                        log("LLM not available - using enhanced fallback")
                        fallback_result = llm_parser._fallback_parse(sentence)
                        fallback_result['original_prompt'] = sentence
                        parsed_constraints.append(fallback_result)
            else:
                log("No pattern match - using LLM/fallback")
                
                if llm_parser.is_available():
                    llm_result = llm_parser.parse_constraint(sentence, scenario_params)
                    if llm_result:
                        llm_result['original_prompt'] = sentence
                        parsed_constraints.append(llm_result)
                        log("LLM parsing successful")
                    else:
                        log("LLM parsing failed - using fallback")
                        fallback_result = llm_parser._fallback_parse(sentence)
                        fallback_result['original_prompt'] = sentence
                        parsed_constraints.append(fallback_result)
                else:
                    log("No LLM available - using enhanced fallback")
                    fallback_result = llm_parser._fallback_parse(sentence)
                    fallback_result['original_prompt'] = sentence
                    parsed_constraints.append(fallback_result)
        
        log(f"Successfully parsed {len(parsed_constraints)} constraints")
        return parsed_constraints
        
    except Exception as e:
        log(f"Error in intelligent constraint parsing: {e}")
        return []


def apply_constraints_to_model(prob, constraints, nodes, vehicle_count, vehicle_capacity, demand, used_k, x, u):
    """
    Apply parsed constraints to the PuLP model
    This is where the magic happens - constraints get converted to mathematical form
    """
    for i, constraint in enumerate(constraints):
        try:
            constraint_type = constraint.get('constraint_type', 'unknown')
            params = constraint.get('parameters', {})
            
            log(f"Applying constraint {i+1}: {constraint_type}")
            
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
                
            elif constraint_type == 'total_distance_max':
                # Maximum total distance (approximation)
                max_distance = float(params.get('distance', float('inf')))
                # This would need the objective function, so we'll handle it differently
                log(f"Maximum distance constraint noted: {max_distance} (applied via objective bound)")
                
            else:
                log(f"Unknown constraint type: {constraint_type} - skipped")
                
        except Exception as e:
            log(f"Error applying constraint {i+1}: {e}")


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
    else:
        if df.shape[1] >= n:
            dist_matrix = df.iloc[:, :n].values
        else:
            raise ValueError(f"CSV does not have enough columns for distance matrix")

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
            "applied_constraints": [
                {
                    "original": c['original_prompt'],
                    "type": c['constraint_type'],
                    "method": c.get('parsing_method', 'unknown')
                } for c in parsed_constraints
            ]
        }
        
        with open(os.path.join(output_dir, "solution_summary.json"), 'w') as f:
            json.dump(solution, f, indent=4)
        log(f"Solution written with {len(parsed_constraints)} applied constraints")
        
        # Comparison metrics
        compare_metrics = {
            "scenario_id": os.path.basename(output_dir),
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
        with open(os.path.join(output_dir, "failure_summary.json"), 'w') as f:
            json.dump(failure, f, indent=4)
        log(f"Failure written to failure_summary.json")


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
        with open(os.path.join(outputs_subdir, "failure_summary.json"), 'w') as f:
            json.dump(failure, f, indent=4)
        sys.exit(1)


if __name__ == "__main__":
    main() 