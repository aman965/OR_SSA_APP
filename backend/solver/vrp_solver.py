import argparse
import json
import os
import sys
import traceback
import pandas as pd
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, LpStatus, value, PULP_CBC_CMD


def log(msg):
    print(f"[vrp_solver] {msg}")


def load_scenario(scenario_path):
    with open(scenario_path, 'r') as f:
        scenario = json.load(f)
    return scenario


def load_snapshot_csv(csv_path):
    return pd.read_csv(csv_path)


def build_and_solve_vrp(scenario, df, output_dir):
    # Assume depot is node 0, customers are 1..N
    n = len(df)
    nodes = list(range(n))
    depot = 0
    # If demand column exists, use it
    demand = df['demand'].tolist() if 'demand' in df.columns else [0]*n
    # If vehicle count param exists, use it, else default to 3
    vehicle_count = int(scenario['params'].get('param2', 3)) or 3
    vehicle_capacity = float(scenario['params'].get('param1', 100)) or 100
    log(f"Nodes: {n}, Vehicles: {vehicle_count}, Capacity: {vehicle_capacity}")

    # Distance matrix: assume columns are node names or indices
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
            raise ValueError(f"CSV does not have enough columns for a distance matrix. Expected at least {n} columns or 'x'/'y' coordinates.")

    # Model
    prob = LpProblem("VRP", LpMinimize)
    x = LpVariable.dicts('x', ((i, j, v) for i in nodes for j in nodes for v in range(vehicle_count)), cat=LpBinary)
    u = LpVariable.dicts('u', ((i, v) for i in nodes for v in range(vehicle_count)), lowBound=0, upBound=vehicle_capacity, cat='Continuous')

    # Objective: Minimize total distance
    prob += lpSum(dist_matrix[i][j] * x[i, j, v] for i in nodes for j in nodes for v in range(vehicle_count) if i != j)

    # Constraints
    # 1. Each customer visited exactly once (not depot)
    for j in nodes:
        if j == depot:
            continue
        prob += lpSum(x[i, j, v] for i in nodes for v in range(vehicle_count) if i != j) == 1, f"Visit_{j}"

    # 2. Flow conservation for vehicles
    for v in range(vehicle_count):
        # Each vehicle leaves depot once
        prob += lpSum(x[depot, j, v] for j in nodes if j != depot) == 1, f"DepartDepot_{v}"
        # Each vehicle returns to depot once
        prob += lpSum(x[i, depot, v] for i in nodes if i != depot) == 1, f"ReturnDepot_{v}"
        for h in nodes:
            if h == depot:
                continue
            prob += (
                lpSum(x[i, h, v] for i in nodes if i != h) == lpSum(x[h, j, v] for j in nodes if j != h)
            ), f"FlowCons_{h}_{v}"

    # 3. Subtour elimination (MTZ)
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

    # 4. Vehicle capacity
    for v in range(vehicle_count):
        prob += lpSum(demand[j] * x[i, j, v] for i in nodes for j in nodes if i != j) <= vehicle_capacity, f"Cap_{v}"

    # Write model.lp
    model_lp_path = os.path.join(output_dir, "model.lp")
    prob.writeLP(model_lp_path)
    log(f"Model written to {model_lp_path}")

    # Solve
    solver = PULP_CBC_CMD(msg=1, timeLimit=60)
    result_status = prob.solve(solver)
    log(f"Solver status: {LpStatus[prob.status]}")

    if LpStatus[prob.status] == 'Optimal':
        # Extract solution
        total_distance = value(prob.objective)
        routes = []
        for v in range(vehicle_count):
            route = [int(depot)]  # ensure native int
            current = depot
            visited = set([depot])
            while True:
                next_nodes = [j for j in nodes if j != current and value(x[current, j, v]) > 0.5]
                if not next_nodes:
                    break
                next_node = int(next_nodes[0])  # ensure int
                route.append(next_node)
                visited.add(next_node)
                current = next_node
                if current == depot:
                    break
            if len(route) > 1:
                route_distance = sum(float(dist_matrix[int(route[i])][int(route[i+1])]) for i in range(len(route)-1))
                routes.append({
                    "stops": [int(node) for node in route],  # convert entire list
                    "distance": round(float(route_distance), 2),
                    "duration": round(float(route_distance * 1.5), 2)
                })
        solution = {
            "status": "optimal",
            "total_distance": total_distance,
            "vehicle_count": vehicle_count,
            "routes": routes
        }
        with open(os.path.join(output_dir, "solution_summary.json"), 'w') as f:
            json.dump(solution, f, indent=4)
        log(f"Solution written to solution_summary.json")
        
        compare_metrics = {
            "scenario_id": os.path.basename(output_dir),
            "snapshot_id": scenario.get("snapshot_id", ""),
            "parameters": scenario.get("params", {}),
            "kpis": {
                "total_distance": total_distance,
                "total_routes": len(routes),
                "avg_route_distance": round(total_distance / len(routes), 2) if routes else 0,
                "customers_served": sum(len(route) - 2 for route in routes) if routes else 0,
                "max_route_length": max(len(route) - 2 for route in routes) if routes else 0,
                "avg_utilization": round(sum(len(route) - 2 for route in routes) / (len(routes) * vehicle_capacity) * 100, 2) if routes else 0
            },
            "status": "solved"
        }
        with open(os.path.join(output_dir, "compare_metrics.json"), 'w') as f:
            json.dump(compare_metrics, f, indent=4)
        log(f"Comparison metrics written to compare_metrics.json")
    else:
        failure = {
            "status": LpStatus[prob.status],
            "message": "Model not solved to optimality.",
            "details": str(prob.status)
        }
        with open(os.path.join(output_dir, "failure_summary.json"), 'w') as f:
            json.dump(failure, f, indent=4)
        log(f"Failure written to failure_summary.json")
        
        compare_metrics = {
            "scenario_id": os.path.basename(output_dir),
            "snapshot_id": scenario.get("snapshot_id", ""),
            "parameters": scenario.get("params", {}),
            "kpis": {
                "total_distance": 0,
                "total_routes": 0,
                "avg_route_distance": 0,
                "customers_served": 0,
                "max_route_length": 0,
                "avg_utilization": 0
            },
            "status": "failed"
        }
        with open(os.path.join(output_dir, "compare_metrics.json"), 'w') as f:
            json.dump(compare_metrics, f, indent=4)
        log(f"Comparison metrics written to compare_metrics.json")


