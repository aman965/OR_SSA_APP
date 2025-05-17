import os
import json
import datetime
import pandas as pd

def ensure_directory_exists(directory_path):
    """Ensure a directory exists, creating it if necessary"""
    os.makedirs(directory_path, exist_ok=True)
    return directory_path

def get_uploads_dir():
    """Get the path to the uploads directory"""
    return ensure_directory_exists(os.path.join('media', 'uploads'))

def get_snapshots_dir():
    """Get the path to the snapshots directory"""
    return ensure_directory_exists(os.path.join('media', 'snapshots'))

def get_scenarios_dir():
    """Get the path to the scenarios directory"""
    return ensure_directory_exists(os.path.join('media', 'scenarios'))

def generate_timestamp_id():
    """Generate a timestamp-based ID for file naming"""
    return datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

def get_snapshot_dir(snapshot_id):
    """Get the directory for a specific snapshot"""
    return ensure_directory_exists(os.path.join(get_snapshots_dir(), f"snapshot__{snapshot_id}"))

def get_scenario_dir(scenario_id):
    """Get the directory for a specific scenario"""
    return ensure_directory_exists(os.path.join(get_scenarios_dir(), f"scenario__{scenario_id}"))

def get_scenario_output_dir(scenario_id):
    """Get the output directory for a specific scenario"""
    scenario_dir = get_scenario_dir(scenario_id)
    return ensure_directory_exists(os.path.join(scenario_dir, "outputs"))

def save_snapshot_file(snapshot_id, df):
    """Save a dataframe as a snapshot file"""
    snapshot_dir = get_snapshot_dir(snapshot_id)
    file_path = os.path.join(snapshot_dir, "snapshot.csv")
    df.to_csv(file_path, index=False)
    return file_path

def load_snapshot_file(snapshot_id):
    """Load a snapshot file as a dataframe"""
    snapshot_dir = get_snapshot_dir(snapshot_id)
    file_path = os.path.join(snapshot_dir, "snapshot.csv")
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return None

def save_scenario_config(scenario_id, config_data):
    """Save scenario configuration data"""
    scenario_dir = get_scenario_dir(scenario_id)
    file_path = os.path.join(scenario_dir, "scenario.json")
    with open(file_path, 'w') as f:
        json.dump(config_data, f, indent=4)
    return file_path

def load_scenario_config(scenario_id):
    """Load scenario configuration data"""
    scenario_dir = get_scenario_dir(scenario_id)
    file_path = os.path.join(scenario_dir, "scenario.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

def save_solution_summary(scenario_id, solution_data):
    """Save solution summary data"""
    output_dir = get_scenario_output_dir(scenario_id)
    file_path = os.path.join(output_dir, "solution_summary.json")
    with open(file_path, 'w') as f:
        json.dump(solution_data, f, indent=4)
    return file_path

def load_solution_summary(scenario_id):
    """Load solution summary data"""
    output_dir = get_scenario_output_dir(scenario_id)
    file_path = os.path.join(output_dir, "solution_summary.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

def save_failure_summary(scenario_id, failure_data):
    """Save failure summary data"""
    output_dir = get_scenario_output_dir(scenario_id)
    file_path = os.path.join(output_dir, "failure_summary.json")
    with open(file_path, 'w') as f:
        json.dump(failure_data, f, indent=4)
    return file_path

def load_failure_summary(scenario_id):
    """Load failure summary data"""
    output_dir = get_scenario_output_dir(scenario_id)
    file_path = os.path.join(output_dir, "failure_summary.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

def save_gpt_error_explanation(scenario_id, explanation):
    """Save GPT error explanation"""
    output_dir = get_scenario_output_dir(scenario_id)
    file_path = os.path.join(output_dir, "gpt_error_explanation.txt")
    with open(file_path, 'w') as f:
        f.write(explanation)
    return file_path

def load_gpt_error_explanation(scenario_id):
    """Load GPT error explanation"""
    output_dir = get_scenario_output_dir(scenario_id)
    file_path = os.path.join(output_dir, "gpt_error_explanation.txt")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return f.read()
    return None

def save_compare_metrics(scenario_id, metrics_data):
    """Save standardized comparison metrics data"""
    output_dir = get_scenario_output_dir(scenario_id)
    file_path = os.path.join(output_dir, "compare_metrics.json")
    with open(file_path, 'w') as f:
        json.dump(metrics_data, f, indent=4)
    return file_path

def load_compare_metrics(scenario_id):
    """Load standardized comparison metrics data"""
    output_dir = get_scenario_output_dir(scenario_id)
    file_path = os.path.join(output_dir, "compare_metrics.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

def generate_compare_metrics(scenario_id):
    """Generate standardized comparison metrics from scenario data and solution/failure summary"""
    from core.models import Scenario
    import os
    
    try:
        scenario = Scenario.objects.get(id=scenario_id)
        solution_data = load_solution_summary(scenario_id)
        
        metrics = {
            "scenario_id": str(scenario_id),
            "scenario_name": scenario.name,
            "snapshot_id": str(scenario.snapshot.id),
            "snapshot_name": scenario.snapshot.name,
            "parameters": {
                "P1": scenario.param1,
                "P2": scenario.param2,
                "P3": scenario.param3,
                "P4": scenario.param4,
                "P5": scenario.param5
            },
            "kpis": {},
            "status": scenario.status
        }
        
        if solution_data:
            total_distance = solution_data.get('total_distance', 0)
            routes = solution_data.get('routes', {})
            total_routes = len(routes) if isinstance(routes, dict) else len(routes) if isinstance(routes, list) else 0
            
            avg_route_distance = total_distance / total_routes if total_routes > 0 else 0
            total_stops = 0
            
            if isinstance(routes, dict):
                for route_id, route_info in routes.items():
                    total_stops += len(route_info.get('stops', []))
            elif isinstance(routes, list):
                for route in routes:
                    total_stops += len(route) - 2 if len(route) > 2 else 0
            
            metrics["kpis"] = {
                "total_distance": total_distance,
                "total_routes": total_routes,
                "avg_route_distance": round(avg_route_distance, 2),
                "customers_served": total_stops,
                "max_route_length": solution_data.get('max_route_length', 0),
                "avg_utilization": solution_data.get('avg_utilization', 0)
            }
        
        save_compare_metrics(scenario_id, metrics)
        return metrics
    except Exception as e:
        print(f"Error generating comparison metrics for scenario {scenario_id}: {str(e)}")
        return None