def main():
    parser = argparse.ArgumentParser(description="MILP VRP Solver with PuLP + CBC")
    parser.add_argument('--scenario-path', required=True, help='Path to scenario.json')
    args = parser.parse_args()
    scenario_path = args.scenario_path
    try:
        log(f"Loading scenario from {scenario_path}")
        scenario = load_scenario(scenario_path)
        output_dir = os.path.dirname(scenario_path)
        csv_path = scenario.get('dataset_file_path')
        if not csv_path:
            raise FileNotFoundError("Dataset file path is empty or not specified")
        normalized_path = os.path.normpath(csv_path)
        if not os.path.exists(normalized_path):
            raise FileNotFoundError(f"Dataset file not found: {csv_path} (normalized: {normalized_path})")
        log(f"Loading snapshot CSV from {normalized_path}")
        df = load_snapshot_csv(normalized_path)
        build_and_solve_vrp(scenario, df, output_dir)
    except Exception as e:
        log(f"Exception: {e}")
        traceback.print_exc()
        failure = {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        output_dir = os.path.dirname(scenario_path)
        with open(os.path.join(output_dir, "failure_summary.json"), 'w') as f:
            json.dump(failure, f, indent=4)
        log(f"Failure written to failure_summary.json")
        
        compare_metrics = {
            "scenario_id": os.path.basename(output_dir),
            "snapshot_id": scenario.get("snapshot_id", "") if 'scenario' in locals() else "",
            "parameters": scenario.get("params", {}) if 'scenario' in locals() else {},
            "kpis": {
                "total_distance": 0,
                "total_routes": 0,
                "avg_route_distance": 0,
                "customers_served": 0,
                "max_route_length": 0,
                "avg_utilization": 0
            },
            "status": "error"
        }
        with open(os.path.join(output_dir, "compare_metrics.json"), 'w') as f:
            json.dump(compare_metrics, f, indent=4)
        log(f"Comparison metrics written to compare_metrics.json")
        sys.exit(1)

if __name__ == "__main__":
    main()          